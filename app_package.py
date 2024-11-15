from vespa.application import ApplicationPackage
from vespa.package import (
    Schema, 
    Document, 
    Field, 
    FieldSet, 
    HNSW, 
    RankProfile, 
    Component, 
    Parameter,
    Function,
    FirstPhaseRanking, 
    SecondPhaseRanking,
)

app_package = ApplicationPackage(
    name="vector0",                              
    schema=[                                    
        Schema(
            name="doc0",
            document=Document(
                fields=[
                    Field(
                        name="id", 
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
                        name="date_string",
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
                        name="embedding",
                        type="tensor<bfloat16>(p{},x[768])",
                        indexing=["attribute", "index"],
                        ann=HNSW(
                            distance_metric="euclidean",
                            max_links_per_node=16,
                            neighbors_to_explore_at_insert=128,
                        ),
                    ),
                ]
            ),
            rank_profiles=[
                RankProfile(
                    name="bm25_ranking",
                    inputs=[("query(q)", "string")],
                    first_phase="bm25(filing_content_string)"
                ),
                RankProfile(
                    name="semantic_ranking",
                    inputs=[("query(q)", "tensor<bfloat16>(x[768])")],
                    first_phase="distance(field, embedding)"
                )
            ],
        )
    ]
)

# 'date' field is a synthetic field that converts date_string provided by
# data source to an epoch (long). 'date' must be set outside of the
# document section.
app_package.schema.add_fields(
            Field(
                name="date",
                type="long",
                indexing=input["date_string", "to_epoch_second", "attribute", "summary"],
                index="enable-bm25",
            ),
            fieldsets=[
                FieldSet(
                    name="default", 
                    fields=["id", 
                        "cik", 
                        "uri", 
                        "reportDate",
                        "date",
                        "primaryDocDescription", 
                        "filing_content_string",
                    ]
                )
            ]
)