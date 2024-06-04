FROM gcr.io/flock-zerobudget/cs234-final:base

ENV DEBIAN_FRONTEND=noninteractive

ARG SERVICE_ACCOUNT
#RUN --mount=type=cache,target=/root/.cache/pip \
#  venv/bin/pip install -e .

RUN echo "test"
#RUN --mount=type=secret,id=gcloud-serviceaccount \
RUN mkdir -p /root/.config/gcloud/ && \
    echo "$SERVICE_ACCOUNT" | sed "s/'{/{/" | sed "s/}'/}/" > /root/.config/gcloud/serviceaccount.json && \
    cat /root/.config/gcloud/serviceaccount.json && \
    gcloud auth login --cred-file=/root/.config/gcloud/serviceaccount.json

RUN gcloud init
#RUN gcloud iam service-accounts keys create /root/.config/gcloud/serviceaccount.json --iam-account=cloudstorage@flock-zerobudget.iam.gserviceaccount.com

RUN gcloud auth activate-service-account --key-file=/root/.config/gcloud/serviceaccount.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
RUN cp /root/.config/gcloud/serviceaccount.json /root/.config/gcloud/application_default_credentials.json
# TODO not sure if needed to do auth application-default login since push to bucket is working
#RUN gcloud auth application-default login --impersonate-service-account cloudstorage@flock-zerobudget.iam.gserviceaccount.com
#RUN gcloud auth application-default set-quota-project flock-zerobudget
RUN gcloud config set project flock-zerobudget


##RUN --mount=type=secret,id=gcloud-adc \
##    mkdir -p /root/.config/gcloud/ && \
##    cp /run/secrets/gcloud-adc /root/.config/gcloud/application_default_credentials.json


EXPOSE 22

#RUN apt-get install tini
#ENTRYPOINT ["/tini", "--"]
#CMD ["/usr/sbin/sshd", "-D"]
#ENTRYPOINT ["/usr/sbin/sshd","-D"]
#CMD ["/mnt/host/cs234_final/venv/bin/python", "jupyter", "lab", "--allow-root", "--autoreload", "--no-browser"]