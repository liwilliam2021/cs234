
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel AS environment

ENV DEBIAN_FRONTEND=noninteractive

# various helper tools
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get update
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y wget vim
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y virtualenv
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y python3.10


RUN mkdir -p /mnt/host
WORKDIR /mnt/host

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  virtualenv venv
#COPY venv /mnt/host/venv

#SHELL ["/root/miniconda3/bin/conda", "run", "--no-capture-output", "-n", "cs234_hw3", "/bin/bash", "-c"]

COPY ../requirements.txt /mnt/host/requirements.txt
#RUN mv requirements.txt requirements1.txt
RUN --mount=type=cache,target=/root/.cache/pip \
  venv/bin/pip install -r /mnt/host/requirements.txt

COPY --link ./ /mnt/host/

RUN mkdir -p /root/.cache/huggingface
COPY --link --from=huggingface-cache ./ /root/.cache/huggingface/


FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel AS deploy

#COPY alfred.py ~/alfred.py
#ENTRYPOINT ["/root/miniconda3/bin/conda", "init", "bash"

## various helper tools
#RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
#    --mount=target=/var/cache/apt,type=cache,sharing=locked \
#  apt-get update
#RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
#    --mount=target=/var/cache/apt,type=cache,sharing=locked \
#  apt-get install -y wget vim



#COPY ../.mujoco /root/.mujoco

# copy code
RUN mkdir -p /mnt/host #/results
#COPY ../*.py /mnt/host
#COPY ../data /mnt/host/data
#COPY ../.git /mnt/host/.git
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get update
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y git
#RUN --mount=type=secret,id=git_key \
#    cd /mnt/host && \
#    git clone "https://$(cat /run/secrets/git_key)@github.com/pongnguy/cs234_pset3"

## copy venv
COPY --link --from=environment /mnt/host/ /mnt/host/
RUN touch /root/.no_auto_tmux

WORKDIR /mnt/host
## copy conda
#COPY --link --from=environment /root/miniconda3 /root/miniconda3
#RUN echo "export PATH=$PATH:/root/miniconda3/bin" >> ~/.bashrc # && source ~/.bashrc
## copy mujoco
#COPY --link --from=environment /root/.mujoco /root/.mujoco

# copy ssh key for downloading data
#RUN --mount=type=secret,id=ssh_key \
#    mkdir /root/.ssh && \
#    cp /run/secrets/ssh_key /root/.ssh/id_rsa
#RUN chmod 600 /root/.ssh/id_rsa

#WORKDIR /mnt/host
#CMD ["/root/miniconda3/bin/conda", "run", "--no-capture-output", "-n", "cs234_hw3", "conda", "activate", "cs234_hw3"]
#ENTRYPOINT ["/root/miniconda3/bin/conda", "run", "--no-capture-output", "-n", "cs234_hw3", "/bin/bash"]
#ENTRYPOINT ["/root/miniconda3/bin/conda", "activate", "cs234_hw3"]
#RUN echo "source /root/miniconda3/bin/activate cs234_hw3" >> ~/.bashrc
#ENTRYPOINT . ~/.bashrc && conda activate cs234_hw3
