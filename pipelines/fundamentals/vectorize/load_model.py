import os
from sentence_transformers import SentenceTransformer
from transformers import PreTrainedModel, PreTrainedTokenizer
from dotenv import load_dotenv
import pdb
load_dotenv()   

VESPA_MODEL_STORAGE = os.getenv("VESPA_VAR_STORAGE") + '/models'
model_name = 'BAAI/bge-base-en'

# pdb.set_trace()
# if not os.path.exists(f'{VESPA_MODEL_STORAGE}/model.safetensors'):
model = SentenceTransformer(model_name)
tokenizer = model.tokenizer
# model.save_pretrained(VESPA_MODEL_STORAGE)
# tokenizer.save_pretrained(VESPA_MODEL_STORAGE)
# else:
#     model = PreTrainedModel.from_pretrained(VESPA_MODEL_STORAGE)
#     tokenizer = PreTrainedTokenizer.from_pretrained(VESPA_MODEL_STORAGE)