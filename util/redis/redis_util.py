import pdb
import traceback
import os
import redis
from dotenv import load_dotenv
import time
import subprocess
import json
import pickle

load_dotenv(override=True)
group_id = os.getenv("GROUP_ID")
redis_stream_name = os.getenv("REDIS_STREAM_NAME")
in_docker = os.getenv("INDOCKER")

def get_redis_ip():
    if bool(in_docker):
        return 'redis'
    # Run a command and capture its stdout and stderr
    ip = subprocess.run(
        "docker inspect --format='{{.NetworkSettings.Networks.homeserver.IPAddress}}' redis",
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

    def add(self, data):
        message_id = self.rstream.xadd(self.stream_name, {'data_obj': pickle.dumps(data)}, id='*')
        return message_id.decode('utf-8')

    def read(self, message_id):
        try:
            data = self.rstream.xread(streams={self.stream_name: message_id}, count=1, block=1000)
            if data:
                # data is a list of lists: [[stream_name, [message1, message2, ...]]]
                for stream, stream_messages in data:
                    for message_id, message_data in stream_messages:
                        msg_id = message_id.decode('utf-8')
                        print(f"Received message ID: {msg_id}")
                        ndeleted = self.delete_msg_id(message_id)
                        print(f'{ndeleted} entries removed from redis.')
        except BaseException as be:
            traceback.print_exc()

        data_out = pickle.loads(message_data['data_obj'.encode('utf-8')])
        return data_out
    
    def delete_stream(self, stream_name):
        self.rstream.delete(stream_name)
        print(f"stream_id : {stream_name} deleted.")

    def delete_msg_id(self, message_id):
        del_count = 0
        try:
            del_count = self.rstream.xdel(self.stream_name, message_id)
        except BaseException as be:
            traceback.print_exc()
        
        if not del_count:
            raise ValueError("No entries have been removed!")

        return del_count

    def __del__(self):
        self.rstream.close()

if __name__ == "__main__":
    rstream = RedisStream(redis_stream_name)
    rstream.delete_stream(redis_stream_name)