FROM ollama/ollama

ARG MODEL
# bring up ollama only to pull model and store in container
SHELL ["/bin/bash", "-c"]
RUN ollama serve & servePID=$!; sleep 10; ollama pull $(echo $MODEL | sed 's/-70b/:70b/')
#RUN ollama pull llama3
# TODO need to kill server or exits automatically on container exit?
#RUN kill $servePID


EXPOSE 22

RUN apt update && apt install  openssh-server sudo -y

#RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 alfred

RUN echo 'root:Cc17931793' | chpasswd #echo 'alfred:Cc17931793' | chpasswd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
    #sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && \
    #echo 'export NOTVISIBLE="in users profile"' >> ~/.bashrc && \
    #echo "export VISIBLE=now" >> /etc/profile
RUN sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

RUN service ssh start

ARG SSH_KEY

# copy ssh key for downloading data
#RUN --mount=type=secret,id=ssh_key \
RUN mkdir /root/.ssh && \
    echo "$SSH_KEY" | sed "s/^'//" | sed "s/'$//" > /root/.ssh/authorized_keys
    #cp /run/secrets/ssh_key /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/authorized_keys

ENTRYPOINT ["/bin/bash", "-c", "service ssh restart && ollama serve"] # & sleep 10; ollama run $MODEL"]