import torch.cuda
from transformers import AutoModelForCausalLM, AutoTokenizer

from toolformer.data_generator import DataGenerator
from toolformer.api import LocationAPI
from toolformer.prompt import location_prompt
from toolformer.utils import yaml2dict

config = yaml2dict('configs/default.yaml')
# Alfred: needs to look for QA based on the qa_prompt which was given
location_api = LocationAPI(
    "Location", location_prompt, cities_csv='alfred/uscities.csv',
    sampling_threshold=0.2, filtering_threshold=0.2
)


#%%
#device = ("cuda" if torch.cuda.is_available() else "cpu")
#model_name = "hivemind/gpt-j-6B-8bit"   # use EleutherAI/gpt-j-6B for tokenizer
model_name = "bigscience/bloom-560m"
#model_name = "EleutherAI/gpt-j-6B"
#revision = "float16"
torch_dtype = torch.float16
#access_token = "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"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch_dtype) #, torch_dtype=torch_dtype) #, token=access_token)
tokenizer = AutoTokenizer.from_pretrained(model_name) #"EleutherAI/gpt-j-6B") #, token=access_token)
print('finished loading model')


texts= []
texts.append("The landowners in Baltimore want to appeal to the state of Maryland for help.")

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
for text in texts:
    #text = "What is the temperature in Baltimore, MD?"
    #text = "From Baltimore, MD we have that Baltimore is in the state of Maryland."
    #text = "39.2896246543727, -76.58026446823449"  # Patterson Park, Baltimore, MD
    #text = "From this, we have 10 - 5 minutes = 5 minutes."
    apis = [location_api]
    generator = DataGenerator(config, model, tokenizer, apis=apis)

    augmented_text_ids = generator.generate(text)

    print(tokenizer.decode(augmented_text_ids[0][0], skip_special_tokens=True))
