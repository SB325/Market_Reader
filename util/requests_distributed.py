import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from kafka.kafka import KafkaProducer, KafkaConsumer
import pdb
from dotenv import load_dotenv
import time
import json
from util.otel import otel_tracer, otel_metrics, otel_logger

otraces = otel_tracer()
ometrics = otel_metrics()
ologs = otel_logger()

# load_dotenv()
# group_id = os.getenv("GROUP_ID")

if __name__ == '__main__':
    requests_collection_topic = 'set_delay_topic'
    requests_response_ready_topic = 'set_ready_topic'

    producer = KafkaProducer(
                    topic = requests_response_ready_topic,
                    clear_topic = False,
                )
    consumer = KafkaConsumer(
            topic = [requests_collection_topic])

    ometrics.create_meter(
            meter_name = 'requests_distributed',
            meter_type = "AsynchronousUpDownCounter",
            description = 'As distributed requests from multiple replicas arrive \
                faster than the api rate limit, this meter will have increasing \
                value over time. As replicas catch up, the value decreases.',
            )
    ologs.info(f'Waiting for message from requests clients...')
    with otraces.set_span('requests_distributed_server') as span:
        while True:
            msg=''
            while not msg:
                msg = consumer.recieve_once(
                            use_redis = False,
                            timeout = 0.1)
            if msg:
                message = json.loads(msg)
                uuid = message.get('uuid')
                period = message.get('period')
                time.sleep(period)
                response = json.dumps({
                        'uuid': uuid, 
                        'status': 'ready'})
                producer.send(response,
                        use_redis = False,
                        counter_name='estimated_queue_length'
                    )
                ologs.info(f"Gave signal to send request {uuid}.")

            