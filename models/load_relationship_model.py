# from langchain_community.chat_models import ChatOllama
# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.runnables import RunnablePassthrough
from gliner import GLiNER
# from glirel import GLiREL
from huggingface_hub import login
login(token="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")
import shutil
import spacy
import pdb
import os
from embeddings import embeddings
import uuid

class ner():
    def __init__(self, ner_model_name: str = None, ent_labels: str = None):
        self.entity_labels = ent_labels

        self.ner_model = GLiNER.from_pretrained(ner_model_name)
        self.nlp = spacy.load("en_core_web_sm")

    def inference(self, text: list, use_gpu: bool = True):

        decimated_text = []
        entity_list = []
        for cnt, txt in enumerate(text):
            decimated_text.append({cnt: txt})
            # entities = []
            # for dec in decimated_text[-1][cnt]:
            entity_list.append({cnt: self.ner_model.predict_entities(txt, self.entity_labels)})

        for cnt, val in enumerate(entity_list):
            for ent in val[cnt]:
                ent.update({'id': str(uuid.uuid4())})

        return entity_list, decimated_text

if __name__ == "__main__":
    # https://huggingface.co/models?sort=trending&search=gliner
    ner_model_name = "urchade/gliner_multi-v2.1"

    ent_labels = [val.upper() for val in ['company', 'country', 'spoke about', 'spoken about', 
                                            'property', 'person', 'group', 'people', 'organization', 
                                                'in conflict with', 'allies', 'state', 'status',
                                                    'immigration status', 'litigation']]

    rel_labels = [
    'assisted with', 
    'was engaged in combat', 
    'disliked', 
    'tried to destroy', 
    'parent of', 
    'located in or next to body of water',  
    'married to',  
    'lived with',
    'living with',
    'child of',  
    'founder of',  
    'founded by',
    'inside of',
    'within',
    'complied with',
    'set requirements for',
    ]

    cm = ner(ner_model_name, ent_labels)

    # text = ["Once upon a time there were three Bears, who lived together in a house of their own, in a wood.",
    #         "One of them was a Little Wee Bear, and one was a Middle-sized Bear, and the other was a Great Big Bear.",
    #         "They had each a bowl for their porridge; a little bowl for the Little Wee Bear; and a middle-sized bowl for the Middle-sized Bear; and a great bowl for the Great Big Bear.",
    #         "And they had each a chair to sit in; a little chair for the Little Wee Bear; and a middle-sized chair for the Middle-sized Bear; and a great chair for the Great Big Bear.",
    #         "And they had each a bed to sleep in; a little bed for the Little Wee Bear; and a middle-sized bed for the Middle-sized Bear; and a great bed for the Great Big Bear.",
    #         ]

    text = ["The Company has also implemented changes to iOS, iPadOS, the App Store and Safari in the EU as it seeks to comply with the DMA.",
            "including new business terms and alternative fee structures for iOS and iPadOS apps, alternative methods of distribution for iOS and iPadOS apps,",
            "alternative payment processing for apps across the Company's operating systems, and additional tools and application programming interfaces (“APIs”) for developers.",
            "The Company has also continued to make changes to its compliance plan in response to feedback and engagement with the Commission.,"
            "Although the Company's compliance plan is intended to address the DMA's obligations, it has been challenged by the Commission and may be challenged further by private litigants.",
            "The DMA provides for significant fines and penalties for noncompliance, and other jurisdictions may seek to require the Company to make changes to its business.",
            "While the changes introduced by the Company in the EU are intended to reduce new privacy and security risks that the DMA poses to EU users, many risks will remain.",
    ]
            
    entities, decimated_text = cm.inference(text=text)

    emb = embeddings()
    nodes = []
    relationships = []
    thresh = 0.5
    for cnt, node_body in enumerate(entities):
        if len(node_body[cnt]) < 2:
            continue

        nodes.extend(node_body[cnt])
        
        for cnt0, node in enumerate(node_body[cnt][:-1]):
            snippet = text[cnt][node['end']+1 : node_body[cnt][cnt0+1]['start']-1]
            semantic_label = [emb.similarity2(snippet, val) for val in rel_labels]
            relation = (rel_labels[semantic_label.index(max(semantic_label))], float(max(semantic_label)))
            if relation[1] < thresh:
                continue
            relationships.append({
                'origin_data_index': cnt,
                'text': snippet,
                'head_id': node['id'],
                'tail_id': node_body[cnt][cnt0+1]['id'],
                'relation_label': relation,
            })

    print("Printing Subject-Predicate-Object Tripilets:")
    for triple in relationships:
        head = triple['head_id']
        tail = triple['tail_id']
        head_node = [val for val in nodes if val['id'] == head][0]
        tail_node = [val for val in nodes if val['id'] == tail][0]
        print(f"[{head_node['text']} | {head_node['label']}] - {triple['relation_label']} | {triple['text']} - [{tail_node['text']} | {tail_node['label']}]")

    pdb.set_trace()
