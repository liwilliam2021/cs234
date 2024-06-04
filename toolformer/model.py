# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_model.ipynb.

# %% auto 0
__all__ = ['ToolFormer']

# %% ../nbs/05_model.ipynb 4
from typing import Optional, List

import torch
from torch import nn
import torch.nn.functional as F

from transformers import AutoModelForCausalLM, AutoTokenizer
from torchtyping import TensorType
from einops import rearrange

from .api import BaseAPI
from .utils import extract_api_content, extract_api_name

# %% ../nbs/05_model.ipynb 5
class ToolFormer(nn.Module):
    def __init__(
        self,
        model: AutoModelForCausalLM,
        apis: List[BaseAPI],
        config: dict,
        device: str
    ):
        super().__init__()
        self.model = model
        self.apis = apis
        self.config = config
        self.is_calling_api: bool = False
        
        # TODO: make a config class contains token_id
        tokenizer = AutoTokenizer.from_pretrained(self.config["tokenizer"]["path"])
        self.tokenizer = tokenizer # TODO: remove after debug
        
        start_character = config["data_generator"]["api_start_character"]
        end_character = config["data_generator"]["api_end_character"]
        output_character = config["data_generator"]["api_output_character"]
        
        self.api_start_token_id = tokenizer(f' {start_character}', return_tensors="pt")["input_ids"][0].to(device)
        self.api_end_token_id = tokenizer(end_character, return_tensors="pt")["input_ids"][0].to(device)
        self.api_output_token_id = tokenizer(f'{output_character}', return_tensors="pt")["input_ids"][0].to(device)

        self.eos_token_ids = tokenizer(
            [".", ".\n\n"],
            return_tensors="pt"
        )["input_ids"].squeeze().to(device)

        # TODO: support batch
        self.api_request_content: torch.Tensor = torch.tensor([]).to(device)
        self.device = device
    
    def _sampling(self, probs: TensorType["batch_size", "seq_len"]) -> TensorType["batch_size", "seq_len"]:
        return torch.argmax(probs, dim=-1)
    
    def execute_api(self, text_ids: TensorType["seq_len"]) -> Optional[TensorType["seq_len"]]:
        """Execute an API call."""
        text = self.tokenizer.decode(text_ids, skip_special_tokens=True)
        api_name = extract_api_name(text, is_end_token=False)

        if api_name is not None:
            # find does apis contains the api_name
            for api in self.apis:
                if api.name == api_name:
                    api_content = extract_api_content(text, api_name=api_name)
                    api_output = api(api_content)
                    return self.tokenizer(api_output, return_tensors="pt")["input_ids"][0]
        return None
    
    def add_idx_to_api_request_content(self, idx: TensorType[1]):
        self.api_request_content = torch.cat([
            self.api_request_content,
            rearrange(idx, '... -> 1 ...')
        ], dim=-1).long()
    
    def forward(
        self,
        input_ids: TensorType["batch_size", "seq_len"],
        attention_mask: Optional[TensorType["batch_size", "seq_len"]]=None,
        max_new_tokens: int = 10,
        **kwargs
    ) -> TensorType["batch_size", "seq_len"]:
        # check padding to the left
        generated_ids = input_ids.to(self.device)
        
        for _ in range(max_new_tokens):
            output_ids = self.model(
                input_ids=generated_ids,
                attention_mask=attention_mask.to(self.device),
                **kwargs
            )
            
            logits = output_ids.logits[:, -1, :]
            probs = F.softmax(logits, dim=-1)
            # TODO: k should be a config
            _, top_k_idx = torch.topk(probs, k=1, dim=-1)
            
            if self.is_calling_api is True:
                if self.api_end_token_id in top_k_idx:
                    # if the api end token is in the top_k_idx, then we will execute the api
                    # and then add api_end_token_id to the generated_ids
                    # TODO: add support batch
                    api_output_ids = self.execute_api(self.api_request_content[0]).to(self.device)
                    if api_output_ids is not None:
                        pred_ids = torch.cat([
                            self.api_output_token_id,
                            api_output_ids,
                            self.api_end_token_id
                        ], dim=-1).long()
                    else:
                        pred_ids = self.api_end_token_id
                    self.is_calling_api = False
                else:
                    pred_ids = self._sampling(probs)
                    self.add_idx_to_api_request_content(pred_ids)
            else:
                if self.api_start_token_id in top_k_idx:
                    # if the api start token is in the top_k_idx, then we are calling an api
                    self.is_calling_api = True
                    pred_ids = self.api_start_token_id
                    self.add_idx_to_api_request_content(pred_ids)
                else:
                    pred_ids = self._sampling(probs)

            generated_ids = torch.cat([
                generated_ids,
                rearrange(pred_ids, '... -> 1 ...')
            ], dim=1)
            
            attention_mask = torch.cat([
                attention_mask.to(self.device),
                rearrange(torch.ones_like(pred_ids), '... -> 1 ...')
            ], dim=1)
            
            # ignore the case that pred_ids contains api_output
            if len(pred_ids) == 1 and pred_ids in self.eos_token_ids:
                break
        
        return generated_ids
