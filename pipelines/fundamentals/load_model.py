import os
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel, pipeline
from dotenv import load_dotenv
load_dotenv()   

VESPA_MODEL_STORAGE = os.getenv("VESPA_VAR_STORAGE") + '/models'

if not os.path.exists(f'{VESPA_MODEL_STORAGE}/model.safetensors'):
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    model.save_pretrained(VESPA_MODEL_STORAGE)
    model = AutoModel.from_pretrained(VESPA_MODEL_STORAGE)
    tokenizer = AutoTokenizer.from_pretrained(VESPA_MODEL_STORAGE)
else:
    model = AutoModel.from_pretrained(VESPA_MODEL_STORAGE)
    tokenizer = AutoTokenizer.from_pretrained(VESPA_MODEL_STORAGE)