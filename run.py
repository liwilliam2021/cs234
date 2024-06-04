from toolformer.utils import ask_gpt
from toolformer.prompt import weather_prompt
from toolformer.api import WeatherAPI
from toolformer.gpt import get_input_generator_prompt
from toolformer.utils import ask_gpt, yaml2dict
from toolformer.data_generator import DataGenerator
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "bigscience/bloom-1b1"
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

config = yaml2dict('./configs/default.yaml')
weather_api = WeatherAPI(
    "Weather", weather_prompt, api_key = os.environ.get("WEATHER_API_KEY"),
    sampling_threshold=0.2, filtering_threshold=0.2
)

apis = [weather_api]
generator = DataGenerator(config, model, tokenizer, apis=apis)

import csv
import os
filename = f"generated_data/{' '.join([api.name for api in apis])}.csv"
os.makedirs(os.path.dirname(filename), exist_ok=True)

total_samples = 0
positive_samples = 0
last_milestone = total_samples - (total_samples % 50)

while positive_samples < 1000:
    if total_samples > last_milestone + 50 == 0:
        print(f"Total Samples: {total_samples}, Positive Samples: {positive_samples}")
        last_milestone += 50
    example_prompts = weather_prompt[weather_prompt.find ("Input:"):]

    prompts = [{
        "role": "system",
        "content": """You will many examples of Input, Output pairs that will be given for incontext learning to another model. 
        Generate more examples of inputs. Do not generate any outputs. Do not include the labels Input and Output.
        Respond with only the examples separated by new lines."""
      }, {
        "role": "user",
        "content": example_prompts
    }]

    response = ask_gpt(prompts)
    texts = response.split("\n")

    for text in texts:
      if len(text) < 2:
        continue
      try:
        augmented_text_ids = generator.generate(text)
        total_samples += max (1, len (augmented_text_ids))
      except Exception as e:
        print(e)
        continue
      with open(filename, "a") as f:
          writer = csv.writer(f)
          # Write header if file is new
          if f.tell() == 0:
              writer.writerow(["input","text","candidate"])
          for augmented_text in augmented_text_ids:
              positive_samples += 1
              decoded_text = tokenizer.decode(augmented_text, skip_special_tokens=True)
              input_generator_prompt = get_input_generator_prompt (decoded_text)
              res = ask_gpt (input_generator_prompt)
              
              writer.writerow([res, text, decoded_text])