FROM gcr.io/flock-zerobudget/cs234-final

RUN apt update && apt install  openssh-server sudo -y

RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 test

## copy pycharm remote dev
RUN mkdir -p /mnt/.cache/JetBrains/RemoteDev/dist
COPY --link --from=remotedev dist/ /mnt/.cache/JetBrains/RemoteDev/dist/
#RUN touch /root/.no_auto_tmux
RUN chown -R test /mnt/


RUN  echo 'test:test' | chpasswd

RUN service ssh start

EXPOSE 22

ENTRYPOINT ["/usr/sbin/sshd","-D"]