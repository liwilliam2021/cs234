variable "SSH_PUBLIC_KEY" {}
variable "BRANCH" {}
variable "REF_NAME" {}
variable "MINIO_ACCESS_KEY" {}
variable "MINIO_SECRET_KEY" {}
variable "B2_ACCESS_KEY" {}
variable "B2_SECRET_KEY" {}
#variable "HOME1" {}

variable "REPO" {
  default = "dzcr/cs234-final"
}

group "default" {
  targets = ["base", "ollama-moondream", "ollama-llama3", "ollama-llama3-70b"] #, "train"]
}

#target "test" {
#  dockerfile = "dockerfile/test.Dockerfile"
#  tags = ["${REPO}:test"]
#  output = ["type=registry"]
#  args = {
#    SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
#    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
#    HOME = "${HOME1}"
#  }
#}

target "main" {
  name = "${variant}"
  matrix = {
    variant = ["base", "will", "train", "test"]
  }
  #target = tgt
  dockerfile = "dockerfile/${variant}.Dockerfile"
  tags = ["${REPO}:${variant}_${BRANCH}"]
  output = ["type=registry"]
  args = {
    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
    REF_NAME = "${REF_NAME}"
    B2_ACCESS_KEY = "${B2_ACCESS_KEY}"
    B2_SECRET_KEY = "${B2_SECRET_KEY}"
    MINIO_ACCESS_KEY = "${MINIO_ACCESS_KEY}"
    MINIO_SECRET_KEY = "${MINIO_SECRET_KEY}"
  }
}


#target "base" {
#  dockerfile = "dockerfile/base.Dockerfile"
#  tags = ["${REPO}:base_${BRANCH}"]
#  output = ["type=registry"]
#  args = {
#    SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
#    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
#  }
#}
#
#target "will" {
#  dockerfile = "dockerfile/will.Dockerfile"
#  tags = ["${REPO}:will_${BRANCH}"]
#  output = ["type=registry"]
#  args = {
#    SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
#    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
#  }
#}

target "ollama" {
  name = "ollama-${variant}"
  matrix = {
    variant = ["moondream", "llama3", "llama3-70b"]
  }
  #target = tgt
  dockerfile = "dockerfile/ollama.Dockerfile"
  tags = ["${REPO}:ollama-${variant}_${BRANCH}"]
  output = ["type=registry"]
  args = {
    MODEL = "${variant}"
    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
  }
}

#target "ollama-moondream" {
#  dockerfile = "dockerfile/ollama.Dockerfile"
#  tags = ["${REPO}:ollama-moondream_${BRANCH}"]
#  output = ["type=registry"]
#  args = {
#    MODEL = "moondream"
#    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
#  }
#}
#
#target "ollama-llama3" {
#  dockerfile = "dockerfile/ollama.Dockerfile"
#  tags = ["${REPO}:ollama-llama3_${BRANCH}"]
#  output = ["type=registry"]
#  args = {
#    MODEL = "llama3"
#    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
#  }
#}

#target "ollama-llama3-70b" {
#  dockerfile = "dockerfile/ollama.Dockerfile"
#  tags = ["${REPO}:ollama-llama3-70b_${BRANCH}"]
#  output = ["type=registry"]
#  args = {
#    MODEL = "llama3:70b"
#    SSH_PUBLIC_KEY = "${SSH_PUBLIC_KEY}"
#  }
#}

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