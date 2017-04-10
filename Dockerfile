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
    git \
    vim # for debug

# Install runtime packages.
RUN apt-get update && \
    apt-get install -y \
    ruby \
    python \
    python-dev \
    python-pip \
    unzip \
    perl \
    software-properties-common \
    php-pear

# Install Oracle JDK 8
RUN add-apt-repository ppa:openjdk-r/ppa
RUN apt-get update && apt-get install -y openjdk-8-jdk

# Setup JAVA_HOME, this is useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

# Install NodeJS
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

# Manually install protobuf with --no-binary flag before installing protoc
# Python and pip are installed by 'brew install --with-plugins grpc'. We need
# to install them preemptively, and then install the protobuf package with
# the --no-binary flag to work around https://github.com/google/protobuf/issues/2895
RUN brew install python
RUN pip install --upgrade pip
RUN pip install protobuf==3.2.0 --no-binary protobuf

# Install protoc and grpc.
RUN brew tap grpc/grpc
RUN brew install --with-plugins grpc

# Install Go1.6 from linuxbrew.
RUN brew install go

USER root

ENV GOPATH /go
ENV PATH $GOPATH/bin:/home/linuxbrew/.linuxbrew/opt/go/libexec/bin:$PATH
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH"
RUN go get -u github.com/golang/protobuf/proto github.com/golang/protobuf/protoc-gen-go

# Install packman
# TODO: consider installing released packages once artman is versioned (so that
#   each release of artman is pegged to a release of packman)
RUN npm install -g https://github.com/googleapis/packman.git

# Setup tools for codegen of Ruby
RUN gem install rubocop --version '= 0.39.0' --no-ri --no-rdoc
RUN gem install bundler --version '= 1.12.1' --no-ri --no-rdoc
RUN gem install rake --version '= 10.5.0' --no-ri --no-rdoc
RUN gem install grpc-tools --version '=1.0.0' --no-ri --no-rdoc

# Install couple of git repos
WORKDIR /
RUN git clone https://github.com/googleapis/googleapis
RUN git clone https://github.com/googleapis/toolkit
ENV TOOLKIT_HOME /toolkit
WORKDIR /toolkit
RUN sudo ./gradlew install # Install toolkit. Must sudo to download gradle plugins.

# Install googleapis protocol compiler plugin which is needed to build gapic resource classes.
RUN pip install -e git+https://github.com/googleapis/proto-compiler-plugin#egg=remote

# Install PHP protobuf plugin
WORKDIR /
RUN apt-get install -y ruby2.0 ruby2.0-dev
RUN /usr/bin/gem2.0 install ronn --no-ri --no-rdoc
RUN git clone https://github.com/stanley-cheung/Protobuf-PHP.git
WORKDIR /Protobuf-PHP
RUN rake pear:package version=1.0 --trace
RUN pear install Protobuf-1.0.tgz

# Install PHP formatting tools
RUN pear install PHP_CodeSniffer-2.7.0
RUN curl -L https://github.com/FriendsOfPHP/PHP-CS-Fixer/releases/download/v1.11.8/php-cs-fixer.phar -o /usr/local/bin/php-cs-fixer
RUN chmod a+x /usr/local/bin/php-cs-fixer

# Install artman.
# TODO(ethanbao): pipeline should be installed from package manager.
ADD . /src
WORKDIR /src
RUN pip install -r requirements.txt

# Run smoketests
# TODO(ethanbao): this should be part of artman CI.
RUN python test/smoketest.py
