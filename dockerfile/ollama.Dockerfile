FROM ollama/ollama

ARG MODEL
# bring up ollama only to pull model and store in container
RUN ollama serve & servePID=$!; sleep 10; ollama pull $MODEL
#RUN ollama pull llama3
# TODO need to kill server or exits automatically on container exit?
#RUN kill $servePID

SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/bin/bash", "-c", "ollama serve"] # & sleep 10; ollama run $MODEL"]