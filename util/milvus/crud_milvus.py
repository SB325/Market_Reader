from pymilvus import MilvusClient, DataType, Collection
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from collection_model import collection_model_type
import pdb
from util.otel import otel_tracer, otel_metrics, otel_logger

otraces = otel_tracer()
ometrics = otel_metrics()
ologs = otel_logger()

# https://opentelemetry-python.readthedocs.io/en/latest/sdk/index.html
def get_db_ip():
    import subprocess

    # Run a command and capture its stdout and stderr
    ip = subprocess.run(
        "docker inspect --format='{{.NetworkSettings.Networks.homeserver.IPAddress}}' milvus",  # Command and its arguments as a list
        capture_output=True,  # Capture stdout and stderr
        text=True,           # Decode output as text (UTF-8 by default)
        shell=True           # Raise CalledProcessError if the command returns a non-zero exit code
    ).stdout.replace('\n', '')
    return ip

class crud_milvus():
    def __init__(self):
        self.client = MilvusClient(
            uri=f"http://{get_db_ip()}:19530",
        )

    def insert(self,
            collection_name: str = "",
            data: list = [],
            timeout: int = 1,
        ):
        success = False
        try:
            collection = Collection(collection_name) 
            with otraces.set_span('milvus_insert') as span:
                span.set_attribute("collection_name", collection_name)
                collection.insert(data=data,timeout=timeout)
            success = True
        except BaseException as be:
            log.error(f"{be}")

        return success

    def query(self,
            collection_name: str = "",
            expr: str = "*", 
            offset: int = 0 , 
            limit: int = 1000, 
            output_fields: list = ["*"], 
            partition_names=None, 
            timeout=2,
        ):
        # https://milvus.io/api-reference/pymilvus/v2.2.x/Collection/query().md
        collection = []
        try:
            if not self.client.list_collections():
                return collection
            collection = Collection(collection_name) 
            with otraces.set_span('milvus_query') as span:
                span.set_attribute("collection_name", collection_name)
                span.set_attribute("expression", expr)
                results = collection.query(
                    expr=expr,
                    offset=offset,
                    limit=limit,
                    output_fields=ouput_fields,
                    partition_names=partition_names,
                    timeout=timeout,
                )
            
        except BaseException as be:
            log.error(f"{be}")
        return collection

    def create_collection(self, collection_obj: collection_model_type):  #collection_model = pydantic BaseModel
        collection = collection_obj.model_dump()

        # 3.1. Create schema    
        self.schema = MilvusClient.create_schema()

        # 3.2. Add fields to schema
        collection_schema = collection.get('model_schema', None)
        if len(collection_schema):
            for field in collection_schema:
                self.schema.add_field(**field)

        # 3.3. Prepare index parameters
        index_params_obj = self.client.prepare_index_params()

        # 3.4. Add indexes
        collection_index_params = collection.get('index_params', None)
        if len(collection_index_params):
            for index in collection_index_params:
                index_params_obj.add_index(**index)

        # 3.5. Create a collection with the index loaded simultaneously
        with otraces.set_span('milvus_create_collection') as span:
            span.set_attribute("collection_name", collection['collection_name'])
            self.client.create_collection(
                collection_name=collection['collection_name'],
                schema=self.schema, 
                index_params=index_params_obj, 
                timeout=collection.get('timeout', None), 
                dimension=collection.get('dimension', None), 
                primary_field_name=collection.get('primary_field_name', None),  
                id_type=collection['id_type'], 
                vector_field_name=collection.get('vector_field_name', None),  
                metric_type=collection.get('metric_type', None),
                auto_id=collection.get('auto_id', None),
                enable_dynamic_field=collection.get('enable_dynamic_field', False),
            )

    def get_collection_state(self, collection_name: str):
        with otraces.set_span('milvus_get_collection_state') as span:
            span.set_attribute("collection_name", collection_name)
            res = self.client.get_load_state(
                collection_name=collection_name
            )
        if not res:
            return None
        return res