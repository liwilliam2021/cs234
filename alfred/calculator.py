from transformers import AutoModelForCausalLM, AutoTokenizer

from toolformer.data_generator import DataGenerator
from toolformer.api import CalculatorAPI
from toolformer.prompt import calculator_prompt
from toolformer.utils import yaml2dict

config = yaml2dict('configs/default.yaml')
calculator_api = CalculatorAPI(
    "Calculator", calculator_prompt,
    sampling_threshold=0.2, filtering_threshold=0.2
)

model = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m,torch_dtype=None")
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m,torch_dtype=None")

text = "From this, we have 10 - 5 minutes = 5 minutes."
apis = [calculator_api]
generator = DataGenerator(config, model, tokenizer, apis=apis)

augmented_text_ids = generator.generate(text)

print(tokenizer.decode(augmented_text_ids[0][0], skip_special_tokens=True))