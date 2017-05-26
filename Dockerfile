FROM ubuntu:16.04

ENV DEBIAN_FRONTEND noninteractive

# Set the locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL C

# Install essential packages.
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    man-db \
    pkg-config \
    # Needed by gcloud-python
    libffi-dev \
    # Needed by gcloud-python
    libssl-dev \
    curl \
    kdiff3 \
    git \
    vim \
  && rm -rf /var/lib/apt/lists/*

# Install runtime packages.
RUN apt-get update \
  && apt-get install -y \
    unzip \
    perl \
    software-properties-common \
    php-pear \
    python3-pip \
  && rm -rf /var/lib/apt/lists/*

# Install protoc 3.3.0.
# Currently, the stable version is still 2.6.x, which can only handle proto2
# syntax, so we have to download our own.
RUN mkdir -p /usr/src/protoc/ \
  && curl --location https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip > /usr/src/protoc/protoc-3.3.0.zip \
  && cd /usr/src/protoc/ \
  && unzip protoc-3.3.0.zip \
  && ln -s /usr/src/protoc/bin/protoc /usr/local/bin/protoc

# Install GRPC and Protobuf.
RUN pip3 install --upgrade pip \
  && pip3 install \
    grpcio==1.3.0 \
    protobuf==3.3.0

# Install Oracle JDK 8
RUN add-apt-repository ppa:openjdk-r/ppa \
  && apt-get update \
  && apt-get install -y openjdk-8-jdk \
  && rm -rf /var/lib/apt/lists/*

# Setup JAVA_HOME, this is useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

# Install NodeJS.
# This installs Node 4 on Ubuntu 16.04.
RUN apt-get update \
  && apt-get install -y \
    nodejs \
    npm \
  && rm -rf /var/lib/apt/lists/* \
  # Ubuntu apt uses "nodejs" as the executable, but everything else expects
  # the executable to be spelled "node".
  && ln -s /usr/bin/nodejs /usr/local/bin/node

# Install Ruby.
# This installs Ruby 2.3 on Ubuntu 16.04.
RUN apt-get update \
  && apt-get install -y \
    ruby \
    ruby-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Go.
# This installs Go 1.6 on Ubuntu 16.04.
RUN apt-get update \
  && apt-get install -y golang \
  && rm -rf /var/lib/apt/lists/*

# Download the go protobuf support.
ENV GOPATH /go
ENV PATH $GOPATH/bin:$PATH
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" \
  && chmod -R 777 "$GOPATH" \
  && go get -u github.com/golang/protobuf/proto github.com/golang/protobuf/protoc-gen-go

# Install packman
# TODO: consider installing released packages once artman is versioned (so that
#   each release of artman is pegged to a release of packman)
RUN npm install -g https://github.com/googleapis/packman.git

# Setup tools for codegen of Ruby
RUN gem install rake --no-ri --no-rdoc \
  && gem install rubocop --version '= 0.39.0' --no-ri --no-rdoc \
  && gem install bundler --version '= 1.12.1' --no-ri --no-rdoc \
  && gem install rake --version '= 10.5.0' --no-ri --no-rdoc \
  && gem install grpc-tools --version '=1.0.0' --no-ri --no-rdoc

# Install couple of git repos
RUN git clone https://github.com/googleapis/googleapis
RUN git clone https://github.com/googleapis/toolkit
ENV TOOLKIT_HOME /toolkit

# Install toolkit. Must sudo to download gradle plugins.
RUN cd /toolkit \
  && ./gradlew install \
  && cd /

# Install PHP protobuf plugin.
RUN gem install ronn --no-ri --no-rdoc \
  && git clone https://github.com/stanley-cheung/Protobuf-PHP.git \
  && cd /Protobuf-PHP \
  && rake pear:package version=1.0 --trace \
  && pear install Protobuf-1.0.tgz \

  # Install PHP formatting tools
  && pear install PHP_CodeSniffer-2.7.0 \
  && curl -L https://github.com/FriendsOfPHP/PHP-CS-Fixer/releases/download/v1.11.8/php-cs-fixer.phar -o /usr/local/bin/php-cs-fixer \
  && chmod a+x /usr/local/bin/php-cs-fixer \
  && cd /

# Setup git config used by github commit pushing.
RUN git config --global user.email googleapis-publisher@google.com \
  && git config --global user.name "Google API Publisher"

# Setup artman user config
# Note: This is somewhat brittle as it relies on a specific path
# outside of or inside Docker.
#
# This should probably be fixed to have the smoke test itself provide
# the configuration.
# TODO (lukesneeringer): Fix this.
RUN mkdir -p /root/
ADD artman-user-config-in-docker.yaml /root/.artman/config.yaml

# Install artman and run the smoke test.
ADD . /artman-src/
# RUN pip3 install googleapis-artman==0.4.3

# TODO (lukesneeringer): Move smoke tests to a different venue.
# RUN smoketest_artman.py \
#   && rm -rf /artman/output
