from transformers import AutoModelForCausalLM, AutoTokenizer

from toolformer.data_generator import DataGenerator
from toolformer.api import SearchAPI
from toolformer.prompt import qa_prompt
from toolformer.utils import yaml2dict

config = yaml2dict('../configs/default.yaml')
search_api = SearchAPI(
    "Search", qa_prompt,
    sampling_threshold=0.2, filtering_threshold=0.2
)

model = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m,torch_dtype=None")
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m,torch_dtype=None")

text = "39.2896246543727, -76.58026446823449"  # Patterson Park, Baltimore, MD
#text = "From this, we have 10 - 5 minutes = 5 minutes."
apis = [search_api]
generator = DataGenerator(config, model, tokenizer, apis=apis)

augumented_text_ids = generator.generate(text)

print(tokenizer.decode(augumented_text_ids[0][0], skip_special_tokens=True))