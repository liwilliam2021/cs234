import os

import torch.cuda
from transformers import AutoModelForCausalLM, AutoTokenizer

from toolformer.data_generator import DataGenerator
from toolformer.api import LocationAPI
from toolformer.prompt import location_prompt
from toolformer.utils import yaml2dict

from dvc.repo import Repo
from datetime import datetime
from dotenv import load_dotenv

from huggingface_hub import snapshot_download, login

load_dotenv()
access_token = os.environ.get("HF_TOKEN")
# login(token = access_token)
#snapshot_download(repo_id ="meta-llama/Llama-2-13b")

import logging

config = yaml2dict('configs/default.yaml')
match config['model']['torch_dtype']:
    case 'float16':
        torch_dtype = torch.float16
    case 'float32':
        torch_dtype = torch.float32
    case 'float64':
        torch_dtype = torch.float64
    case 'bfloat16':
        torch_dtype = torch.bfloat16
    case _:
        raise ValueError('torch_dtype is invalid')


DATE_TIME = datetime.strftime(datetime.now(),"%F_%H-%M-%S")
LOG_PATH = f'alfred/logs/{config["model"]["path"]},torch_dtype={torch_dtype}/{DATE_TIME}.log'
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
OUTPUT_PATH = f'alfred/logs/{config["model"]["path"]},torch_dtype={torch_dtype}/{DATE_TIME}.json'
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(module)s %(funcName)s %(lineno)d] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)

logging.info(f"model={config['model']['path']}, torch_dtype={config['model']['torch_dtype']}")

# Alfred: needs to look for QA based on the qa_prompt which was given
location_api = LocationAPI(
    "Location", location_prompt, cities_csv='alfred/uscities.csv',
    sampling_threshold=0.2, filtering_threshold=0.2
)


#%%
model = AutoModelForCausalLM.from_pretrained(config['model']['path'], torch_dtype=torch_dtype)
tokenizer = AutoTokenizer.from_pretrained(config['model']['path']) #"EleutherAI/gpt-j-6B") #, token=access_token)
print('finished loading model')


texts= []
#texts.append("The landowners in Baltimore want to appeal to the state of Maryland for help.")

texts.append("From Baltimore, MD we have that Baltimore is in the state of Maryland.")

texts.append("From Cleveland, OH we have that Seattle is in the state of Ohio.")

texts.append("From Cleveland, OH we have that Portland is in the state of Texas.")




#texts.append("several wealthy Marylanders pushed through the State Legislature a town charter for Baltimore.")


# texts.append(
#     """1729 to 1752 – The Beginning
# There was nothing unusual in 1729 when several
# wealthy Marylanders pushed through the State Legislature a town charter for Baltimore. Town charters
# were issued routinely across the State in those times.
# In 1730, Baltimore Town was established with sixty
# lots, one-acre each, and located on the north side of
# the Inner Basin of the Patapsco River (now the Inner
# Harbor). These lots were squeezed in between a shallow harbor on the south; the Jones Falls River and
# marsh on the east; a bluff and woods on the north; and
# large gullies on the west. In 1745, Jonestown, a small
# settlement just east of the Jones Falls, was merged
# into Baltimore, adding twenty more lots to the town.
# By 1752, only twenty-five buildings had been constructed in Baltimore– a rate of approximately one building per year. Shortly
# after 1752, the pace changed.
# 1752 to 1773 – Seizing the Geography
# The rise of Baltimore from a sleepy town trading in tobacco to a city rivaling Philadelphia, Boston, and New York began when Dr. John Stevenson, a
# prominent Baltimore physician and merchant, began shipping flour to Ireland. The success of this seemingly insignificant venture opened the eyes
# of many Baltimoreans to the City’s most extraordinary advantage– a port
# nestled alongside a vast wheat growing countryside, significantly closer to
# this rich farm land than Philadelphia.
# The town exploded with energy, and Baltimoreans restructured the City’s
# economy based on flour. Trails heading west were transformed into roads;
# flour mills were built along the Jones Falls, Gwynns Falls, and Patapsco River; and merchants built warehouses on thousand-foot long wharves that extended into the harbor. Soon, the roads from Baltimore extended all the way
# to Frederick County and southern Pennsylvania, and Baltimore ships sailed
# beyond Ireland to ports in Europe, the Caribbean, and South America.
# The City’s widening reach was also apparent in the foreign-born populations
# it attracted. In 1756 a group of nine hundred Acadians, French-speaking Catholics from Nova Scotia, made what homes they could in an undeveloped tract
# along the waterfront. This pattern would be repeated by numerous groups over
# subsequent decades and centuries: entry into Baltimore’s harbor, a scramble
# for housing near the centers of commerce, and a dispersion throughout the
# city as much as space, means and sometimes stigma would allow. But not all
# newcomers started at a disadvantage. During this period, Irish, Scottish and
# German families with experience and capital gained from milling in other
# parts of the region took advantage of the City’s growth economy."""
#              )
#%%
with open(OUTPUT_PATH, 'a') as f:
    f.write('{ "feedback": [ ')

for text in texts:
    #text = "What is the temperature in Baltimore, MD?"
    #text = "From Baltimore, MD we have that Baltimore is in the state of Maryland."
    #text = "39.2896246543727, -76.58026446823449"  # Patterson Park, Baltimore, MD
    #text = "From this, we have 10 - 5 minutes = 5 minutes."
    apis = [location_api]
    generator = DataGenerator(config, model, tokenizer, apis=apis)

    with open(OUTPUT_PATH, 'a') as f:
        augmented_text_ids = generator.generate(text, human=True)
        if len(augmented_text_ids) > 0:
            for single_augmented in augmented_text_ids:
                f.write('{' + f'"text": "{text}", ')
                #assert augmented_text_ids is not None
                #if len(augmented_text_ids[0]) > 0:
                decoded = tokenizer.decode(single_augmented, skip_special_tokens=True)
                f.write(f'"status": "accepted" ')
                #print(f"accepted this one: {decoded}")
                f.write('},')
        else:
            f.write('{' + f'"text": "{text}", ')
            f.write(f'"status": "rejected" ')
            f.write('},')
            #print(f"filtered out text: {text}")
        # remove last comma according to JSON format

# remove last comma according to JSON format
with open(OUTPUT_PATH, 'rb+') as f:
    f.seek(-1, os.SEEK_END)
    f.truncate()
with open(OUTPUT_PATH, 'a') as f:
    f.write('] }')


#else:
#print("no text_ids after filtering!")

# add log to dvc
# repo = Repo(".")
# repo.add(OUTPUT_PATH)
# repo.push()