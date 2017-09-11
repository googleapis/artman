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
    less \
    openssh-client \
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
    # Ensure that grpcio matches requirements.txt
    grpcio==1.3.5 \
    grpcio-tools==1.3.5 \
    protobuf==3.3.0

# Install grpc_csharp_plubin
RUN curl -L https://www.nuget.org/api/v2/package/Grpc.Tools/1.3.6 -o temp.zip \
  && unzip -p temp.zip tools/linux_x64/grpc_csharp_plugin > /usr/local/bin/grpc_csharp_plugin \
  && chmod +x /usr/local/bin/grpc_csharp_plugin \
  && rm temp.zip

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

# Install grpc_php_plugin
RUN apt-get update \
  && apt-get install -y autoconf autogen libtool \
  && git clone -b v1.4.1 https://github.com/grpc/grpc.git /temp/grpc \
  && cd /temp/grpc \
  && git submodule update --init --recursive \
  && make grpc_php_plugin \
  && mv ./bins/opt/grpc_php_plugin /usr/local/bin/ \
  && cd / \
  && rm -r /temp/grpc

# Install PHP formatting tools
RUN pear install PHP_CodeSniffer-2.7.0 \
  && curl -L https://github.com/FriendsOfPHP/PHP-CS-Fixer/releases/download/v1.11.8/php-cs-fixer.phar -o /usr/local/bin/php-cs-fixer \
  && chmod a+x /usr/local/bin/php-cs-fixer \
  && cd /

# Set up tools for Python codegen; these are:
#   pandoc: an apt package that can convert text between formats
#     (example: Markdown to Restructured Text)
#   protoc-docs-plugin: A protoc plugin to add docstrings to the Python
#     protoc output.cd
RUN apt-get update \
  && apt-get install -y pandoc \
  && pip3 install protoc-docs-plugin \
  && rm -rf /var/lib/apt/lists/*

# Install .NET Core SDK (about 280MB)
# Install .NET CLI dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libc6 \
    libcurl3 \
    libgcc1 \
    libgssapi-krb5-2 \
    liblttng-ust0 \
    libssl1.0.0 \
    libstdc++6 \
    libunwind8 \
    libuuid1 \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Install .NET Core SDK
ENV DOTNET_SDK_VERSION 1.0.4
ENV DOTNET_SDK_DOWNLOAD_URL https://dotnetcli.blob.core.windows.net/dotnet/Sdk/$DOTNET_SDK_VERSION/dotnet-dev-ubuntu.16.04-x64.$DOTNET_SDK_VERSION.tar.gz

RUN curl -SL $DOTNET_SDK_DOWNLOAD_URL --output dotnet.tar.gz \
    && mkdir -p /usr/share/dotnet \
    && tar -zxf dotnet.tar.gz -C /usr/share/dotnet \
    && rm dotnet.tar.gz \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet

# Install couple of git repos
RUN git clone https://github.com/googleapis/googleapis \
  && cd googleapis \
  && git checkout adc3b951d5dbeac0df787444f1fc85e61a461fea \
  && cd .. \
  && rm -rf /googleapis/.git/
RUN git clone https://github.com/googleapis/toolkit \
  && cd toolkit/ \
  && git checkout 0345503faa9e36781d30eb77ac02b8737048da91 \
  && cd .. \
  && rm -rf /toolkit/.git/
ENV TOOLKIT_HOME /toolkit

# Install toolkit.
RUN cd /toolkit \
  && ./gradlew install \
  && ./gradlew build \
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

# Install artman.
RUN pip3 install googleapis-artman==0.4.14
