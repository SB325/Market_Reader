from pymilvus import DataType
import pdb

# https://milvus.io/api-reference/pymilvus/v2.4.x/ORM/FieldSchema/FieldSchema.md

filing_schema =  [
    {
        "field_name": 'cik',
        "datatype": DataType.INT64,
        "description": "The Central Index Key (CIK) is used on \
            the SEC's computer systems to identify corporations \
            and individual people who have filed disclosure with \
            the SEC.",
        "is_partition_key": True,
        "is_clustering_key": False
    },
    {
        "field_name": 'reportDate',
        "datatype": DataType.VARCHAR,
        "description": "The Date that the filing was disclosed with \
            the SEC.",
        "is_partition_key": False,
        "is_clustering_key": False
    },
    {
        "field_name": 'acceptanceDateTime',
        "datatype": DataType.VARCHAR,
        "description": "The Date that the filing was accepted by \
            the SEC.",
        "is_partition_key": False,
        "is_clustering_key": False
    },
    {
        "field_name": 'accessionNumber',
        "datatype": DataType.VARCHAR,
        "description": "A unique ID the SEC's EDGAR system assigns to each \
            submission, acting as its specific tracking number for status \
            checks and inquiries, composed of the filer's CIK, the year, \
            and a sequential number.",
        "is_partition_key": False,
        "is_clustering_key": False,
        "is_primary": True
    },
    {
        "field_name": 'uri',
        "datatype": DataType.VARCHAR,
        "description": "Universal Resource Identifier",
        "is_partition_key": False,
        "is_clustering_key": False
    },
    {
        "field_name": 'primaryDocDescription',
        "datatype": DataType.VARCHAR,
        "description": "main, mandatory part of an SEC filing \
            (like a 10-K, 10-Q, 8-K, or registration statement) \
            that contains the core required financial and business \
            information, formatted in HTML, ASCII, XML, XBRL, or PDF.",
        "is_partition_key": False,
        "is_clustering_key": True
    },
    {
        "field_name": 'filename',
        "datatype": DataType.VARCHAR,
        "description": "The name identifying the file containing a piece of \
            information.",
        "is_partition_key": False,
        "is_clustering_key": False
    },
    {
        "field_name": 'content_vector',
        "datatype": DataType.INT8_VECTOR,
        "description": "The html content of the SEC Filing, both raw and parsed.",
        "is_partition_key": False,
        "is_clustering_key": False,
    }
]

field_params_dict = {
    "field_name": "index_field",
    "index_type": "AUTOINDEX",
    "index_name": "index",
    "metric_type": "COSINE",
}

field_params_dict = [field_params_dict.copy() for _ in range(len(filing_schema))]
[
    field_params_dict[cnt].update({'field_name': val["field_name"]})
    for cnt, val in enumerate(filing_schema)
]

[
    val.update({'metric_type': "bin_vectors"}) for val in field_params_dict
    if 'vector' in val['field_name']
]
