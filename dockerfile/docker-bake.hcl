variable "SERVICE_ACCOUNT" {
  default = "$SERVICE_ACCOUNT"
}

variable "REPO" {
  default = "gcr.io/flock-zerobudget/cs234-final"
}

group "default" {
  targets = ["base", "cloud"]
}

target "base" {
  dockerfile = "dockerfile/base.Dockerfile"
  tags = ["${REPO}:base"]
  output = ["type=registry"]
}

target "cloud" {
  contexts = { base = "target:base" }
  dockerfile = "dockerfile/cloud.Dockerfile"
  tags = ["${REPO}:cloud"]
  output = ["type=registry"]
  args = {
    SERVICE_ACCOUNT = "${SERVICE_ACCOUNT}"
  }
#   secret = [
#     #"type=env,id=KUBECONFIG",
#     "type=file,id=gcloud-serviceaccount,src=/home/alfred/.keys/flock-zerobudget-5f5733b793c1.json"
#   ]
}