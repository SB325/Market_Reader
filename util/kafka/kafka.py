import pdb
import traceback
import os
from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient
from dotenv import load_dotenv
import time
import subprocess
import json

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

producer_conf = {'bootstrap.servers': f'{get_kafka_ip()}:9092'}
consumer_conf = {
    'bootstrap.servers': f'{get_kafka_ip()}:9092',
    'default.topic.config': {'auto.offset.reset': 'smallest'},
    'group.id': group_id,
}

def get_number_of_messages_in_topic(self, topic):
    unused_consumer = Consumer(consumer_conf)
    admin_client = AdminClient(producer_conf)
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
    producer = Producer(producer_conf)

    def __init__(self):
        pass

    def send(self, topic, msg):
        if isinstance(msg, list):
            for message in msg:
                self.producer.produce(topic, json.dumps(message).encode('utf-8'))
        if isinstance(msg, str):
            self.producer.produce(topic, msg.encode('utf-8'))
        elif isinstance(msg, bytes):
            self.producer.produce(topic, msg)
        self.producer.flush()

    def send_limit_queue_size(self, topic, msg, queue_size):
        while get_number_of_messages_in_topic(self, topic) >= queue_size:
            time.sleep(3)
            
        if isinstance(msg, list):
            for message in msg:
                self.producer.produce(topic, json.dumps(message).encode('utf-8'))
        if isinstance(msg, str):
            self.producer.produce(topic, msg.encode('utf-8'))
        elif isinstance(msg, bytes):
            self.producer.produce(topic, msg)
        self.producer.flush()

class KafkaConsumer():
    consumer = Consumer(consumer_conf)

    admin_client = AdminClient(consumer_conf)

    def __init__(self, topic):
        self.consumer.subscribe(topic)

    def recieve_once(self, topic, msg):
        try:
            msg = self.consumer.poll(1.0)
            if not msg.error():
                print('Received message: %s' % msg.value().decode('utf-8'))
                # send message to transform block
            elif msg.error().code() != KafkaError._PARTITION_EOF:
                print(msg.error())

        except BaseException as be:
            traceback.print_exc()
    
    def recieve_continuous(self, topic, msg):
        try:
            while True:
                msg = consumer.poll(1.0) # Poll with a timeout of 1 second

                if msg is None:
                    continue
                elif msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        # End of partition event
                        sys.stderr.write('%% %s [%d] reached end of offset %d\n' %
                                        (msg.topic(), msg.partition(), msg.offset()))
                    else:
                        raise KafkaException(msg.error())
                    # print('Received message: %s' % msg.value().decode('utf-8'))
                    # send message to transform block
                else:
                    # Process the message
                    print(f"Received message: {msg.value().decode('utf-8')}")
                    # Optionally commit offsets manually after processing
                    # consumer.commit(msg)

        except BaseException as be:
            traceback.print_exc()
        finally:
            # Close the consumer gracefully to trigger a group rebalance
            consumer.close()
    
    def __del__(self):
        self.consumer.close()