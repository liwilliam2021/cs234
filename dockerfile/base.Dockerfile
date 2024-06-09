FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel

ENV DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

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

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y apt-transport-https ca-certificates gnupg curl

#RUN mkdir -p /mnt/host
#WORKDIR /mnt/host

#COPY venv /mnt/host/venv

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y python3.10-distutils python3.10-dev

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  apt-get install -y git

# install minio client for syncing checkpoint with object server
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc \
  --create-dirs \
  -o $HOME/minio-binaries/mc
RUN chmod +x $HOME/minio-binaries/mc
ENV PATH=$PATH:$HOME/minio-binaries/
# add in key
ARG MINIO_ACCESS_KEY
ARG MINIO_SECRET_KEY
RUN mkdir $HOME/.aws && \
    echo "[default]" > $HOME/.aws/credentials && \
    echo "aws_access_key_id = $MINIO_ACCESS_KEY" >> $HOME/.aws/credentials && \
    echo "aws_secret_access_key = $MINIO_SECRET_KEY" >> $HOME/.aws/credentials
RUN echo "[default]" > $HOME/.aws/config && \
    echo "region = us-east-1" >> $HOME/.aws/config
RUN  $HOME/minio-binaries/mc alias set r730 http://storage.diezcansecoramirez.com:9010 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
RUN mkdir /mnt/share
# copy code
RUN mkdir -p /mnt/host
#COPY ../*.py /mnt/host
#COPY ../data /mnt/host/data
#COPY ../.git /mnt/host/.git
#RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
#    --mount=target=/var/cache/apt,type=cache,sharing=locked \
#  apt-get update



ARG REF_NAME
# this whould not invalidate cache for commits on same branch
# only invalidate cache on branch changes
RUN cd /mnt/host && \
    git clone "http://alfred:Cc17931793@git.diezcansecoramirez.com:3000/alfred/cs234_final" cs234_final && \
    cd cs234_final && \
    echo $REF_NAME && \
    git checkout $REF_NAME
#RUN mv /mnt/host/venv /mnt/host/cs234/venv
#
# dvc push access for B2 bucket
ARG B2_ACCESS_KEY
ARG B2_SECRET_KEY
RUN ls -lah /mnt/host/cs234_final && \
    echo '['\''remote "b2"'\'']' > /mnt/host/cs234_final/.dvc/config.local && \
    echo "    access_key_id = $B2_ACCESS_KEY" >> /mnt/host/cs234_final/.dvc/config.local && \
    echo "    secret_access_key = $B2_SECRET_KEY" >> /mnt/host/cs234_final/.dvc/config.local

WORKDIR /mnt/host/cs234_final

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
  virtualenv venv

# could conflict with pulled github version
COPY requirements.txt /mnt/host/cs234_final/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
  venv/bin/pip install -r requirements.txt

#RUN --mount=type=cache,target=/root/.cache/pip \
#  venv/bin/pip install -e .

#RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
#    --mount=target=/var/cache/apt,type=cache,sharing=locked \
#  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
#    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
#RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
#    --mount=target=/var/cache/apt,type=cache,sharing=locked \
#  apt-get update && apt-get install -y google-cloud-cli
RUN --mount=type=cache,target=/root/.cache/pip \
  venv/bin/pip install dvc[all]


#COPY --link ./ /mnt/host/

## copy venv
#COPY --link --from=environment /mnt/host/ /mnt/host/
#RUN touch /root/.no_auto_tmux

# TODO download and install pycharm client
# cython debugger compile
#RUN /usr/bin/python3 /<PYCHARM_INSTALLATION_PATH>/plugins/python/helpers/pydev/setup_cython.py build_ext --inplace

## copy conda
#COPY --link --from=environment /root/miniconda3 /root/miniconda3
#RUN echo "export PATH=$PATH:/root/miniconda3/bin" >> ~/.bashrc # && source ~/.bashrc
## copy mujoco
#COPY --link --from=environment /root/.mujoco /root/.mujoco


#WORKDIR /mnt/host
#CMD ["/root/miniconda3/bin/conda", "run", "--no-capture-output", "-n", "cs234_hw3", "conda", "activate", "cs234_hw3"]
#ENTRYPOINT ["/root/miniconda3/bin/conda", "run", "--no-capture-output", "-n", "cs234_hw3", "/bin/bash"]
#ENTRYPOINT ["/root/miniconda3/bin/conda", "activate", "cs234_hw3"]
#RUN echo "source /root/miniconda3/bin/activate cs234_hw3" >> ~/.bashrc
#ENTRYPOINT . ~/.bashrc && conda activate cs234_hw3


RUN apt update && apt install  openssh-server sudo -y

#RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 alfred

RUN echo 'root:Cc17931793' | chpasswd #echo 'alfred:Cc17931793' | chpasswd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
    #sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && \
    #echo 'export NOTVISIBLE="in users profile"' >> ~/.bashrc && \
    #echo "export VISIBLE=now" >> /etc/profile
RUN sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

RUN service ssh start

## copy pycharm remote dev
#RUN mkdir -p /mnt/.cache/JetBrains/RemoteDev/dist
#COPY --link --from=remotedev dist/ /mnt/.cache/JetBrains/RemoteDev/dist/
RUN touch /root/.no_auto_tmux
#RUN if ! [ -d /home/alfred ]; then mkdir /home/alfred; fi; chown -R alfred /home/alfred

EXPOSE 22

RUN git config --global --add safe.directory /mnt/host/cs234_final

RUN --mount=type=cache,target=/root/.cache/pip \
  venv/bin/pip install -U datasets

# dev version of trl has DPOTrainer
RUN venv/bin/python -m pip uninstall -y trl && \
    venv/bin/python -m pip install -U git+https://github.com/huggingface/trl


RUN git config --global user.email "alfred.wechselberger@gmail.com" && \
    git config --global user.name "Alfred" && \
    git config pull.rebase false

##RUN --mount=type=secret,id=gcloud-adc \
##    mkdir -p /root/.config/gcloud/ && \
##    cp /run/secrets/gcloud-adc /root/.config/gcloud/application_default_credentials.json

#RUN venv/bin/python -m ipykernel install --user --name=cs234_final

EXPOSE 22

ARG SSH_PUBLIC_KEY

# copy ssh key for downloading data
#RUN --mount=type=secret,id=ssh_key \
RUN mkdir /root/.ssh && \
    echo "$SSH_PUBLIC_KEY" | sed "s/^'//" | sed "s/'$//" > /root/.ssh/authorized_keys
    #cp /run/secrets/ssh_key /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/authorized_keys

EXPOSE 8080
#RUN apt-get install tini
#ENTRYPOINT ["/tini", "--"]
#CMD ["/usr/sbin/sshd", "-D"]
ENV SHELL=/bin/bash
ENTRYPOINT ["/bin/bash", "-c", "service ssh restart && $HOME/minio-binaries/mc mirror --watch /mnt/share r730/cs234-final/$(uname -n) & /mnt/host/cs234_final/venv/bin/python -m jupyter lab --allow-root --autoreload --no-browser --ip '*' --port 8080 --IdentityProvider.token=f9a3bd4e9f2c3be01cd629154cfb224c2703181e050254b5"]
CMD ["git", "pull"]
#ENTRYPOINT ["/bin/bash", "-c", "service", "ssh", "restart &&", "/mnt/host/cs234_final/venv/bin/python", "jupyter", "lab", "--allow-root", "--autoreload", "--no-browser", "--ip '*'"]