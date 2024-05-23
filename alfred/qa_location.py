import torch.cuda
from transformers import AutoModelForCausalLM, AutoTokenizer

from toolformer.data_generator import DataGenerator
from toolformer.api import LocationAPI
from toolformer.prompt import qa_prompt
from toolformer.utils import yaml2dict

config = yaml2dict('configs/default.yaml')
# Alfred: needs to look for QA based on the qa_prompt which was given
location_api = LocationAPI(
    "QA", qa_prompt, cities_csv='alfred/uscities.csv',
    sampling_threshold=0.2, filtering_threshold=0.2
)


#%%
#device = ("cuda" if torch.cuda.is_available() else "cpu")
model_name = "hivemind/gpt-j-6B-8bit"   # use EleutherAI/gpt-j-6B for tokenizer
#model_name = "EleutherAI/gpt-j-6B"
# revision = "float16",
# torch_dtype = torch.float16,
#access_token = "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"
model = AutoModelForCausalLM.from_pretrained(model_name) #, token=access_token)
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B") #, token=access_token)
print('finished loading model')


#%%
#text = "What is the temperature in Baltimore, MD?"
text = "From Baltimore, MD we have that Baltimore is in the state of Maryland."
#text = "39.2896246543727, -76.58026446823449"  # Patterson Park, Baltimore, MD
#text = "From this, we have 10 - 5 minutes = 5 minutes."
apis = [location_api]
generator = DataGenerator(config, model, tokenizer, apis=apis)

augmented_text_ids = generator.generate(text)

print(tokenizer.decode(augmented_text_ids[0][0], skip_special_tokens=True))