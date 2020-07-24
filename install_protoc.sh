#!/usr/bin/env bash

### TODO(alexander-fenster, vam-google): 
### The whole idea of this script is wrong. 
### We either should not use different protoc versions across languages,
### or should invent a better way of managing this kind of dependency. 

# Store protobuf versions in an associative array keyed by language.
declare -A protobuf_versions
declare -A override_download_location

# Please adhere to this format, as artman parses these lines for the protobuf versions.
protobuf_versions[nodejs]=3.12.3
protobuf_versions[go]=3.12.3
# Protobuf Python should match the latest version available on PyPI
protobuf_versions[python]=3.12.2
protobuf_versions[ruby]=3.12.3
protobuf_versions[php]=3.12.3
protobuf_versions[csharp]=3.12.3
# Protobuf Java dependency must match grpc-java's protobuf dep.
# https://github.com/grpc/grpc-java/blob/master/build.gradle#L61
protobuf_versions[java]=3.12.0

# Install each unique protobuf version.
for i in "${protobuf_versions[@]}"
do
  location=https://github.com/google/protobuf/releases/download/v${i}/protoc-${i}-linux-x86_64.zip
  if [ "${override_download_location[$i]}" != "" ]; then
    location=${override_download_location[$i]}
  fi
  mkdir -p /usr/src/protoc-${i}/ \
      && curl --location $location > /usr/src/protoc-${i}/protoc.zip \
      && cd /usr/src/protoc-${i}/ \
      && unzip protoc.zip \
      && rm protoc.zip \
      && ln -s /usr/src/protoc-${i}/bin/protoc /usr/local/bin/protoc-${i}
done


# Install GRPC and Protobuf.
pip3 install --upgrade pip==20.0.2 setuptools==39.2.0 \
  && hash -r pip3 && pip3 install grpcio==1.30.0 \
    grpcio-tools==1.30.0 \
    protobuf==${protobuf_versions[python]}
