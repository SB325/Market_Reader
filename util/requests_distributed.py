from kafka.kafka import KafkaProducer, KafkaConsumer
import pdb
from dotenv import load_dotenv
import time
import json

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

    print(f'Waiting for message from requests clients...')
    while True:
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
                    use_redis = False
                )
            print(f"Gave signal to send request {uuid}.")

            