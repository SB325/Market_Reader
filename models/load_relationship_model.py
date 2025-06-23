# from langchain_community.chat_models import ChatOllama
# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.runnables import RunnablePassthrough
from gliner import GLiNER
from glirel import GLiREL
import shutil
import spacy
import pdb
import os

class ner():
    def __init__(self, ner_model_name: str = None, re_model_name: str = None, labels: str = None):
        self.labels = labels

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

        entities = self.ner_model.predict_entities(text, self.labels)
        
        doc = self.nlp(text)
        tokens = [token.text for token in doc]

        entity_list = [list(val.values()) for val in entities]
        relations = self.re_model.predict_relations(tokens, self.labels, threshold=0.0, ner=entity_list, top_k=1)

        sorted_data_desc = sorted(relations, key=lambda x: x['score'], reverse=True)

        return sorted_data_desc

if __name__ == "__main__":
    # https://huggingface.co/models?sort=trending&search=gliner
    ner_model_name = "urchade/gliner_multi-v2.1"
    re_model_name = "jackboyla/glirel_beta"
    
    labels = ['country of origin', 'person', 'company', 'licensed to broadcast to', 'father', 'followed by', 'characters']

    cm = ner(ner_model_name, re_model_name, labels)

    text = 'Jack Dorsey owned the company named Twitter. Jack started the company in 2008. He sold the company to his dad John who moved to Germany the year after.'
    #  The company also stated it will not seek listing on OTC \
    # Markets due to associated costs and in light of other ongoing corporate developments. "

    entities = cm.inference(text=text)

    print("\nDescending Order by Score:")
    for item in entities:
        print(f"{item['head_text']} --> {item['label']} --> {item['tail_text']} | score: {item['score']}")

    # pdb.set_trace()