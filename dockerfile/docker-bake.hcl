variable "SERVICE_ACCOUNT" {}
variable "SSH_KEY" {}

variable "REPO" {
  default = "gcr.io/flock-zerobudget/cs234-final"
}

group "default" {
  targets = ["base", "will", "ollama-moondream", "ollama-llama3", "ollama-llama3-70b"] #, "train"]
}

target "base" {
  dockerfile = "dockerfile/base.Dockerfile"
  tags = ["${REPO}:base"]
  output = ["type=registry"]
  args = {
    SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
    SSH_KEY = "${SSH_KEY}"
  }
}

target "will" {
  dockerfile = "dockerfile/will.Dockerfile"
  tags = ["${REPO}:will"]
  output = ["type=registry"]
  args = {
    SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
    SSH_KEY = "${SSH_KEY}"
  }
}

target "ollama-moondream" {
  dockerfile = "dockerfile/ollama.Dockerfile"
  tags = ["${REPO}:ollama-moondream"]
  output = ["type=registry"]
  args = {
    MODEL = "moondream"
  }
}

target "ollama-llama3" {
  dockerfile = "dockerfile/ollama.Dockerfile"
  tags = ["${REPO}:ollama-llama3"]
  output = ["type=registry"]
  args = {
    MODEL = "llama3"
  }
}

target "ollama-llama3-70b" {
  dockerfile = "dockerfile/ollama.Dockerfile"
  tags = ["${REPO}:ollama-llama3-70b"]
  output = ["type=registry"]
  args = {
    MODEL = "llama3:70b"
  }
}

# target "train" {
#   contexts = { base = "target:train" }
#   dockerfile = "dockerfile/train.Dockerfile"
#   tags = ["${REPO}:train"]
#   output = ["type=registry"]
#   args = {
#     SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
#   }
# #   secret = [
# #     #"type=env,id=KUBECONFIG",
# #     "type=file,id=gcloud-serviceaccount,src=/home/alfred/.keys/flock-zerobudget-5f5733b793c1.json"
# #   ]
# }