import pytest

from toolformer.utils import extract_api_content, extract_api_name, yaml2dict

from dotenv import load_dotenv
import openai
import os

def test_extract_api_content():
    text = "From this, we have 10 - 5 minutes = [Calculator(10 - 5)] 5 minutes."
    # text = "From this, we have 10 - 5 minutes = [Calculator((2+3) - 1)] 5 minutes." # TODO: add test case for this
    target = "10 - 5"

    output = extract_api_content(text, api_name="Calculator")

    assert isinstance(output, str)
    assert output == target

@pytest.mark.parametrize(
    "text, is_end_token, target",
    [
        ("From this, we have 10 - 5 minutes = [Calculator(10 - 5)] 5 minutes.", True, "Calculator"),
        ("[Calculator(10 - 5)", False, "Calculator"),
    ],
)
def test_extract_api_name(text, is_end_token, target):
    output = extract_api_name(text, is_end_token=is_end_token)

    assert isinstance(output, str)
    assert output == target

def test_ask_gpt():
    content = "This is a test prompt that will be echoed."
    messages = [{
        "role": "system",
        "content": "Echo the text prompt from the user exactly and word for word."
    }, {
        "role": "user",
        "content": f"{content}"  # \n Baseline1: {original_text}\n Baseline2: {baseline}"
    }]

    load_dotenv()
    openai_client = openai.Client(
        api_key=os.environ.get("OPENAI_API_KEY")
    )

    config = yaml2dict('./configs/default.yaml')

    chat_completion = openai_client.chat.completions.create(messages=messages, model=config["gpt"]["model"])
    assert chat_completion.choices[0].message.content == content #chat_completion["message"]["content"]