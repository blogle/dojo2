FROM dojo:latest

ARG DOJO_BUILD_SHA
ENV DOJO_BUILD_SHA=${DOJO_BUILD_SHA}
LABEL org.opencontainers.image.revision=${DOJO_BUILD_SHA}

COPY web/dist/ /share/dojo/
