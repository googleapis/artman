FROM ubuntu:14.04

# Install essential packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    man-db \
    pkg-config \
    curl \
    kdiff3

# Install runtime packages.
RUN apt-get install -y ruby python python-dev python-pip openjdk-7-jre-headless nodejs npm

# Install linuxbrew.
RUN useradd -m -s /bin/bash linuxbrew
RUN echo 'linuxbrew ALL=(ALL) NOPASSWD:ALL' >>/etc/sudoers
USER linuxbrew
WORKDIR /home/linuxbrew
ENV PATH /home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH
ENV SHELL /bin/bash
RUN yes |ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/linuxbrew/go/install)"
RUN brew doctor || true

# Install protoc and grpc.
RUN curl -s https://raw.githubusercontent.com/grpc/homebrew-grpc/master/scripts/install | bash -s

# Install Go1.6 from linuxbrew.
RUN brew install go

USER root

ENV GOPATH /go
ENV PATH $GOPATH/bin:/home/linuxbrew/.linuxbrew/opt/go/libexec/bin:$PATH
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"

# Install Node.js.
RUN npm install -g googleapis-packman

# Run the pipeline.
ADD . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':2} SamplePipeline
