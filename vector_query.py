from vespa.io import VespaQueryResponse
from pipelines.fundamentals.vectorize import app
from dotenv import load_dotenv
import sys
import pdb

class vector_query():
    def __init__(self):
        nrecords = self.number_of_records()
        print(f"VECTOR_QUERY:\nNUMBER OF RECORDS IN DB = {nrecords}")

    def assess_response(self, response):
        if response.is_successful():
                ndocsretrieved = response.number_documents_retrieved
                operation = response.operation_type
                nindexed = response.number_documents_indexed
                nhits = len(response.hits)
                print(
                    f"NDocsRetrieved: {ndocsretrieved}\n" + \
                    f"NDocsWithheld: {ndocsretrieved - nhits}\n" + \
                    f"Operation: {operation}\n" + \
                    f"NIndexed: {nindexed}\n"
                )
        else:
            print("Response Error")
            pdb.set_trace()

    def fields(self):
        schema = app.application_package.get_schema()
        fields = schema.document.fields
        field_dicts = [field.__dict__ for field in fields]
        return field_dicts

    def schema_fields(self, fieldset_name: str = "default"):
        return app.application_package.get_schema().fieldsets[fieldset_name].__dict__

    def rank_profiles(self):
        return app.application_package.get_schema().rank_profiles

    def number_of_records(self) -> int:
        with app.syncio() as session:
            response: VespaQueryResponse = session.query(
                    yql='select * from sources * where true'
                    ).number_documents_indexed
        return response

    def query_bm25(self, 
                query_str : str,
                yql : str = "select * from sources * WHERE userQuery()", 
                verbose : bool = True,
                hits : int = 10,
                ):
        with app.syncio() as session:
            response: VespaQueryResponse = session.query(
                        yql=yql,
                        hits=hits,
                        query=query_str,
                        ranking="bm25_ranking",
                    )
            if verbose:
                self.assess_response(response)
                self.get_hits_uri(response)
        return response
        
    def query_semantic(self, 
                       query_str : str,
                       yql : str = "select * from sources * WHERE userQuery()", 
                       verbose : bool = True,
                       hits : int = 10,
                       ):
        with app.syncio() as session:
            response: VespaQueryResponse = session.query(
                        yql=yql,
                        hits=10,
                        query=query_str,
                        ranking="semantic_ranking",
                    )
            if verbose:
                self.assess_response(response)
                self.get_hits_uri(response)
        return response

    def get_hits_uri(self, response):
        return [print(f"{hit['fields']['uri']} {hit['relevance']}") 
                for hit in response.hits]

if __name__ == "__main__":
    vquery = vector_query()

    query = sys.argv[1]
    response = vquery.query_semantic(query)

    pdb.set_trace()
