# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_data_generator.ipynb.

# %% auto 0
__all__ = ['AugmentedCandidate', 'DataGenerator']

# %% ../nbs/04_data_generator.ipynb 4
import re
from typing import List, Callable, Tuple, Union, TypedDict
from transformers import StoppingCriteria, StoppingCriteriaList

import torch
from torch import nn
import torch.nn.functional as F

from torchtyping import TensorType
from einops import rearrange
from transformers.utils import torch_only_method

from .api import BaseAPI
from .utils import ask_gpt
from .gpt import *

MAX_SEQ_LENGTH = 50

# %% ../nbs/04_data_generator.ipynb 5
class AugmentedCandidate(TypedDict):
    api_start_positions: int

# %% ../nbs/04_data_generator.ipynb 6
class DataGenerator(nn.Module):
    def __init__(
        self,
        config: dict,
        model: Callable, tokenizer: Callable,
        apis: List[BaseAPI],
        device: str = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ):
        super().__init__()
        start_character = config["data_generator"]["api_start_character"]
        end_character = config["data_generator"]["api_end_character"]
        output_character = config["data_generator"]["api_output_character"]
        
        # add a space, because when the model generate a token, it's also include a "space"
        self.api_start_token_id = tokenizer(f' {start_character}', return_tensors="pt")["input_ids"][0]
        self.api_end_token_id = tokenizer(end_character, return_tensors="pt")["input_ids"][0]
        self.api_output_token_id = tokenizer(f'{output_character}', return_tensors="pt")["input_ids"][0]
        
        self.top_k_sampling = config["data_generator"]["top_k_sampling"]
        self.sampling_threshold = config["data_generator"]["sampling_threshold"]
        self.filtering_threshold = config["data_generator"]["filtering_threshold"]
        
        self.apis = apis
        self.model = model.to(device)
        self.tokenizer = tokenizer
        self.device = device
        
        # TODO: handle for cases that the sentence contains ".\n\n"
        self.pad_token_id = tokenizer.pad_token_id
        self.eos_token_id = tokenizer(".\n\n")["input_ids"][0]
    
    def sample_api_position(
        self,
        prompt_ids: TensorType["seq_len"], # the ids of the prompt
    ) -> Tuple[
        TensorType["n_positions"], # The positions of api call
        TensorType["seq_len"] # The generated text
    ]:
        """Sampling API positions."""
        # TODO: add support batch
        # the ids of the prompt and generated_ids
        prompt_and_generated_ids = prompt_ids.to(self.device)
        # only the ids of the generated_ids
        generated_ids = torch.tensor([]).to(self.device)
        i = torch.tensor([0]).to(self.device)
        
        api_pos_probs = torch.tensor([]).to(self.device)
        
        with torch.no_grad():    
            while i < MAX_SEQ_LENGTH:
                logits = self.model(
input_ids=prompt_and_generated_ids.unsqueeze(0)).logits

                # Alfred returns the last row of second dimension, and all the columns of third dimension
                last_logit = logits[0, -1, :]
                probs = torch.softmax(last_logit, dim=-1)
                api_start_prob = probs[self.api_start_token_id].to(self.device)
                
                # Alfred: returns tensor stack of index having api_start_prob greater than threshold
                if api_start_prob > self.sampling_threshold:
                    api_pos_probs = torch.cat([
                        api_pos_probs,
                        torch.tensor([api_start_prob, i]).unsqueeze(0).to(self.device)
                    ], dim=0)
                # print (self.sampling_threshold, api_start_prob, probs[self.eos_token_id])  
                
                # sampling a token
                # next_token = torch.multinomial(probs, num_samples=1)
                next_token = torch.argmax(probs, dim=-1)
                next_token = next_token.unsqueeze(0)

                if i == MAX_SEQ_LENGTH - 1: 
                    # Prevent infinite generation
                    next_token = torch.tensor([self.eos_token_id]).to(self.device)
                
                prompt_and_generated_ids = torch.cat([prompt_and_generated_ids, next_token], dim=0)
                generated_ids = torch.cat([generated_ids, next_token], dim=0).to(self.device)
                
                if next_token == self.eos_token_id:
                    break
                else:
                    i += 1
        
        if api_pos_probs.numel() == 0:
            api_positions = torch.tensor([]).to(self.device)
        else:
            _, indices = torch.sort(api_pos_probs[:, 0], descending=True)
            top_k_sampling = self.top_k_sampling
            api_positions = api_pos_probs[indices[:top_k_sampling], 1]
        return api_positions.long(), generated_ids.long()
    
    def generate_api_candidates_and_baselines (
        self, 
        api_positions,
        generated_ids,
        prompt_ids,
        api: BaseAPI,
        task_prompt = None,
        do_DAgger = False,
    ):
        API_NAME = api.name

        def remove_surrounding_quotes(s):
            if s.startswith('"') and s.endswith('"'):
                return s[1:-1]
            elif s.startswith("'") and s.endswith("'"):
                return s[1:-1]
            return s
        
        def extract_api_request_content(text: str, api_name: str) -> str:
            """Extract the content of an API request from a given text."""
            start_tag = f"{api_name}API("
            end_tag = ")"
            start_idx = text.find(start_tag)
            if start_idx == -1:
                return None
            start_idx += len(start_tag)
            end_idx = text.find(end_tag, start_idx)
            if end_idx == -1:
                return None
            return remove_surrounding_quotes(text[start_idx:end_idx])
        
        def extract_api_syntax(text: str, api_name: str) -> str:
            """Extract the API Syntax from a given text."""
            pattern = r"\[{}\(.*?\)\]".format(api_name)
            matches = re.findall(pattern, text)
            return remove_surrounding_quotes(matches)

        candidates = []
        baselines = []
        for api_idx in api_positions:
            modified_generation_ids = generated_ids[: api_idx]
            modified_generation_ids = torch.cat([modified_generation_ids, torch.tensor([self.api_start_token_id]).to(self.device)], dim=0)  
            api_tokens = self.tokenizer(api.name, return_tensors="pt")["input_ids"][0].to(self.device)
            modified_generation_ids = torch.cat([modified_generation_ids, api_tokens], dim=0)  

            prompt_and_generated_ids = torch.cat([prompt_ids.to(self.device), modified_generation_ids], dim=0)

            # A little hacky
            stop_words_to_prevent_long_gen = [
                self.tokenizer(word, return_tensors='pt')['input_ids'].squeeze()
                for word in ["\n" , ".\n", ".\n\n"]
            ]
            class PreventLongGen (StoppingCriteria):
                def __init__(self):
                    super().__init__()
                def __call__(self, input_ids: torch.LongTensor, score: torch.FloatTensor, **kwargs) -> bool:
                    # print (torch.max(score[-1]))
                    # print (thing.decode(input_ids[0][-1]), input_ids[0][-1])
                    return input_ids[0][-1] in stop_words_to_prevent_long_gen

            baseline_ids = self.model.generate(
                  torch.Tensor(prompt_and_generated_ids).unsqueeze(0).to(self.device),
                  max_new_tokens=MAX_SEQ_LENGTH - api_idx,
                  repetition_penalty=1.2,
                  temperature = 0,
                  stopping_criteria= StoppingCriteriaList([PreventLongGen()]),
                  return_dict_in_generate=True, output_scores=True
            )[0].squeeze()[len(prompt_ids): ]
            baselines.append (baseline_ids)

            i = api_idx + 1 + len (api_tokens)
            with torch.no_grad():    
                while i < MAX_SEQ_LENGTH:
                    logits = self.model(input_ids=prompt_and_generated_ids.unsqueeze(0)).logits
                    last_logit = logits[0, -1, :]
                    probs = torch.softmax(last_logit, dim=-1)

                    next_token = torch.argmax(probs, dim=-1)
                    next_token = next_token.unsqueeze(0)

                    if i == MAX_SEQ_LENGTH - 1: 
                        # Prevent infinite generation
                        next_token = torch.tensor([self.eos_token_id]).to(self.device)
                    
                    if next_token == torch.tensor([self.api_end_token_id]).to(self.device):

                        text = self.tokenizer.decode(modified_generation_ids[api_idx:])
                        api_request_content = extract_api_request_content(text, api_name=API_NAME)
                        api_response = api(api_request_content)
                        api_response_ids = self.tokenizer(api_response, return_tensors="pt")["input_ids"][0].to(self.device)
                        modified_generation_ids = torch.cat(
                          [modified_generation_ids, torch.tensor([self.api_end_token_id]).to(self.device),
                          torch.tensor([self.api_output_token_id]).to(self.device),
                          api_response_ids], dim=0)
                        
                        if (do_DAgger and "Exception" in api_response):
                            print (self.tokenizer.decode(modified_generation_ids))
                            expert_suggestion = input ("Please provide a suggestion for the API response\n")
                            expert_suggestion_ids = self.tokenizer(expert_suggestion, return_tensors="pt")["input_ids"][0].to(self.device)
                            candidates.append (expert_suggestion_ids)
                            break

                        # A little messy here
                        if task_prompt:
                            new_prompt_ids = self.tokenizer(task_prompt, return_tensors="pt")["input_ids"][0].to(self.device)
                        else:
                            new_prompt_ids = torch.tensor([]).to(self.device)

                        final_ids = torch.cat (
                            [new_prompt_ids, modified_generation_ids]
                        ).unsqueeze(0).to(self.device)
                        max_new_tokens = (len (baseline_ids) - len(final_ids)) * 1.1
                        # Done in one step to resolve weird reptition problem
                        full_output_ids = self.model.generate(
                              final_ids.long(),
                              max_new_tokens= max_new_tokens,
                              repetition_penalty=1.2,
                              temperature = 0,
                              stopping_criteria= StoppingCriteriaList([PreventLongGen()]),
                              return_dict_in_generate=True, output_scores=True
                        )[0].squeeze()
                        
                        # Remove the prompt
                        candidate_ids = full_output_ids[len(new_prompt_ids): ]
                        # Truncate overgeneration
                        end_indices = [
                            self.tokenizer(word, return_tensors='pt')['input_ids'].squeeze()
                            for word in [".", "\n" , ".\n", ".\n\n"]
                        ]
                        mask = torch.zeros_like(candidate_ids, dtype=torch.bool)
                        for end_index in end_indices:
                            mask = mask | (candidate_ids == end_index)
                        if len (mask.nonzero(as_tuple=True)):
                            last_end_index = mask.nonzero(as_tuple=True)[0][-1].item()

                            # Truncate the tensor after the last "." character
                            candidate_ids = candidate_ids[:last_end_index + 1]

                        candidates.append (candidate_ids)
                        break
                    else:
                        prompt_and_generated_ids = torch.cat([prompt_and_generated_ids, next_token], dim=0)
                        modified_generation_ids = torch.cat([modified_generation_ids, next_token], dim=0)
                        if next_token == self.eos_token_id:
                            candidates.append (modified_generation_ids)
                            break
                        i += 1
            
        return candidates, baselines
    
    def should_not_filter_api_candidate (self, original_text, api_candidate_ids, baseline_ids, human = False):
        api_candidate = self.tokenizer.decode (api_candidate_ids)
        
        baseline = self.tokenizer.decode (baseline_ids)
        return_val = None
        if human: # Do human eval
            print ("Candidate:", api_candidate)
            print ("Baseline1:", original_text)
            print ("Baseline2:", baseline)
            while True:
                res = input ("Respond with True if the Candidate is better than the Baselines, and False otherwise\n")
                if res == "True": 
                  return_val = True
                  break
                elif res == "False": 
                  return_val = False
                  break
                else: print ("Please only respond True or False")
        if len (self.apis) == 1 and "Weather" == self.apis[0].name:
            messages = get_weather_eval_prompt (original_text, api_candidate)
            res = ask_gpt (messages)
            if "True" in res: 
              return_val2 = True
            else:
              return_val2 = False

            if return_val == None: 
              return_val = return_val2
            elif return_val != return_val2:
              print (res)
              
        else:
            messages = [{
                "role": "system",
                "content": "You will recieve a candidate text and baseline texts. Respond with True if the Candidate is a better text generation than the Baselines, and False otherwise. If the candidate is more accurate than the baselines it is better. Do not respond with anything else."
            }, {
                "role": "user",
                "content": f"Candidate:{api_candidate}\n Baseline1: {original_text}\n Baseline2: {baseline}"
            }]
            res = ask_gpt (messages)
            if res == "True": return True
            else: return False
        
        return return_val


    def generate(
        self,
        text: str,
        task_prompt=None,
        human=False
    ) -> TensorType["n_apis", "n_candidates", "seq_len"]:
        filtered_apis = torch.tensor([]).to(self.device)
        
        for api in self.apis:
            # TODO: add support batch
            prompt = api.prompt_template.format(input=text)

            prompt_ids = self.tokenizer(prompt, return_tensors="pt")["input_ids"][0]

            # sampling positions
            api_start_idxs, generated_ids = self.sample_api_position(prompt_ids)

            # A little messy right now
            candidates, baselines = self.generate_api_candidates_and_baselines (
              api_start_idxs, generated_ids, prompt_ids, api, task_prompt=task_prompt
            )

            filtered_candidates_ids = []
            for api_candidate_ids, baseline_ids in zip(candidates, baselines):
                if self.should_not_filter_api_candidate (
                    text,
                    api_candidate_ids,
                    baseline_ids,
                    human = human
                ): filtered_candidates_ids.append (api_candidate_ids)
        
        return filtered_candidates_ids 