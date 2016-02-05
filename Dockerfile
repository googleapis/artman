FROM ubuntu:14.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    automake \
    gcc \
    build-essential \
    g++ \
    cpp \
    libc6-dev \
    man-db \
    autoconf \
    pkg-config \
    curl \
    git \
    wget

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
USER linuxbrew

# Install protoc and grpc.
RUN curl -s https://raw.githubusercontent.com/grpc/homebrew-grpc/master/scripts/install | bash -s
USER root

# Install Node.js
RUN npm install -g googleapis-packman

ADD . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD python execute_pipeline.py --pipeline_kwargs={\'sleep_secs\':2} SamplePipeline
