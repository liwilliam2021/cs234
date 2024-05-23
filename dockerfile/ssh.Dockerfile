FROM gcr.io/flock-zerobudget/cs234-final

RUN apt update && apt install  openssh-server sudo -y

#RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 alfred

RUN echo 'root:Cc17931793' | chpasswd #echo 'alfred:Cc17931793' | chpasswd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
    #sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && \
    #echo 'export NOTVISIBLE="in users profile"' >> ~/.bashrc && \
    #echo "export VISIBLE=now" >> /etc/profile

RUN service ssh start

## copy pycharm remote dev
#RUN mkdir -p /mnt/.cache/JetBrains/RemoteDev/dist
#COPY --link --from=remotedev dist/ /mnt/.cache/JetBrains/RemoteDev/dist/
RUN touch /root/.no_auto_tmux
#RUN if ! [ -d /home/alfred ]; then mkdir /home/alfred; fi; chown -R alfred /home/alfred

EXPOSE 22

ENTRYPOINT ["/usr/sbin/sshd","-D"]