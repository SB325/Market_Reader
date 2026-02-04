import pdb
import traceback
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, ConfigResource, NewTopic, ResourceType
from dotenv import load_dotenv
from util.redis.redis_util import RedisStream
import time
import subprocess
import json
from uuid import uuid4
from util.otel import otel_tracer, otel_metrics, otel_logger

otraces = otel_tracer()
ologs = otel_logger()

# https://opentelemetry-python.readthedocs.io/en/latest/sdk/index.html
load_dotenv(override=True)
group_id = os.getenv("GROUP_ID")
redis_stream_name_facts = os.getenv("REDIS_FACTS_STREAM_NAME")
redis_stream_name_submissions = os.getenv("REDIS_SUBMISSIONS_STREAM_NAME")
in_docker = os.getenv("INDOCKER")

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
    'default.topic.config': {'auto.offset.reset': 'earliest'},
    'group.id': group_id,
}
admin_client = AdminClient(producer_conf)

def get_number_of_messages_in_topic(self, topic):
    unused_consumer = Consumer(consumer_conf)
    with otraces.set_span('kafka_list_topics') as span:
        metadata = admin_client.list_topics(topic=topic, timeout=10)
    if topic not in metadata.topics:
        ologs.error(f"Error: Topic '{topic}' not found.")
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
        restype=ResourceType.TOPIC,
        name=topic,
        described_configs={"retention.ms": new_retention_ms_day},
    )
    with otraces.set_span('kafka_update_retention_period') as span:
        span.set_attribute("retention_period", retention_time_ms)
        fs = admin_client.alter_configs([config_resource])
    try:
        fs[config_resource].result()
        ologs.info(f"Topic configuration successfully altered to {new_retention_ms_day}ms retention")
    except Exception as e:
        ologs.error(f"Failed to alter topic config: {e}")

def delete_topic(admin_client, topic_name):
    """Deletes a topic and re-creates it to clear all messages."""
    
    # 1. Delete the topic
    ologs.info(f"Deleting topic '{topic_name}'...")
    with otraces.set_span('kafka_delete_topics') as span:
        span.set_attribute("topic", topic_name)
        fs = admin_client.delete_topics([topic_name], operation_timeout=30)
    
    # Wait for the deletion to finish (optional but recommended in scripts)
    for topic, f in fs.items():
        try:
            f.result()
            ologs.info(f"Topic '{topic}' deleted successfully.")
        except Exception as e:
            # Handle cases where the topic might not exist or other errors
            ologs.error(f"Failed to delete topic '{topic}': {e}")

    # Give Kafka a moment to process the deletion completely
    time.sleep(2) 
    
def create_topic(admin_client, topic_name):
    # 2. Re-create the topic
    ologs.info(f"Creating topic '{topic_name}'...")
    # Define topic partitions and replication factor as needed
    new_topic = NewTopic(
        topic_name, 
        # num_partitions=1, 
        # replication_factor=1
    )
    with otraces.set_span('kafka_create_topic') as span:
        span.set_attribute("topic", topic_name)
        fs = admin_client.create_topics([new_topic], operation_timeout=30)

    # Wait for the creation to finish
    for topic, f in fs.items():
        try:
            f.result()
            ologs.info(f"Topic '{topic}' created successfully.")
        except Exception as e:
            ologs.error(f"Failed to create topic '{topic}': {e}")

class KafkaProducer():
    producer = Producer(producer_conf)

    def __init__(self, topic = None, clear_topic: bool = True, redis_stream_name=''):
        self.topic = topic
        if clear_topic:
            self.clear_topic(topic)
        update_retention_period(new_retention_ms_day, topic)
        self.rstream = RedisStream(redis_stream_name)

    def clear_topic(self, topic):
        if self.clear_topic:
            if isinstance(topic, list):
                [delete_topic(admin_client, tpc) for tpc in topic]
            else:
                delete_topic(admin_client, topic)
            if isinstance(topic, list):
                [create_topic(admin_client, tpc) for tpc in topic]
            else:
                create_topic(admin_client, topic)

    def send(self, msg, topic=None, use_redis: bool = True):
        if topic:
            self.topic = topic
        if use_redis:
            with otraces.set_span('redis_add_message') as span:
                message_id = self.rstream.add(msg, self.topic)
                span.set_attribute("message_id", message_id)
            with otraces.set_span('kafka_produce_message') as span:
                span.set_attribute("topic", self.topic)
                self.producer.produce(self.topic, message_id.encode('utf-8'))
        else:
            with otraces.set_span('kafka_produce_message') as span:
                span.set_attribute("topic", self.topic)
                self.producer.produce(self.topic, msg.encode('utf-8'))
            
        self.producer.flush()
    
    def __del__(self):
        self.producer.close()

class KafkaConsumer():

    def __init__(self, 
                    commit_immediately: bool = True, 
                    topic: list = [],
                    partition_messages = True,
                    unique_group_id: str = '',
                    redis_stream_name=''):
        self.topic = topic
        [create_topic(admin_client, tpc) for tpc in topic]

        self.commit_immediately = commit_immediately
        if not commit_immediately:
            consumer_conf.update({'enable.auto.commit': 'false'})
        if not partition_messages:
            uuid = str(uuid4())
            consumer_conf['group.id'] = f"{unique_group_id}.{uuid}"
        self.consumer = Consumer(consumer_conf)
        self.consumer.subscribe(topic)
        self.rstream = RedisStream(redis_stream_name)

    def recieve_once(self,
                    use_redis: bool = True,
                    timeout = 10
                    ):
        data = ''
        try:
            with otraces.set_span('kafka_consume_message') as span:
                span.set_attribute("topic", self.topic)
                span.set_attribute("timeout", timeout)
                msg = self.consumer.poll(timeout)
            if msg:
                if not msg.error():
                    msg_decoded = msg.value().decode('utf-8')
                    if use_redis:
                        with otraces.set_span('redis_read_message') as span:
                            data = self.rstream.read(msg_decoded, self.topic)
                            span.set_attribute("message_id", msg_decoded)
                        # send message to transform block
                    else: 
                        data = msg_decoded
                elif msg.error().code() != KafkaError._PARTITION_EOF:
                    ologs.error(msg.error())
                    raise BaseException(msg.error())
                elif msg.error().code() == KafkaError._PARTITION_EOF:
                    ologs.error(f'Reached end of topic/partition: {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

        except BaseException as be:
            traceback.print_exc()

        if self.commit_immediately:
            self.consumer.commit(msg)
        return data

    def __del__(self):
        self.consumer.close()

    
    