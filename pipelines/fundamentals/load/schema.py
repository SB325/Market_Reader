from util.milvus.collection_model import field

filing_schema = [
    field(
        field_name='cik',
        datatype='int64',
        description="The Central Index Key (CIK) is used on \
            the SEC's computer systems to identify corporations \
            and individual people who have filed disclosure with \
            the SEC.",
        is_partition_key=True,
        is_clustering_key=True
    ),
    field(
        field_name='reportDate',
        datatype='string',
        description="The Date that the filing was disclosed with \
            the SEC.",
        is_partition_key=False,
        is_clustering_key=False
    ),
    field(
        field_name='acceptanceDateTime',
        datatype='timestamptz',
        description="The Date that the filing was accepted by \
            the SEC.",
        is_partition_key=Falsee,
        is_clustering_key=False
    ),
    field(
        field_name='accessionNumber',
        datatype='string    ',
        description="A unique ID the SEC's EDGAR system assigns to each \
            submission, acting as its specific tracking number for status \
            checks and inquiries, composed of the filer's CIK, the year, \
            and a sequential number.",
        is_partition_key=False,
        is_clustering_key=False
    ),
    field(
        field_name='uri',
        datatype='string',
        description="Universal Resource Identifier",
        is_partition_key=False,
        is_clustering_key=False
    ),
    field(
        field_name='primaryDocDescription',
        datatype='string',
        description="main, mandatory part of an SEC filing \
            (like a 10-K, 10-Q, 8-K, or registration statement) \
            that contains the core required financial and business \
            information, formatted in HTML, ASCII, XML, XBRL, or PDF.",
        is_partition_key=False,
        is_clustering_key=True
    ),
    field(
        field_name='filename',
        datatype='string',
        description="The name identifying the file containing a piece of \
            information.",
        is_partition_key=False,
        is_clustering_key=False
    ),
    field(
        field_name='content',
        datatype='json',
        description="The html content of the SEC Filing, both raw and parsed."
        is_partition_key=False,
        is_clustering_key=False
    )
]

