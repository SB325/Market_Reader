# from langchain_community.chat_models import ChatOllama
# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.runnables import RunnablePassthrough
from gliner import GLiNER
from glirel import GLiREL
# from huggingface_hub import login
# login(token="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")
import shutil
import spacy
import pdb
import os
from embeddings import embeddings

class ner():
    def __init__(self, ner_model_name: str = None, re_model_name: str = None, ent_labels: str = None, rel_labels: str = None):
        self.entity_labels = ent_labels
        self.rel_labels = rel_labels

        # ner_model_prefix = ner_model_name.split('/')[1]
        # re_model_prefix = re_model_name.split('/')[1]

        # dircontents = os.listdir(os.path.dirname(__file__))
        # if (ner_model_prefix in dircontents) and \
        #         (re_model_prefix in dircontents) and \
        #             ("en_core_web_sm" in dircontents):
        #     self.load_model(ner_model_prefix, re_model_prefix)
        # else:
        self.ner_model = GLiNER.from_pretrained(ner_model_name)
        self.re_model = GLiREL.from_pretrained(re_model_name) 
        self.nlp = spacy.load("en_core_web_sm")
        # self.save_model(ner_model_name.split('/')[1], re_model_name.split('/')[1])

    # def save_model(self, ner_filename: str = '', re_filename: str = ''):
    #     self.ner_model.save_pretrained(os.path.dirname(__file__) + '/' + ner_filename)
    #     self.re_model.save_pretrained(os.path.dirname(__file__) + '/' + re_filename)
    #     self.nlp.to_disk(os.path.dirname(__file__) + '/' + "en_core_web_sm")
    #     print("Saved Models to disk.")

    # def load_model(self, ner_filename: str = '', re_filename: str = ''):
    #     self.ner_model = GLiNER.from_pretrained(os.path.dirname(__file__) + '/' + ner_filename)
    #     self.re_model = GLiREL.from_pretrained(os.path.dirname(__file__) + '/' + re_filename)
    #     self.nlp = spacy.blank("en").from_disk(os.path.dirname(__file__) + '/' + 'en_core_web_sm')
    #     print("Loaded Models from disk.")

    def inference(self, text: list, use_gpu: bool = True):

        entity_list = []
        sorted_data_desc = []
        tokens = []
        non_entity_tokens = []
        for txt in text:
            entities = self.ner_model.predict_entities(txt, self.entity_labels)
            txt = ''.join([val for val in txt if "'" not in val])
            txt = ''.join([val for val in txt if "," not in val])
            txt = ''.join([val for val in txt if ";" not in val])
            txt = ''.join([val for val in txt if "." not in val])
            pdb.set_trace()
            doc = self.nlp(txt)
            tokens.append([token.text for token in doc])

            entity_list.append([list(val.values()) for val in entities])

            if entity_list[-1]:
                relations = self.re_model.predict_relations(tokens[-1], self.rel_labels, threshold=0.0, ner=entity_list[-1], top_k=1)
            else:
                sorted_data_desc.append([])
                non_entity_tokens.append([])
                continue
            [val.update({'head_text': txt[val['head_pos'][0]: val['head_pos'][1]].strip(),'tail_text': txt[val['tail_pos'][0]: val['tail_pos'][1]].strip()}) for val in relations]
            sorted_data_desc.append(sorted(relations, key=lambda x: x['score'], reverse=True))
            
            entity_set = [val[2] for val in entity_list[-1]]

            non_entity_tokens.append(' '.join([val for val in tokens[-1] if val not in entity_set]))
        # pdb.set_trace()
        return entity_list, sorted_data_desc, tokens, non_entity_tokens

if __name__ == "__main__":
    # https://huggingface.co/models?sort=trending&search=gliner
    ner_model_name = "urchade/gliner_multi-v2.1"
    re_model_name = "jackboyla/glirel-large-v0"
    re_model_name = "jackboyla/glirel_beta"

    ent_labels = [val.upper() for val in ['company', 'country', 'spoke about', 'spoken about', 'property', 'person', 'organization', 'in conflict with', 'allies']]

    rel_labels = [
    'assisted with', 
    'was engaged in combat', 
    'disliked', 
    'tried to destroy', 
    'parent of', 
    'located in or next to body of water',  
    'married to',  
    'child of',  
    'founder of',  
    'founded by',
    ]

    cm = ner(ner_model_name, re_model_name, ent_labels, rel_labels)

    text = ["Once upon a time there were three Bears, who lived together in a house of their own, in a wood.",
            "One of them was a Little Wee Bear, and one was a Middle-sized Bear, and the other was a Great Big Bear.",
            "They had each a bowl for their porridge; a little bowl for the Little Wee Bear; \
                and a middle-sized bowl for the Middle-sized Bear; and a great bowl for the Great Big Bear.",
            "And they had each a chair to sit in; a little chair for the Little Wee Bear; \
                and a middle-sized chair for the Middle-sized Bear; and a great chair for the Great Big Bear.",
            "And they had each a bed to sleep in; a little bed for the Little Wee Bear; \
                and a middle-sized bed for the Middle-sized Bear; and a great bed for the Great Big Bear.",
            ]

    pdb.set_trace()
    entities, relationships, tokens, non_entity_tokens = cm.inference(text=text)
    pdb.set_trace()

    print("\nRelationships Descending Order by Score:")
    emb = embeddings()
    for cnt, item in enumerate(relationships):
        if non_entity_tokens[cnt]:
            forward_item = [val for val in item if val['head_pos'][0] < val['tail_pos'][0]]
            for fi in forward_item:
                for ent in entities:
                    head_category = {val[3]: val[0:2] for val in ent if fi['head_text'] in val[3]}
                    tail_category = {val[3]: val[0:2] for val in ent if fi['tail_text'] in val[3]}
                pdb.set_trace()
                non_entities = non_entity_tokens[cnt][[*head_category][1] : [*tail_category][1]]
                semantic_label = [emb.similarity2(non_entity_tokens[cnt], val) for val in rel_labels]

                relation = rel_labels[semantic_label.index(max(semantic_label))]
                print(f"{fi['head_text']} {[*head_category][0]} --> {relation} --> {fi['tail_text']}  {[*tail_category][0]} | score: {fi['score']} | {non_entity_tokens}")

    print(f"Entities:\n{entities}")
    print(f"Non Entity Tokens:\n{non_entity_tokens}")
    zipped = list(zip(semantic_label, rel_labels))
    print(f"Similarity Scores:")
    [print(z) for z in zipped]

    pdb.set_trace()
