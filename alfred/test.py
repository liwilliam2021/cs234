import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

tokenizer = AutoTokenizer.from_pretrained(r"dmayhem93/toolformer_v0_epoch2")
model = AutoModelForCausalLM.from_pretrained(
    r"dmayhem93/toolformer_v0_epoch2",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
).cuda()
generator = pipeline(
    "text-generation", model=model, tokenizer=tokenizer, device=0
)