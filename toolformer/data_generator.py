# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_data_generator.ipynb.

# %% auto 0
__all__ = ['AugmentedCandidate', 'DataGenerator']

# %% ../nbs/04_data_generator.ipynb 4
import re
from typing import List, Callable, Tuple, Union, TypedDict

import torch
from torch import nn
import torch.nn.functional as F

from torchtyping import TensorType
from einops import rearrange

from .api import BaseAPI

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
            while True:
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
                
                # sampling a token
                # next_token = torch.multinomial(probs, num_samples=1)
                next_token = torch.argmax(probs, dim=-1)
                next_token = next_token.unsqueeze(0)
                
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

    def obtain_api_response(
        self,
        prompt_ids: TensorType["seq_len"],
        positions: TensorType["n_positions"],
        generated_ids: TensorType["seq_len"]
    ) -> TensorType["n_positions", "seq_len"]:
        
        MAX_PAD = 50
        
        # the ids before the start of an api call
        pre_api_ids = torch.tensor([]).to(self.device)

        for position in positions:
            #print(generated_ids[:position])
            #print(self.api_start_token_id)
            text_ids = torch.cat([generated_ids[:position], self.api_start_token_id.to(self.device)], dim=0)
            padded_text_ids = F.pad(text_ids, pad=(MAX_PAD - text_ids.shape[-1], 0), value=self.pad_token_id).to(self.device)

            #print(pre_api_ids)
            #print(padded_text_ids)
            pre_api_ids = torch.cat([
                pre_api_ids,
                rearrange(padded_text_ids, "... -> 1 ...")
            ])
        
        PROMPT_LENGTH = len(prompt_ids)
        
        # TODO: optimzie this
        prompt_and_pre_api_ids = torch.tensor([]).to(self.device)
        for x in pre_api_ids:
            prompt_and_pre_api_ids = torch.cat([
                prompt_and_pre_api_ids,
                torch.cat([prompt_ids, x]).unsqueeze(0)
            ], dim=0)
                     
        with torch.no_grad():
            candidate_ids = self.model.generate(
                input_ids=prompt_and_pre_api_ids.long(),
                eos_token_id=self.eos_token_id,
                max_new_tokens=50,
            )
        
        # filter out the prompt template
        # only keep the generated ids
        candidate_ids = candidate_ids[:, PROMPT_LENGTH:]
        
        return candidate_ids
    
    def _generate_conditioning_prompts(
        self,
        api: BaseAPI,
        candidate_ids: TensorType["n_candidates", "seq_len"],
    ):
        conditioning_api_ids = torch.tensor([])

        API_NAME = api.name
        MAX_PAD = 100
        
        def extract_api_request_content(text: str, api_name: str) -> str:
            """Extract the content of an API request from a given text."""
            start_tag = f"{api_name}("
            end_tag = ")"
            start_idx = text.find(start_tag)
            if start_idx == -1:
                return None
            start_idx += len(start_tag)
            end_idx = text.find(end_tag, start_idx)
            if end_idx == -1:
                return None
            return text[start_idx:end_idx]
        
        def extract_api_syntax(text: str, api_name: str) -> str:
            """Extract the API Syntax from a given text."""
            pattern = r"\[{}\(.*?\)\]".format(api_name)
            matches = re.findall(pattern, text)
            return matches

        for text_ids in candidate_ids:
            # the ids of the prediction
            text = self.tokenizer.decode(text_ids, skip_special_tokens=True)
            
            api_request_content = extract_api_request_content(text, api_name=API_NAME)
            api_response = api(api_request_content)
            api_response_ids = self.tokenizer(api_response, return_tensors="pt")["input_ids"][0]
            # Format: "-> [api_response]"
            api_response_with_arrow_ids = torch.cat([self.api_output_token_id, api_response_ids], dim=0)
            
            api_syntax = extract_api_syntax(text, api_name=API_NAME)
            api_syntax_ids = self.tokenizer(api_syntax, return_tensors="pt")["input_ids"][0]
            api_syntax_with_response_ids = torch.cat([api_syntax_ids[:-1], api_response_with_arrow_ids, api_syntax_ids[-1:]])
            api_syntax_without_response_ids = torch.cat([api_syntax_ids[:-1], self.api_output_token_id, api_syntax_ids[-1:]])
                              
            padded_api_without_response = rearrange(
                F.pad(api_syntax_without_response_ids, pad=((MAX_PAD - api_syntax_without_response_ids.shape[-1]), 0), value=self.pad_token_id),
                "... -> 1 ..."
            )
            padded_api_with_response = rearrange(
                F.pad(api_syntax_with_response_ids, pad=((MAX_PAD - api_syntax_with_response_ids.shape[-1]), 0), value=self.pad_token_id),
                "... -> 1 ..."
            )
        
            padded_api_call = torch.cat([
                padded_api_without_response,
                padded_api_with_response
            ], dim=0)
            padded_api_call = rearrange(padded_api_call, "... -> 1 ...")
            
            conditioning_api_ids = torch.cat([conditioning_api_ids, padded_api_call], dim=0).long()
                    
        return conditioning_api_ids

    def _filter_candidate_by_threshold(
        self,
        losses,
        candidates: TensorType["seq_len"]
    ):
        filtered_augmented_text_ids = torch.tensor([]).to(self.device)
        for i, position in enumerate(losses):
            negative_loss = min(losses[position][0], losses[position][1])
            positive_loss = losses[position][2]

            print(f'loss computed is {negative_loss - positive_loss}')
            if negative_loss - positive_loss >= self.filtering_threshold:
                # filtered_augmented_text_ids.append(candidates[i])
                filtered_augmented_text_ids = torch.cat([
                    filtered_augmented_text_ids,
                    candidates[i].unsqueeze(0)
                ], dim=0)
        
        return filtered_augmented_text_ids.long()

    def filter_api( 
        self,
        api: BaseAPI,
        text_ids: TensorType["seq_len"],
        api_start_idxs: TensorType["n_positions"],
        candidate_ids: TensorType["n_positions", "seq_len"]
    ):
        conditioning_api_ids = self._generate_conditioning_prompts(api, candidate_ids)
                
        SPACE_TOKEN = self.tokenizer(". ", return_tensors="pt")["input_ids"][0]
        API_LENGTH = 100
        augmented_text_ids = {"api_start_positions": {}}
        
        def _compute_weight(t: int) -> Union[int, float]:
            """Compute the weight in the loss function."""
            return max(0, 1-0.2*t)
        
        for idx, api_ids in zip(api_start_idxs, conditioning_api_ids):
            idx = idx.item()
            seq_len = len(text_ids)
            augmented_text_ids["api_start_positions"][idx] = {
                "seq_positions": {}
            }

            j = idx
            while j <= seq_len - 1:
                # if the model predic
                if j == 1:
                    j += 1
                    continue
                
                # in the formua, from x_1 to x_j (include x_j)
                # => generate_ids[:j]
                conditioning_text_ids = text_ids[:j]
                api_and_text_ids = torch.stack([
                    F.pad(conditioning_text_ids, pad=(API_LENGTH + len(SPACE_TOKEN), 0), value=self.pad_token_id), # [text_ids]
                    torch.cat([api_ids[0], SPACE_TOKEN, conditioning_text_ids], dim=0), # [api->, text_ids]
                    torch.cat([api_ids[1], SPACE_TOKEN, conditioning_text_ids], dim=0), # [api->result, text_ids]
                ], dim=0)
                                
                # the next token after x_j
                next_token_ids = text_ids[j]
                augmented_text_ids["api_start_positions"][idx]["seq_positions"][j] = {
                    "prompt_ids": api_and_text_ids,
                    "unnormalized_weight": _compute_weight(t=j-idx),
                    "losses": [],
                    "target_ids": torch.tensor([next_token_ids, next_token_ids, next_token_ids])
                }
                j += 1
        
        def _normalize_weights(augmented_text_ids):
            """Normalize the weight of each position in a sequence."""
            for api_start_position in augmented_text_ids["api_start_positions"].values():
                total_weight = sum([seq_position["unnormalized_weight"] for seq_position in api_start_position["seq_positions"].values()])
                for seq_position in api_start_position["seq_positions"].values():
                    seq_position["normalized_weight"] = seq_position["unnormalized_weight"] / total_weight
            
            return augmented_text_ids
        
        augmented_text_ids = _normalize_weights(augmented_text_ids)
                
        def extract_conditioning_ids_and_target_ids(augmented_text_ids):
            conditioning_text_ids = torch.tensor([])
            target_ids = torch.tensor([])
            
            for _, api_start_position_dict in augmented_text_ids["api_start_positions"].items():
                for _, seq_position_dict in api_start_position_dict["seq_positions"].items():
                    # Alfred what are target_ids?
                    target_ids = torch.concat([target_ids, seq_position_dict["target_ids"]], dim=0)
                    for prompt_id in seq_position_dict["prompt_ids"]:
                        conditioning_text_ids = torch.cat([
                            conditioning_text_ids,
                            F.pad(prompt_id.long(), pad=(50-prompt_id.shape[-1], 0), value=self.pad_token_id).unsqueeze(0)
                        ], dim=0)
        
            return conditioning_text_ids.long(), target_ids.long()

        # Alfred what are these?
        conditioning_text_ids, target_ids = extract_conditioning_ids_and_target_ids(augmented_text_ids)

        # Alfred what is this asking of the model?
        output = self.model(input_ids=conditioning_text_ids.long().to(self.device))
        logits = output.logits[:, -1, :]
                    
        def extract_target_logprob_from_logits(logits, target_ids):
            log_probs = F.log_softmax(logits, dim=-1)
            target_log_probs = log_probs[range(target_ids.shape[-1]), target_ids]
            return target_log_probs

        log_probs = extract_target_logprob_from_logits(logits, target_ids)
            
        for _, api_start_position_dict in augmented_text_ids["api_start_positions"].items():
            for _, seq_position_dict in api_start_position_dict["seq_positions"].items():
                # Alfred assigns losses in seq_positions with three rows
                # Alfred for qa_location, last two rows are always the same!!
                seq_position_dict["losses"] = log_probs[:3].squeeze(0)
                log_probs = log_probs[3:]
        
        def _calculate_weighted_loss(augmented_text_ids):
            for position in augmented_text_ids["api_start_positions"]:        
                seq_positions = augmented_text_ids["api_start_positions"][position]["seq_positions"]
                for i in seq_positions:
                    losses = seq_positions[i]["losses"]
                    weights = seq_positions[i]["normalized_weight"]
                    # Alfred adds weighted_losses, losses is a Tensor having three rows
                    seq_positions[i]["weighted_losses"] = -losses * weights
            
            return augmented_text_ids
        
        augmented_text_ids = _calculate_weighted_loss(augmented_text_ids)
        
        def _calculate_loss(augmented_text_ids):
            data = {}
            for position in augmented_text_ids["api_start_positions"]:        
                seq_positions = augmented_text_ids["api_start_positions"][position]["seq_positions"]
                losses = [0, 0, 0]            
                for i in seq_positions:
                    losses[0] += seq_positions[i]["weighted_losses"][0] # loss for [text]
                    losses[1] += seq_positions[i]["weighted_losses"][1] # loss for [api->, text]
                    losses[2] += seq_positions[i]["weighted_losses"][2] # loss for [api-result, text]
                data[position] = losses
                
            return data
        
        losses = _calculate_loss(augmented_text_ids)
        filtered_candidate_ids = self._filter_candidate_by_threshold(losses, candidate_ids)
        return filtered_candidate_ids
    
    def generate(
        self,
        text: str,
    ) -> TensorType["n_apis", "n_candidates", "seq_len"]:
        filtered_apis = torch.tensor([]).to(self.device)
        
        for api in self.apis:
            # TODO: add support batch
            prompt = api.prompt_template.format(input=text)
            prompt_ids = self.tokenizer(prompt, return_tensors="pt")["input_ids"][0]
            prompt_ids = prompt_ids.to(self.device)
        
            # sampling positions
            api_start_idxs, generated_ids = self.sample_api_position(prompt_ids)
    
            # obtaining api responses
            #print(prompt_ids)
            #print(api_start_idxs)
            #print(generated_ids)
            candidate_ids = self.obtain_api_response(prompt_ids, api_start_idxs, generated_ids)

            # filtering
            text_ids = self.tokenizer(text, return_tensors="pt")["input_ids"][0]
            
            # return prompt_ids, api_start_idxs, generated_ids, candidate_ids, text_ids
            filtered_candidate_ids = self.filter_api(api, text_ids, api_start_idxs, candidate_ids)
                    
            filtered_apis = torch.cat([filtered_apis, filtered_candidate_ids.unsqueeze(0)], dim=0)
        
        return filtered_apis.long()
