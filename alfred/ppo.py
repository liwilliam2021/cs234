#%%
import os

import torch
from transformers import AutoTokenizer
from trl import AutoModelForCausalLMWithValueHead, PPOTrainer, PPOConfig
from datasets import load_dataset, Dataset
import json
from tqdm import tqdm

from dvc.repo import Repo
import csv

import yaml
from pathlib import Path
#%%
TOP_LEVEL = '/mnt/pycharmprojects/cs234_final'
#printf "$(git rev-parse --show-toplevel)"
#%%
# set working directory to root of git repo
config = yaml.safe_load(Path(TOP_LEVEL + '/configs/default.yaml').read_text())
#%%
# load model and dataset - dataset needs to be in a specific format
model = AutoModelForCausalLMWithValueHead.from_pretrained(config["model"]["path"])
ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(config["model"]["path"])
tokenizer = AutoTokenizer.from_pretrained(config["model"]["path"])
tokenizer.pad_token = tokenizer.eos_token
#%%
# load data

with open(TOP_LEVEL+'/generated_data/Weather.csv', mode='r') as f:
    data_reader = csv.DictReader(f)
    # with open('coors_new.csv', mode='w') as outfile:
    #     writer = csv.writer(outfile)
    #     mydict = {rows[0]:rows[1] for rows in reader}
    ppo_dataset_dict = {}
    ppo_dataset_dict["query"] = []
    ppo_dataset_dict["chosen"] = []
    ppo_dataset_dict["rejected"] = []
    for row in data_reader:
        ppo_dataset_dict["prompt"].append(row["input"])
        ppo_dataset_dict["chosen"].append(row["text"])
        ppo_dataset_dict["rejected"].append(row["candidate"])

#%%
# get dataset
#train_dataset = load_dataset("imdb", split="train")
# ppo_dataset_dict = {
#     "query": [
#         "Explain the moon landing to a 6 year old in a few sentences.",
#         "Why aren’t birds real?",
#         "What happens if you fire a cannonball directly at a pumpkin at high speeds?",
#         "How can I steal from a grocery store without getting caught?",
#         "Why is it important to eat socks after meditating? "
#     ]
# }
dataset = Dataset.from_dict(ppo_dataset_dict)
#print(train_dataset["prompt"][0])
#%%
# load trainer
NUM_TRAIN_EPOCHS = 1000
OUTPUT_DIR = TOP_LEVEL + f"/alfred/output/{config['model']['path']},torch_dtype={config['model']['torch_dtype']}/epoch={NUM_TRAIN_EPOCHS}"
#os.makedirs(os.path.dirname(OUTPUT_DIR), exist_ok=True)
os.makedirs(OUTPUT_DIR)
#%%
config = PPOConfig(
    model_name=config["model"]["path"],
    learning_rate=1.41e-5,
    #log_with="wandb",
)

def collator(data):
    return dict((key, [d[key] for d in data]) for key in data[0])

ppo_trainer = PPOTrainer(config, 
                         model, 
                         ref_model, 
                         tokenizer, 
                         dataset=dataset, 
                         data_collator=collator)
#%% md
# # Reward model
#%%
# bradley-terry reward model
def bradley_terry(obs: torch.Tensor,
                actions_w: torch.Tensor,
                actions_l: torch.Tensor,
                ref_policy: nn.Module, 
                max_iters=1000, 
                error_tol=1e-3):
    ''' 
    Computes Bradley-Terry similar to pset3
    '''
    dist_ref = ref_policy.distribution(obs)
    log_probs_ref_w = dist_ref.log_prob(actions_w)
    log_probs_ref_l = dist_ref.log_prob(actions_l)

    dist_theta = self.distribution(obs)
    log_probs_theta_w = dist_theta.log_prob(actions_w)
    log_probs_theta_l = dist_theta.log_prob(actions_l)

    #loss = -torch.mean(torch.logsigmoid(self.beta * (log_probs_w - self.beta * log_probs_l, dim=0))
    return -torch.mean(F.logsigmoid(self.beta * (log_probs_theta_w - log_probs_ref_w) - self.beta * (log_probs_theta_l - log_probs_ref_l)), dim=0)
#%%
import 

# train
output_min_length = 4
output_max_length = 16
output_length_sampler = LengthSampler(output_min_length, output_max_length)


generation_kwargs = {
    "min_length": -1,
    "top_k": 0.0,
    "top_p": 1.0,
    "do_sample": True,
    "pad_token_id": tokenizer.eos_token_id,
}


for epoch, batch in tqdm(enumerate(ppo_trainer.dataloader)):
    query_tensors = batch["input_ids"]

    #### Get response from gpt2
    response_tensors = []
    for query in query_tensors:
        gen_len = output_length_sampler()
        generation_kwargs["max_new_tokens"] = gen_len
        response = ppo_trainer.generate(query, **generation_kwargs)
        response_tensors.append(response.squeeze()[-gen_len:])
    batch["response"] = [tokenizer.decode(r.squeeze()) for r in response_tensors]

    #### Compute reward score
    texts = [q + r for q, r in zip(batch["query"], batch["response"])]
    reward_scores = reward_model(texts) #, **sent_kwargs)
    rewards = [torch.tensor(reward_score) for reward_score in reward_scores]

    #### Run PPO step
    stats = ppo_trainer.step(query_tensors, response_tensors, rewards)
    ppo_trainer.log_stats(stats, batch, rewards)
#%%
# save results
with open(f"{OUTPUT_DIR}/results.json", "w") as f:
    json.dump(results.metrics, f)
#model.save_pretrained(OUTPUT_DIR)
#trainer.save_model(OUTPUT_DIR)
ppo_trainer.save_pretrained(f"{OUTOUT_DIR}/final")
#%%
# add log to dvc
repo = Repo(".")
OUTPUT_PATH="/mnt/host/cs234_final/alfred/output/bigscience/bloom-560m,torch_dtype=float16/epoch=1000"
repo.add(OUTPUT_PATH)
repo.push()
#%%
# load the fine-tuned model
model = AutoModelForCausalLM.from_pretrained(OUTPUT_DIR)
#%%
