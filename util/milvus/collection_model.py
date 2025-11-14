from pydantic import BaseModel
from pymilvus import DataType
from typing import List, Optional
from enum import IntEnum, Enum

class index_type_enum(str, Enum):
    auto = "AUTOINDEX"
    gpu_ivf_flat = "GPU_IVF_FLAT"
    gpu_ivf_pq = "GPU_IVF_PQ"
    flat = "FLAT"
    ivf_flat = "IVF_FLAT"
    ivf_sq8 = "IVF_SQ8"
    ivf_pq = "IVF_PQ"
    hnsw = "HNSW"
    bin_flat = "BIN_FLAT"
    bin_ivf_flat = "BIN_IVF_FLAT"
    diskann = "DISKANN"
    gpu_cagra = "GPU_CAGRA"
    gpu_brute_force = "GPU_BRUTE_FORCE"

class datatype_enum(Enum):
    int8 = DataType.INT8
    int16 = DataType.INT16
    int32 = DataType.INT32
    int64 = DataType.INT64
    float = DataType.FLOAT
    float_vector = DataType.FLOAT_VECTOR
    varchar = DataType.VARCHAR
    bool = DataType.BOOL
    double = DataType.DOUBLE
    string = DataType.STRING
    array = DataType.ARRAY
    json = DataType.JSON
    geometry = DataType.GEOMETRY
    timestamptz = DataType.TIMESTAMPTZ
    binary_vector = DataType.BINARY_VECTOR
    float16_vector = DataType.FLOAT16_VECTOR
    bfloat16_vector = DataType.BFLOAT16_VECTOR
    sparse_float_vector = DataType.SPARSE_FLOAT_VECTOR
    int8_vector = DataType.INT8_VECTOR
    null = DataType.NONE

class metric_type_enum(str, Enum):
    cosine = "COSINE"
    ids = "ids"
    float_vectors = "float_vectors"
    bin_vectors = "bin_vectors"
    metric = "metric"
    l2 = "L2"
    ip = "IP"
    bm25 = "BM25"
    hamming = "HAMMING"
    tanimoto = "TANIMOTO"
    jaccard = "JACCARD"
    sqrt = "sqrt"
    dim = "dim"

class field(BaseModel):
    field_name: str
    datatype: datatype_enum
    description: Optional[str]
    is_primary: Optional[bool] = False
    is_dynamic: Optional[bool] = False
    nullable: Optional[bool] = False
    auto_id: Optional[bool] = False # Defined for field only
    is_partition_key: Optional[bool]
    is_clustering_key: Optional[bool]
    default_value: Optional[Union[int, str]]
    # struct_schema: # from pymilvus/orm/schema.py
    # max_capacity: # from pymilvus/orm/schema.py
    # mmap_enabled: # from pymilvus/orm/schema.py

class index_params(BaseModel):
    field_name: str
    index_type: Optional[index_type_enum]
    index_name: Optional[str]
    metric_type: Optional[metric_type_enum]  # Applied to index only

class id_type_enum(str, Enum):
    string = "string"
    integer = "int"

class collection_model(BaseModel):
    collection_name: str
    schema: Optional[List[field]]
    index_params: Optional[List[index_params]]
    timeout: Optional[float]
    dimension: Optional[int]
    primary_field_name: Optional[str] = "id"
    id_type: id_type_enum
    vector_field_name: Optional[str] = "vector"
    metric_type: Optional[metric_type_enum] # Applied to entire collection
    auto_id: Optional[bool] = False  # Defined for entire collection
    enable_dynamic_field: Optional[bool] = True  # involved in bulk_writer
    
    
    
