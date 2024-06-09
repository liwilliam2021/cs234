FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel


SHELL ["/bin/bash", "-c"]




ARG SERVICE_ACCOUNT
#RUN --mount=type=cache,target=/root/.cache/pip \
#  venv/bin/pip install -e .
ARG HOME

RUN echo "$HOME"

#RUN --mount=type=secret,id=gcloud-serviceaccount \
RUN mkdir -p /root/.config/gcloud/ && \
    echo "$SERVICE_ACCOUNT" | sed "s/'{/{/" | sed "s/}'/}/" > /root/.config/gcloud/serviceaccount.json && \
    cat /root/.config/gcloud/serviceaccount.json
ENV SHELL=/bin/bash
ENTRYPOINT "/bin/bash"