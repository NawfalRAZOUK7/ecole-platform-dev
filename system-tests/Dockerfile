FROM node:22-alpine

RUN apk add --no-cache bash ca-certificates curl jq && \
    npm install -g newman@6

WORKDIR /workspace

ENTRYPOINT ["/bin/bash"]
