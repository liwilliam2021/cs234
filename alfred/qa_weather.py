import torch.cuda
from transformers import AutoModelForCausalLM, AutoTokenizer

from toolformer.data_generator import DataGenerator
from toolformer.api import WeatherAPI
from toolformer.prompt import qa_prompt
from toolformer.utils import yaml2dict

config = yaml2dict('../configs/default.yaml')
weather_api = WeatherAPI(
    "Weather", qa_prompt,
    sampling_threshold=0.2, filtering_threshold=0.2
)

#device = ("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m")
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m")

text = "What is the temperature in Baltimore, MD?"
#text = "39.2896246543727, -76.58026446823449"  # Patterson Park, Baltimore, MD
#text = "From this, we have 10 - 5 minutes = 5 minutes."
apis = [weather_api]
generator = DataGenerator(config, model, tokenizer, apis=apis)

augmented_text_ids = generator.generate(text)

print(tokenizer.decode(augmented_text_ids[0][0], skip_special_tokens=True))