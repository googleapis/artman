FROM ubuntu:14.04

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install essential packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    man-db \
    pkg-config \
    # Needed by gcloud-python
    libffi-dev \
    # Needed by gcloud-python
    libssl-dev \
    curl \
    kdiff3 \
    git

# Install runtime packages.
RUN apt-get update && \
    apt-get install -y \
    ruby \
    python \
    python-dev \
    python-pip \
    unzip \
    perl \
    openjdk-7-jdk

# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-7-openjdk-amd64

ADD ./scripts /scripts
WORKDIR /scripts
# This is need to install nodejs 4.x otherwise nodejs 0.x will be installed.
RUN bash setup_node4.sh
RUN apt-get install -y nodejs

# Install linuxbrew.
RUN useradd -m -s /bin/bash linuxbrew
RUN echo 'linuxbrew ALL=(ALL) NOPASSWD:ALL' >>/etc/sudoers
USER linuxbrew
WORKDIR /home/linuxbrew
ENV PATH /home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH
ENV SHELL /bin/bash
RUN yes |ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install)"
RUN brew doctor || true

# Install protoc and grpc.
RUN brew tap grpc/grpc
RUN brew install --with-plugins grpc

# Install Go1.6 from linuxbrew.
RUN brew install go

USER root

ENV GOPATH /go
ENV PATH $GOPATH/bin:/home/linuxbrew/.linuxbrew/opt/go/libexec/bin:$PATH
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"

# Install pacman
RUN npm install -g googleapis-packman@0.8.0

# Setup tools for codegen of Ruby
RUN gem install rubocop --version '= 0.39.0' --no-ri --no-rdoc
RUN gem install bundler --version '= 1.12.1' --no-ri --no-rdoc
RUN gem install rake --version '= 10.5.0' --no-ri --no-rdoc

# Install couple of git repos
WORKDIR /
RUN git clone https://github.com/googleapis/googleapis
RUN git clone https://github.com/googleapis/toolkit
ENV TOOLKIT_HOME /toolkit

# Run the pipeline.
# TODO(ethanbao): pipeline should be installed from package manager.
ADD . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD python start_conductor.py
