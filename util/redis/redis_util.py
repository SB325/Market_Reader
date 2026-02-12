import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
import pdb
import traceback
import redis
from dotenv import load_dotenv
import time
import subprocess
import json
import pickle
from util.otel import otel_tracer, otel_metrics, otel_logger, metrics

otraces = otel_tracer()
ometrics = otel_metrics()
ologs = otel_logger()

# https://opentelemetry-python.readthedocs.io/en/latest/sdk/index.html
load_dotenv(override=True)
group_id = os.getenv("GROUP_ID")
redis_stream_name_facts = os.getenv("REDIS_FACTS_STREAM_NAME")
redis_stream_name_submissions = os.getenv("REDIS_SUBMISSIONS_STREAM_NAME")
in_docker = os.getenv("INDOCKER")

def get_redis_ip():
    if bool(in_docker):
        return 'redis'
    # Run a command and capture its stdout and stderr
    ip = subprocess.run(
        "docker inspect --format='{{.NetworkSettings.Networks.homeserver.IPAddress}}' redis_home",
        capture_output=True,  # Capture stdout and stderr
        text=True,           # Decode output as text (UTF-8 by default)
        shell=True           # Raise CalledProcessError if the command returns a non-zero exit code
    ).stdout.replace('\n', '')
    return ip

redis_ip = get_redis_ip()
pool = redis.ConnectionPool(host=redis_ip, port=6379, db=0)

class RedisStream():
    def __init__(self, stream_name):
        self.stream_name = stream_name
        self.rstream = redis.Redis(connection_pool=pool, decode_responses=True)
        ometrics.create_meter(
            meter_name = f'{stream_name}_queue',
            callbacks=self.get_stream_size_gen,
            meter_type = "ObservableGauge",
            description = 'As distributed transform/load replicas process \
                filing data, this value will decline.',
            )

    def get_stream_size(self):
        data = self.rstream.xread(streams={self.stream_name: '0-0'}, count=None, block=None)
        stream, stream_messages = data[0]
        return len(stream_messages)

    def get_stream_size_gen(self, result):
        data = self.rstream.xread(streams={self.stream_name: '0-0'}, count=None, block=None)
        stream, stream_messages = data[0]
        yield metrics.Observation(len(stream_messages), {'stream_name': self.stream_name})

    def add(self, data, topic):
        with otraces.set_span('redis_xadd') as span:
            message_id = self.rstream.xadd(self.stream_name, {'data_obj': pickle.dumps(data)}, id='*')
        return message_id.decode('utf-8')

    def read(self, message_id, topic):
        data_out = {}
        try:
            with otraces.set_span('redis_xread') as span:
                span.set_attribute("message_id", message_id)
                data = self.rstream.xread(streams={self.stream_name: '0-0'}, count=None, block=None)
            if data:
                exit_loop = False
                # data is a list of lists: [[stream_name, [message1, message2, ...]]]
                for stream, stream_messages in data:
                    if exit_loop:
                        break
                    for message_id_found, message_data in stream_messages:
                        if message_id == message_id_found.decode('utf-8'):
                            msg_id = message_id_found.decode('utf-8')
                            ologs.info(f"Received message ID: {msg_id}")

                            ndeleted = self.delete_msg_id(message_id_found)
                            ologs.info(f'{ndeleted} entries removed from redis.')
                            exit_loop = True
                            break

                data_out = pickle.loads(message_data['data_obj'.encode('utf-8')])
                
        except BaseException as be:
            traceback.print_exc()

        return data_out
    
    def delete_stream(self, stream_name):
        with otraces.set_span('redis_delete') as span:
            span.set_attribute("stream_name", stream_name)
            self.rstream.delete(stream_name)
        ologs.info(f"stream_id : {stream_name} deleted.")

    def delete_msg_id(self, message_id):
        del_count = 0
        try:
            with otraces.set_span('redis_xdel') as span:
                span.set_attribute("message_id", message_id)
                del_count = self.rstream.xdel(self.stream_name, message_id)
        except BaseException as be:
            traceback.print_exc()
        
        if not del_count:
            raise ValueError("No entries have been removed!")

        return del_count

    def __del__(self):
        self.rstream.close()

if __name__ == "__main__":
    rstream_f = RedisStream(redis_stream_name_facts)
    rstream_f.delete_stream(redis_stream_name_facts)
    rstream_s = RedisStream(redis_stream_name_submissions)
    rstream_s.delete_stream(redis_stream_name_submissions)
    # print('running meter')
    # # print(f'{rstream_f.get_stream_size()}')

    # while True:
    #     time.sleep(1)