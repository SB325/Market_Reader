from pymilvus import MilvusClient, DataType, Collection
from collection_model import collection_model
from util.logger import log
import pdb

class crud_milvus():
    def __init__(self):
        self.client = MilvusClient(
            uri="http://172.18.0.12:19530",
        )

    def insert(
            collection_name: str = "",
            data: list = [],
            timeout: int = 1
        )
        success = False
        try:
            collection = Collection(collection_name) 
            collection.insert(data=data,
                            timeout=timeout)
            success = True
        except BaseException as be:
            log.Errmsg(f"{be}")

        return success

    def query(
            collection_name: str = "",
            expr: str = "*", 
            offset: int = 0 , 
            limit: int = 1000, 
            output_fields: list = ["*"], 
            partition_names=None, 
            timeout=2
        ):
        # https://milvus.io/api-reference/pymilvus/v2.2.x/Collection/query().md
        pdb.set_trace()
        try:
            collection = Collection(collection_name) 
            results = collection.query(
                expr=expr,
                offset=offset,
                limit=limit,
                output_fields=ouput_fields,
                partition_names=partition_names,
                timeout=timeout
            )
        except BaseException as be:
            log.Errmsg(f"{be}")
        return results

    def create_collection(self, collection_obj: collection_model)  #collection_model = pydantic BaseModel
        collection = collection_obj.model_dump()

        # 3.1. Create schema    
        self.schema = MilvusClient.create_schema()

        # 3.2. Add fields to schema
        collection_schema = collection.get('schema', None)
        if len(collection_schema):
            for field in collection_schema:
                self.schema.add_field(**field)

        # 3.3. Prepare index parameters
        index_params = self.client.prepare_index_params()

        # 3.4. Add indexes
        collection_index_params = collection.get(index_params, None)
        if len(collection_index_params):
            for index in collection_index_params
                    index_params.add_index(**index)

        # 3.5. Create a collection with the index loaded simultaneously
        self.client.create_collection(
            collection_name=collection['collection_name'],
            schema=self.schema, 
            index_params=index_params, 
            timeout=collection.get('timeout', None), 
            dimension=collection.get('dimension', None), 
            primary_field_name=collection.get('primary_field_name', None),  
            id_type=collection['id_type'], 
            vector_field_name=collection.get('vector_field_name', None),  
            metric_type=collection.get('metric_type', None),
            auto_id=collection.get('auto_id', None),
            enable_dynamic_field=collection.get('enable_dynamic_field', None),
        )

    def get_collection_state(self, collection_name: str):
        res = self.client.get_load_state(
            collection_name=collection_name
        )
        if not res:
            return None
        return res