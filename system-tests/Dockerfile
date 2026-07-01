FROM node:22-alpine

RUN apk add --no-cache bash ca-certificates curl jq && \
    npm install -g newman@6.2.1

WORKDIR /workspace

RUN chown node:node /workspace
USER node

ENTRYPOINT ["/bin/bash"]
