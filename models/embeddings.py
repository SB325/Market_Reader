# https://huggingface.co/FinLang/finance-embeddings-investopedia
# This is a finetuned embedding model on top of BAAI/bge-base-en-v1.5. 
# It maps sentences & paragraphs to a 768 dimensional dense vector 
# space and can be used for tasks like clustering or semantic search 
# in RAG applications.

from sentence_transformers import SentenceTransformer
import os, sys
import pdb
from dotenv import load_dotenv
import torch
import numpy as np
import pandas as pd
import networkx as nx

load_dotenv() 

# 'FinLang/finance-embeddings-investopedia'
model_name = os.getenv("EMBEDDING_MODEL_NAME")
model_directory = os.getenv("EMBEDDING_MODEL_DIR")
full_model_path = model_directory + model_name

class embeddings():
    model = None
    def __init__(self):
        print(f"Loading {model_name} model for document embedding.")
        # Load a pre-trained model and tokenizer
        if os.path.exists(full_model_path):
            # load locally saved model
            self.model = SentenceTransformer(full_model_path)
        else:
            # download and save model from huggingface
            self.model = SentenceTransformer(model_name)                                                                          
            self.model.save(full_model_path)

    def encode(self, text: str):
        return self.model.encode(text)
    
    def similarity2(self, text_1: str, text_2: str):
        embedding1 = self.encode(text_1)
        embedding2 = self.encode(text_2)
        return (embedding1*embedding2).sum()
    
    def similarity(self, text_list: pd.DataFrame, threshold: float = 1.0):
        assert isinstance(threshold, float), 'Threshold must be a float'
        assert threshold<=1, "Threshold msut be less than 1"
        assert isinstance(text_list, list), "Text list must be a list"

        embed = self.encode(text_list)
        return self.model.similarity(embed, embed)
    
emb = embeddings()
def group_similar_documents(sentences: list, thresh: float):
    # Takes list of sentences (documents) and groups them by similarity, 
    # returning data object with similar docs grouped by group_id's.
    
    # sentences = {cnt:val for cnt, val in enumerate(sentences)}
    # sentences_pd = pd.Series(sentences)
    simil = torch.tril(emb.similarity(sentences, threshold=thresh),diagonal=-1)

    bool_np = np.array([val for val in simil>thresh])
    matches = pd.DataFrame(np.argwhere(bool_np))

    graph = nx.from_pandas_edgelist(matches, 0, 1)
    groups = list(nx.connected_components(graph))
    corpus_df = pd.DataFrame(sentences, columns = ['title'])
    corpus_df['group_id'] = None

    for cnt, group in enumerate(groups):
        corpus_df.loc[list(group), 'group_id'] = cnt
    
    doc_stats = {'corpus': corpus_df,
                'matrix': simil,
                'ngroups': len(groups)
            }
    return doc_stats

def return_documents_in_group(df, group_id: int):
    retval = df[df['group_id']==group_id]
    return len(retval), retval

if __name__ == "__main__":
    
    sentences = ["This is an example sentence", 
                 "Each sentence is converted",
                 "Happy day, happy day!",
                 "Cars on the road can be very quick.",
                "Street vehicles are swift.",
                "Fast sedans can be found on the highway."
                 ]
    
    groups = group_similar_documents(sentences, 0.5)
    pdb.set_trace()
    print(groups)