from vespa.application import ApplicationPackage
from vespa.package import Schema, Document, Field, FieldSet, HNSW, RankProfile, Component, Parameter

app_package = ApplicationPackage(
    name="vector0",                              
    schema=[                                    
        Schema(
            name="doc0",
            document=Document(
                fields=[
                    Field(name="id", 
                        type="string", 
                        indexing=["summary", "attribute"]
                    ),
                    Field(
                        name="cik",
                        type="string",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="uri",
                        type="uri",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="primaryDocDescription",
                        type="string",
                        indexing=["attribute", "index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="filing_content_string",
                        type="string",
                        indexing=["attribute", "index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="filing_content_embedding",
                        type="tensor<bfloat16>(x[768])",
                        indexing=["attribute", "summary", "index"],
                        ann=HNSW(       # https://zilliz.com/learn/hierarchical-navigable-small-worlds-HNSW
                            distance_metric="innerproduct",
                            max_links_per_node=16,
                            neighbors_to_explore_at_insert=128,
                        ),
                    ),
                ]
            ),
            fieldsets=[FieldSet(name="default", fields=["cik", "primaryDocDescription", "filing_content_string"])],
            rank_profiles=[
                RankProfile(   # https://docs.vespa.ai/en/reference/schema-reference.html#rank-profile
                    name="tensor-default",
                    inputs=[("query(q)", "string")], #"tensor<bfloat16>(x[768])")],
                    first_phase="closeness(field, filing_content_embedding)",
                )
            ],
        )
    ]
)