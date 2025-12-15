from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import IntEnum, Enum
from pymilvus import DataType

class index_type_enum(Enum):
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

# class datatype_enum(Enum):
#     DataType.INT8 = "int8"
#     DataType.INT16 = "int16"
#     DataType.INT64 = "int64"
#     DataType.FLOAT = "float"
#     DataType.FLOAT_VECTOR = "float_vector"
#     DataType.VARCHAR = "varchar"
#     DataType.BOOL = "bool"
#     DataType.DOUBLE = "double"
#     DataType.STRING = "string"
#     DataType.ARRAY = "array"
#     DataType.JSON = "json"
#     DataType.GEOMETRY = "geometry"
#     DataType.BINARY_VECTOR = "binary_vector"
#     DataType.FLOAT16_VECTOR = "float16_vector"
#     DataType.BFLOAT16_VECTOR = "bfloat16_vector"
#     DataType.SPARSE_FLOAT_VECTOR = "sparse_float_vector"
#     DataType.INT8_VECTOR = "int8_vector"
#     DataType.NONE = "null"

class metric_type_enum(Enum):
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
    datatype: int
    description: Optional[str] = ""
    is_primary: Optional[bool] = False
    is_dynamic: Optional[bool] = False
    nullable: Optional[bool] = False
    auto_id: Optional[bool] = False # Defined for field only
    is_partition_key: Optional[bool] = False
    is_clustering_key: Optional[bool] = False
    default_value: Optional[Union[int, str]] = ""

class index_params_type(BaseModel):
    field_name: Optional[str] = "index_field"
    index_type: Optional[index_type_enum] = index_type_enum.auto
    index_name: Optional[str] = "index"
    metric_type: Optional[metric_type_enum] = metric_type_enum.cosine # Applied to index only

class id_type_enum(Enum):
    string = "string"
    integer = "int"

class collection_model_type(BaseModel):
    collection_name: str
    model_schema: List[field]
    index_params: Optional[List[index_params_type]] = [Field(index_params_type, gt=0)]
    timeout: Optional[float] = 1
    dimension: Optional[int] = 1
    primary_field_name: Optional[str] = None
    id_type: Optional[id_type_enum] = id_type_enum.integer
    vector_field_name: Optional[str] = "content_vector"
    metric_type: Optional[metric_type_enum] = metric_type_enum.cosine # Applied to entire collection
    auto_id: Optional[bool] = False  # Defined for entire collection
    enable_dynamic_field: Optional[bool] = True  # involved in bulk_writer