from vespa.application import ApplicationPackage
from vespa.package import Schema, Document, Field, FieldSet, HNSW, RankProfile
from vespa.deployment import VespaDocker

'''
If :class: ContainerCluster is used, any :class: Component`s must be added to the :class: 
`ContainerCluster, rather than to the :class: ApplicationPackage, 
in order to be included in the generated schema.
'''
ContainerCluster(id="example_container",
   components=[Component(id="e5", type="hugging-face-embedder",
       parameters=[
           Parameter("transformer-model", {"url": "https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx"}),
           Parameter("tokenizer-model", {"url": "https://raw.githubusercontent.com/vespa-engine/sample-apps/master/simple-semantic-search/model/tokenizer.json"})
       ]
   )],
   auth_clients=[AuthClient(id="mtls", permissions=["read", "write"])],
   nodes=Nodes(count="2", parameters=[Parameter("resources", {"vcpu": "4.0", "memory": "16Gb", "disk": "125Gb"})])
)
ContainerCluster(id="example_container", 
                 version="1.0", 
                 nodes="Nodes(count="2")", 
                 components="[Component(id="e5", type="hugging-face-embedder")]", 
                 auth_clients="[AuthClient(id="mtls", permissions="['read', 'write']")]"
                 )


'''
Define a simple application package: https://pyvespa.readthedocs.io/en/latest/reference-api.html
'''
app_package = ApplicationPackage(
    name="vector",                              
    schema=[                                    
        Schema(
            name="doc",
            document=Document(
                fields=[
                    Field(name="id", type="string", indexing=["attribute", "summary"]),
                    Field(
                        name="title",
                        type="string",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="body",
                        type="string",
                        indexing=["index", "summary"],
                        index="enable-bm25",
                    ),
                    Field(
                        name="popularity",
                        type="float",
                        indexing=["attribute", "summary"],
                    ),
                    Field(
                        name="embedding",
                        type="tensor<bfloat16>(x[1536])",
                        indexing=["attribute", "summary", "index"],
                        ann=HNSW(
                            distance_metric="innerproduct",
                            max_links_per_node=16,
                            neighbors_to_explore_at_insert=128,
                        ),
                    ),
                ]
            ),
            fieldsets=[FieldSet(name="default", fields=["title", "body"])],
            rank_profiles=[
                RankProfile(
                    name="default",
                    inputs=[("query(q)", "tensor<float>(x[1536])")],
                    first_phase="closeness(field, embedding)",
                )
            ],
        )
    ],
)

vespa_docker = VespaDocker()
app = vespa_docker.deploy(application_package=app_package)

'''
Visiting is a feature to efficiently get or process a set of documents, 
identified by a document selection expression. Visit yields multiple slices 
(run concurrently) each yielding responses (depending on number of documents in each slice). 
This allows for custom handling of each response.
'''
all_docs = []
for slice in app.visit(
    content_cluster_name="vector_content",
    schema="doc",
    namespace="benchmark",
    selection="true",  # Document selection - see https://docs.vespa.ai/en/reference/document-select-language.html
    slices=4,
    wanted_document_count=300,
):
    for response in slice:
        print(response.number_documents_retrieved)
        all_docs.extend(response.documents)

''' 
Delete all the synthetic data with a custom generator. 
'''
def my_delete_generator() -> dict:
    for i in range(1000):
        yield {"id": str(i)}

    app.feed_iterable(
        iter=my_delete_generator(),
        schema="doc",
        namespace="benchmark",
        callback=callback,
        operation_type="delete",
        max_queue_size=5000,
        max_workers=48,
        max_connections=48,
    )

'''
Updates
We can also perform other update operations, see Vespa docs on reads and writes. 
To achieve this we need to set the auto_assign parameter to False in the feed_iterable 
method (which will pass this to update_data_point-method).
'''
def my_update_generator() -> dict:
    for i in range(1000):
        yield {"id": str(i), "fields": {"popularity": 2.0}}
app.feed_iterable(
    iter=my_update_generator(),
    schema="doc",
    namespace="benchmark",
    callback=callback,
    operation_type="update",
    max_queue_size=4000,
    max_workers=12,
    max_connections=12,
)

from vespa.io import VespaQueryResponse

with app.syncio(connections=1):
    response: VespaQueryResponse = app.query(
        yql="select id from doc where popularity > 2.5", hits=0
    )
    print(response.number_documents_retrieved)

# Feeding operations from a file
# This demonstrates how we can use feed_iter to feed from a large file without reading the entire file, this also uses a generator.

# Dump some operation to a jsonl file, we store it in the format expected by pyvespa
# This to demonstrate feeding from a file in the next section.
import json

with open("documents.jsonl", "w") as f:
    for doc in dataset:
        d = {"id": doc["_id"], "fields": {"id": doc["_id"], "embedding": doc["openai"]}}
        f.write(json.dumps(d) + "\n")

#Get and Feed individual data points
#Feed a single data point to Vespa

with app.syncio(connections=1):
    response: VespaResponse = app.feed_data_point(
        schema="doc",
        namespace="benchmark",
        data_id="1",
        fields={
            "id": "1",
            "title": "title",
            "body": "this is body",
            "popularity": 1.0,
        },
    )
    print(response.is_successful())
    print(response.get_json())

# Cleanup
vespa_docker.container.stop()
vespa_docker.container.remove()