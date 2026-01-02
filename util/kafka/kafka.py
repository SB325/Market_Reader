import pdb
import traceback
import os
from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, ConfigResource, NewTopic
from dotenv import load_dotenv
from util.redis.redis_util import RedisStream
import time
import subprocess
import json

load_dotenv(override=True)
group_id = os.getenv("GROUP_ID")
redis_stream_name = os.getenv("REDIS_STREAM_NAME")
in_docker = os.getenv("INDOCKER")

rstream = RedisStream(redis_stream_name)

new_retention_ms_day = 24 * 60 * 60 * 1000  # 1 day

def get_kafka_ip():
    if bool(in_docker):
        return 'kafka:29092'

    # Run a command and capture its stdout and stderr
    ip = subprocess.run(
        "docker inspect --format='{{.NetworkSettings.Networks.homeserver.IPAddress}}' kafka",
        capture_output=True,  # Capture stdout and stderr
        text=True,           # Decode output as text (UTF-8 by default)
        shell=True           # Raise CalledProcessError if the command returns a non-zero exit code
    ).stdout.replace('\n', '')
    return f'{ip}:9092'

producer_conf = {
    'bootstrap.servers': get_kafka_ip(),
}
consumer_conf = {
    'bootstrap.servers': get_kafka_ip(),
    'default.topic.config': {'auto.offset.reset': 'smallest'},
    'group.id': group_id,
}
admin_client = AdminClient(producer_conf)

def get_number_of_messages_in_topic(self, topic):
    unused_consumer = Consumer(consumer_conf)
    metadata = admin_client.list_topics(topic=topic, timeout=10)
    if topic not in metadata.topics:
        print(f"Error: Topic '{topic}' not found.")
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

def update_retention_period(retention_time_ms, topic):
    config_resource = ConfigResource(
        ResourceType.TOPIC,
        topic,
        set_configs={'retention.ms': new_retention_ms_day},
    )
    fs = admin_client.alter_configs([config_resource])
    try:
        fs[config_resource].result()
        print(f"Topic configuration successfully altered to {new_retention_ms_day}ms retention")
    except Exception as e:
        print(f"Failed to alter topic config: {e}")

def delete_and_create_topic(admin_client, topic_name):
    """Deletes a topic and re-creates it to clear all messages."""
    
    # 1. Delete the topic
    print(f"Deleting topic '{topic_name}'...")
    fs = admin_client.delete_topics([topic_name], operation_timeout=30)
    
    # Wait for the deletion to finish (optional but recommended in scripts)
    for topic, f in fs.items():
        try:
            f.result()
            print(f"Topic '{topic}' deleted successfully.")
        except Exception as e:
            # Handle cases where the topic might not exist or other errors
            print(f"Failed to delete topic '{topic}': {e}")

    # Give Kafka a moment to process the deletion completely
    time.sleep(2) 
    
    # 2. Re-create the topic
    print(f"Creating topic '{topic_name}'...")
    # Define topic partitions and replication factor as needed
    new_topic = NewTopic(
        topic_name, 
        # num_partitions=1, 
        # replication_factor=1
    )
    fs = admin_client.create_topics([new_topic], operation_timeout=30)

    # Wait for the creation to finish
    for topic, f in fs.items():
        try:
            f.result()
            print(f"Topic '{topic}' created successfully.")
        except Exception as e:
            print(f"Failed to create topic '{topic}': {e}")

class KafkaProducer():
    producer = Producer(producer_conf)

    def __init__(self, topic = None):
        self.topic = topic
        delete_and_create_topic(admin_client, topic)

    def send(self, msg, topic=None):
        if topic:
            self.topic = topic
            update_retention_period(new_retention_ms_day, topic)

        message_id = rstream.add(msg)
        self.producer.produce(self.topic, message_id.encode('utf-8'))
        self.producer.flush()

    def send_limit_queue_size(self, msg, queue_size, topic = None):
        if topic:
            self.topic = topic
            update_retention_period(new_retention_ms_day, topic)
        while get_number_of_messages_in_topic(self, self.topic) >= queue_size:
            time.sleep(1)
        
        message_id = rstream.add(msg)
        self.producer.produce(self.topic, message_id.encode('utf-8'))
        self.producer.flush()

class KafkaConsumer():
    consumer = Consumer(consumer_conf)
    admin_client = AdminClient(consumer_conf)

    def __init__(self, topic):
        self.topic = topic
        self.consumer.subscribe([topic])

    def recieve_once(self):
        data = {}
        try:
            msg = self.consumer.poll(10.0)
            if not msg.error():
                msg_decoded = msg.value().decode('utf-8')
                data = rstream.read(msg_decoded)
                # send message to transform block
            elif msg.error().code() != KafkaError._PARTITION_EOF:
                print(msg.error())

        except BaseException as be:
            traceback.print_exc()

        if not data:
            print("data returned from stream is empty!")

        self.consumer.commit(msg)
        return data

    # def recieve_continuous(self):
    #     try:
    #         while True:
    #             msg = self.consumer.poll(1.0) # Poll with a timeout of 1 second

    #             if msg is None:
    #                 continue
    #             elif msg.error():
    #                 if msg.error().code() == KafkaException._PARTITION_EOF:
    #                     # End of partition event
    #                     sys.stderr.write('%% %s [%d] reached end of offset %d\n' %
    #                                     (msg.topic(), msg.partition(), msg.offset()))
    #                 else:
    #                     raise KafkaException(msg.error())
    #                 # print('Received message: %s' % msg.value().decode('utf-8'))
    #                 # send message to transform block
    #             else:
    #                 data = {}
    #                 # Process the message
    #                 msg_decoded = msg.value().decode('utf-8')
    #                 data = rstream.read(msg_decoded)

    #                 # send message to transform block
    #                 return data
    #                 # Optionally commit offsets manually after processing
    #                 # consumer.commit(msg)

    #     except BaseException as be:
    #         traceback.print_exc()
    #     # finally:
    #     #     # Close the consumer gracefully to trigger a group rebalance
    #     #     self.consumer.close()
    
    def __del__(self):
        self.consumer.close()