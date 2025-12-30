'''
Requests list of company names, their ticker symbols and their SEC Filing CIK 
'''
import pdb
import traceback
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from util.logger import log
from dotenv import load_dotenv
import zipfile
from tqdm import tqdm
import math
import json
from util.kafka.kafka import KafkaProducer
import subprocess

load_dotenv(override=True)
load_dotenv('util/kafka/.env')

zip_filename = os.getenv("FILINGS_ZIP_FILENAME")
zip_chunk_size = int(os.getenv("ZIP_CHUNK_SIZE"))
topic = os.getenv("KAFKA_TOPIC")

zip_fullpath=os.path.join(os.path.join(os.path.dirname(__file__), '../'), zip_filename)

producer = KafkaProducer()

def get_kafka_ip():
    # Run a command and capture its stdout and stderr
    ip = subprocess.run(
        "docker inspect --format='{{.NetworkSettings.Networks.homeserver.IPAddress}}' kafka",
        capture_output=True,  # Capture stdout and stderr
        text=True,           # Decode output as text (UTF-8 by default)
        shell=True           # Raise CalledProcessError if the command returns a non-zero exit code
    ).stdout.replace('\n', '')
    return ip

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

    try:
        producer = KafkaProducer()
        nfilings = nfilings_in_zip(zip_fullpath)
        filing = read_zip_file(zip_fullpath, nfilings, zip_chunk_size)
        pbar = tqdm(enumerate(filing), 
                    total=math.ceil(nfilings/zip_chunk_size), 
                    desc="Performing Extract+Load of SEC Filings")
        for cnt, downloaded_list in pbar:
            # push objects to kafka log
            pdb.set_trace()
            producer.send_limit_queue_size(topic, downloaded_list, zip_chunk_size)
            pbar.set_description(f"Processing {zip_filename}: {100*zip_chunk_size*(cnt+1)/(nfilings):.2f}%")

    except BaseException as be:
        traceback.print_exc()