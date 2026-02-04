'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
import pdb
import traceback
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from dotenv import load_dotenv
import zipfile
from tqdm import tqdm
import math
import json
import time
from util.kafka.kafka import KafkaProducer
from util.redis.redis_util import RedisStream
import subprocess
import argparse
from util.otel import otel_tracer, otel_logger

load_dotenv(override=True)
load_dotenv('.env')
load_dotenv('util/kafka/.env')

facts_zip_filename = os.getenv("FACTS_ZIP_FILENAME")
submissions_zip_filename = os.getenv("SUBMISSIONS_ZIP_FILENAME")
zip_chunk_size = int(os.getenv("ZIP_CHUNK_SIZE"))
queue_size = int(os.getenv("QUEUE_SIZE"))

def read_zip_file(zip_path, nfilings, chunk_size):
    with zipfile.ZipFile(zip_path) as zip_ref:
        for i in range(0, nfilings, chunk_size):
            fact_obj = []
            info_chunk = zip_ref.infolist()[i:i + chunk_size]
            for info in info_chunk:
                if info.flag_bits & 0x1 == 0:
                    if not 'placeholder.txt' in info.filename:
                        with zip_ref.open(info, 'r') as f:
                            # You can read the contents of the file here
                            fact_obj.append(json.loads(f.read().decode('utf-8')))
            yield fact_obj

def nfilings_in_zip(zip_path):
    return len(zipfile.ZipFile(zip_path).infolist())

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
                    prog='Stream Unzipper',
                    description='This process Extracts a Facts or Submissions \
                        EDGAR .zip file and populates the contents into kafka-redis \
                        streams for distributed consumption by replicated facts \
                        Transform/Load pipelines.',
                    epilog='by: SFB')
    parser.add_argument('fileType', 
                    help='either \'facts\' or \'submissions\'',
                    choices=['facts', 'submissions'])  # on/off flag
    args = parser.parse_args()
    fileType = args.fileType
    if 'facts' in fileType:
        zip_filename = facts_zip_filename
        topic = os.getenv("FACTS_KAFKA_TOPIC")
        redis_stream_name = os.getenv("REDIS_FACTS_STREAM_NAME")
    elif 'submissions' in fileType:
        zip_filename = submissions_zip_filename
        topic = os.getenv("SUBMISSIONS_KAFKA_TOPIC")
        redis_stream_name = os.getenv("REDIS_SUBMISSIONS_STREAM_NAME")

    otraces = otel_tracer()
    ologs = otel_logger()

    # Clear Redis stream objects before starting
    rstream = RedisStream(redis_stream_name)
    rstream.delete_stream(redis_stream_name)
    
    zip_fullpath=os.path.join(os.path.join(os.path.dirname(__file__), '../'), zip_filename)
    
    try:
        producer = KafkaProducer(topic=topic, redis_stream_name=redis_stream_name)
        nfilings = nfilings_in_zip(zip_fullpath)
        chunk_size = math.ceil(nfilings/100)
        filing = read_zip_file(zip_fullpath, nfilings, chunk_size)
        pbar = tqdm(enumerate(filing), 
                    total=math.ceil(nfilings/chunk_size), 
                    desc="Performing Extract+Load of SEC Filings")

        with otraces.set_span(f'extract_{fileType}_stream_unzip') as span:
            span.set_attribute("topic", topic)
            for cnt, downloaded_list in pbar:
                # push objects to kafka log
                producer.send(downloaded_list)
                pbar.set_description(f"Processing {zip_filename}: {100*chunk_size*(cnt+1)/(nfilings):.2f}%")

    except BaseException as be:
        traceback.print_exc()
    
    # temporary wait to keep process open long enough for data to run through
    while True:
        time.sleep(1)