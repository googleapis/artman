#!/usr/bin/env bash

# Store protobuf versions in an associative array keyed by language.
declare -A protobuf_versions

# Please adhere to this format, as artman parses these lines for the protobuf versions.
protobuf_versions[nodejs]=3.8.0
protobuf_versions[go]=3.8.0
protobuf_versions[python]=3.8.0
protobuf_versions[ruby]=3.8.0
protobuf_versions[php]=3.8.0
protobuf_versions[csharp]=3.8.0
# Protobuf Java dependency must match grpc-java's protobuf dep.
protobuf_versions[java]=3.7.1


# Install each unique protobuf version.
for i in "${protobuf_versions[@]}"
do
  mkdir -p /usr/src/protoc-${i}/ \
      && curl --location https://github.com/google/protobuf/releases/download/v${i}/protoc-${i}-linux-x86_64.zip > /usr/src/protoc-${i}/protoc.zip \
      && cd /usr/src/protoc-${i}/ \
      && unzip protoc.zip \
      && rm protoc.zip \
      && ln -s /usr/src/protoc-${i}/bin/protoc /usr/local/bin/protoc-${i}
done


# Install GRPC and Protobuf.
pip3 install --upgrade pip==10.0.1 setuptools==39.2.0 \
  && hash -r pip3 && pip3 install grpcio>=1.21.1 \
    grpcio-tools==1.21.1 \
    protobuf==${protobuf_versions[python]}