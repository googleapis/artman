FROM ubuntu:16.04

# Release parameters
ENV GOOGLEAPIS_HASH ac33855ebab4995167d88e8d3975f181098fc6c6
ENV GAPIC_GENERATOR_HASH 579dce05d8bc39607858d144fd095d71e89ec950
# Define version number below. The ARTMAN_VERSION line is parsed by
# .circleci/config.yml and setup.py, please keep the format.
ENV ARTMAN_VERSION 0.16.25

ENV DEBIAN_FRONTEND noninteractive

# Set the locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL C

# OpenJDK repository
RUN apt-get update \
  && apt-get install -y --no-install-recommends software-properties-common \
  && rm -rf /var/lib/apt/lists/* \
  && add-apt-repository ppa:openjdk-r/ppa

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    curl \
    git \
    # debugging
    vim \
    # openssh-client is needed for CircleCI git checkout
    openssh-client \
    # runtime packages
    unzip \
    php \
    python3-pip \
    # Java
    openjdk-8-jdk-headless \
    # NodeJS
    # This installs Node 4 on Ubuntu 16.04.
    nodejs \
    npm \
    # Ruby
    ruby \
    ruby-dev \
    # Required to build grpc_php_plugin
    autoconf \
    autogen \
    libtool \
    autotools-dev \
    automake \
    make \
    g++ \
    # Used to create Python doc
    pandoc \
    # .NET dependencies
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

# Install protoc 3.7.1.
RUN mkdir -p /usr/src/protoc/ \
  && curl --location https://github.com/google/protobuf/releases/download/v3.7.1/protoc-3.7.1-linux-x86_64.zip > /usr/src/protoc/protoc.zip \
  && cd /usr/src/protoc/ \
  && unzip protoc.zip \
  && rm protoc.zip \
  && ln -s /usr/src/protoc/bin/protoc /usr/local/bin/protoc

# Install GRPC and Protobuf.
RUN pip3 install --upgrade pip==10.0.1 setuptools==39.2.0 \
  && hash -r pip3 && pip3 install \
    # Ensure that grpcio matches requirements.txt
    grpcio==1.17.1 \
    grpcio-tools==1.17.1 \
    protobuf==3.7.1

# Install grpc_csharp_plugin
RUN curl -L https://www.nuget.org/api/v2/package/Grpc.Tools/1.17.1 -o temp.zip \
  && unzip -p temp.zip tools/linux_x64/grpc_csharp_plugin > /usr/local/bin/grpc_csharp_plugin \
  && chmod +x /usr/local/bin/grpc_csharp_plugin \
  && rm temp.zip

# Setup JAVA_HOME, this is useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

# Ubuntu apt uses "nodejs" as the executable, but everything else expects
# the executable to be spelled "node".
RUN ln -s /usr/bin/nodejs /usr/local/bin/node

# Install Go.
RUN mkdir -p /golang \
  && cd /golang \
  && curl https://dl.google.com/go/go1.11.linux-amd64.tar.gz > go.tar.gz \
  && (echo 'b3fcf280ff86558e0559e185b601c9eade0fd24c900b4c63cd14d1d38613e499 go.tar.gz' | sha256sum -c) \
  && tar xzf go.tar.gz \
  && rm go.tar.gz \
  && cd /
ENV PATH $PATH:/golang/go/bin

# Download the go protobuf support.
ENV GOPATH /go
ENV PATH $GOPATH/bin:$PATH
RUN mkdir -p "$GOPATH/src" "$GOPATH/bin" "$GOPATH/pkg" \
  && chmod -R 777 "$GOPATH" \
  && go get -u github.com/golang/protobuf/protoc-gen-go \
  && go clean -cache -testcache -modcache

# Setup tools for codegen of Ruby
RUN gem install rake --no-ri --no-rdoc \
  && gem install rubocop --version '= 0.39.0' --no-ri --no-rdoc \
  && gem install bundler --version '= 1.12.1' --no-ri --no-rdoc \
  && gem install rake --version '= 10.5.0' --no-ri --no-rdoc \
  && gem install grpc-tools --version '=1.17.1' --no-ri --no-rdoc

# Install grpc_php_plugin
RUN git clone -b v1.17.1 --recurse-submodules --depth=1 https://github.com/grpc/grpc.git /temp/grpc \
  && cd /temp/grpc \
  && make -j $(nproc) grpc_php_plugin \
  && mv ./bins/opt/grpc_php_plugin /usr/local/bin/ \
  && cd / \
  && rm -r /temp/grpc

# Install PHP formatting tools
RUN curl -L https://github.com/FriendsOfPHP/PHP-CS-Fixer/releases/download/v2.9.1/php-cs-fixer.phar -o /usr/local/bin/php-cs-fixer \
  && chmod a+x /usr/local/bin/php-cs-fixer \
  && cd /
RUN curl -L https://squizlabs.github.io/PHP_CodeSniffer/phpcbf.phar -o /usr/local/bin/phpcbf \
  && chmod a+x /usr/local/bin/phpcbf \
  && cd /

# Used to add docstrings to the Python protoc output.
RUN pip3 install protoc-docs-plugin==0.3.0

# Install .NET Core SDK
ENV DOTNET_SDK_VERSION 1.0.4
ENV DOTNET_SDK_DOWNLOAD_URL https://dotnetcli.blob.core.windows.net/dotnet/Sdk/$DOTNET_SDK_VERSION/dotnet-dev-ubuntu.16.04-x64.$DOTNET_SDK_VERSION.tar.gz

RUN curl -SL $DOTNET_SDK_DOWNLOAD_URL --output dotnet.tar.gz \
    && mkdir -p /usr/share/dotnet \
    && tar -zxf dotnet.tar.gz -C /usr/share/dotnet \
    && rm dotnet.tar.gz \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet

# Install googleapis.
RUN git clone --single-branch https://github.com/googleapis/googleapis \
  && cd googleapis \
  && git checkout $GOOGLEAPIS_HASH \
  && cd .. \
  && rm -rf /googleapis/.git/

# Install toolkit.
RUN git clone --single-branch https://github.com/googleapis/gapic-generator toolkit \
  && cd toolkit/ \
  && git checkout $GAPIC_GENERATOR_HASH \
  && ./gradlew fatJar createToolPaths \
  && cd .. \
  && rm -rf /toolkit/.git/
ENV TOOLKIT_HOME /toolkit

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
ADD . /artman
ARG install_artman_from_source=false
RUN if [ "$install_artman_from_source" = true ]; then pip3 install -e /artman; else pip3 install googleapis-artman==$ARTMAN_VERSION; rm -r /artman; fi
