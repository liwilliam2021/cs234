from toolformer.utils import ask_gpt
from toolformer.prompt import weather_prompt, location_prompt, temperature_prompt
from toolformer.api import WeatherAPI, LocationAPI, TemperatureAPI
from toolformer.gpt import get_input_generator_prompt
from toolformer.utils import ask_gpt, yaml2dict
from toolformer.data_generator import DataGenerator
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

import traceback
import logging
from datetime import datetime

config = yaml2dict('./configs/default.yaml')
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
    level=logging.WARN,
    format="%(asctime)s [%(levelname)s] [%(module)s %(funcName)s %(lineno)d] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)

model = AutoModelForCausalLM.from_pretrained(config["model"]["path"], trust_remote_code=True, torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(config["model"]["path"], trust_remote_code=True)

weather_api = WeatherAPI(
    "Weather", weather_prompt, api_key=os.environ.get("WEATHER_API_KEY"),
    sampling_threshold=0.2, filtering_threshold=0.2
)
location_api = LocationAPI(
    "Location", location_prompt, cities_csv='alfred/uscities.csv',
    sampling_threshold=0.2, filtering_threshold=0.2
)

import csv
import os

apis_prompts = []
apis_prompts.append([weather_api, weather_prompt])
#apis_prompts.append([location_api, location_prompt])
for api_prompt in apis_prompts:

    generator = DataGenerator(config, model, tokenizer, apis=[api_prompt[0]])

    filename = f"generated_data/{api_prompt[0].name}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    total_samples = 0
    positive_samples = 0
    negative_samples = 0
    last_milestone = total_samples - (total_samples % 50)

    while positive_samples < 1000:
        if total_samples > last_milestone + 50 == 0:
            print(f"Total Samples: {total_samples}, Positive Samples: {positive_samples}")
            last_milestone += 50
        prompt_text = api_prompt[1]
        example_prompts = prompt_text[prompt_text.find ("Input:"):]

        prompts = [{
            "role": "system",
            "content": """You will receive many examples of Input, Output pairs that will be given for incontext learning to another model. 
            Generate more examples of inputs. Do not generate any outputs. Do not include the labels Input and Output.
            Respond with only the examples separated by new lines."""
          }, {
            "role": "user",
            "content": example_prompts
        }]

        response = ask_gpt(prompts)
        texts = response.split("\n")

        print(f"Auto-generated {len(texts)} texts and will now ask you to evaluate them.")
        for text in texts:
          if len(text) < 2:
            continue
          try:
            augmented_text_ids = generator.generate(text)
            total_samples += max (1, len(augmented_text_ids))
          except Exception as e:
            #print(e.__traceback__)
            print(f"skipping text {text} on encountering an error")
            traceback.print_exc()
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
                  res = ask_gpt(input_generator_prompt)

                  writer.writerow([res, text, decoded_text])

