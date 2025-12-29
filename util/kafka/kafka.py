import pdb
import traceback
from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient
from dotenv import load_dotenv
import time

load_dotenv(override=True)
group_id = os.getenv("GROUP_ID")

def get_kafka_ip():
    # Run a command and capture its stdout and stderr
    ip = subprocess.run(
        "docker inspect --format='{{.NetworkSettings.Networks.homeserver.IPAddress}}' kafka",
        capture_output=True,  # Capture stdout and stderr
        text=True,           # Decode output as text (UTF-8 by default)
        shell=True           # Raise CalledProcessError if the command returns a non-zero exit code
    ).stdout.replace('\n', '')
    return ip

client_conf = {
    'bootstrap.servers': f'{get_kafka_ip()}:9092',
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}

def get_number_of_messages_in_topic(self, topic):
    unused_consumer = Consumer(client_conf)
    admin_client = AdminClient(client_conf)
    metadata = admin_client.list_topics(topic=topic, timeout=10)
    if topic not in metadata.topics:
        print(f"Error: Topic '{topic_name}' not found.")
        return 0
    partitions = metadata.topics[topic].partitions.keys()
    topic_partitions = [TopicPartition(topic, p) for p in partitions]

    total_messages = 0
    for tp in topic_partitions:
        # Get the low (earliest) and high (latest) watermarks (offsets)
        low, high = unused_consumer.get_watermark_offsets(tp, timeout=10)
        # The number of messages in the partition is the difference between the high and low offsets
        total_messages += (high - low)

    unused_consumer.close()
    return total_messages

class KafkaProducer():
    producer = Producer(client_conf)

    def __init__(self):
        pass

    def send(self, topic, msg):
        self.producer.produce(topic, msg.encode('utf-8'))
        self.producer.flush()

    def send_limit_queue_size(self, topic, msg, queue_size):
        while get_number_of_messages_in_topic(self, topic) >= queue_size:
            time.sleep(3)
        self.producer.produce(topic, msg.encode('utf-8'))
        self.producer.flush()
    
    def __del__(self):
        self.producer.close()

class KafkaConsumer():
    consumer = Consumer(client_conf.update({'group.id': group_id})

    admin_client = AdminClient(client_conf)
    producer = Producer(client_conf)

    def __init__(self, topic):
        self.consumer.subscribe(topic)

    def recieve(self, topic, msg):
        try:
            msg = self.consumer.poll(1.0)
            if not msg.error():
                # print('Received message: %s' % msg.value().decode('utf-8'))
                # send message to transform block
            elif msg.error().code() != KafkaError._PARTITION_EOF:
                print(msg.error())

        except BaseException as be:
            traceback.print_exc()
    
    def __del__(self):
        self.consumer.close()