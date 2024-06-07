import pytest
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain import PromptTemplate

from toolformer.data_generator import DataGenerator
from toolformer.utils import yaml2dict
from toolformer.prompt import calculator_prompt

device = ("cuda" if torch.cuda.is_available() else "cpu")

@pytest.fixture
def default_config():
    return yaml2dict('./configs/default.yaml')

@pytest.fixture
def model(default_config):
    match default_config['model']['torch_dtype']:
        case 'float16':
            torch_dtype = torch.float16
        case 'float32':
            torch_dtype = torch.float32
        case 'float64':
            torch_dtype = torch.float64
        case 'auto':
            torch_dtype = "auto"
        case _:
            raise ValueError("torch_dtype has invalid value")
    return AutoModelForCausalLM.from_pretrained(default_config['model']['path'], torch_dtype=torch_dtype).to(device)

@pytest.fixture
def tokenizer(default_config):
    return AutoTokenizer.from_pretrained(default_config['tokenizer']['path'])

@pytest.fixture
def prompt_tempalte():
    return PromptTemplate(template=calculator_prompt, input_variables=["input"])

@pytest.fixture
def data_generator(default_config, model, tokenizer):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return DataGenerator(default_config, model, tokenizer, apis=[]).to(device)