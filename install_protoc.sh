#!/usr/bin/env bash

### TODO(alexander-fenster, vam-google): 
### The whole idea of this script is wrong. 
### We either should not use different protoc versions across languages,
### or should invent a better way of managing this kind of dependency. 

# Store protobuf versions in an associative array keyed by language.
declare -A protobuf_versions
declare -A override_download_location

# Please adhere to this format, as artman parses these lines for the protobuf versions.
protobuf_versions[nodejs]=3.11.2
protobuf_versions[go]=3.11.2
protobuf_versions[python]=3.11.2
protobuf_versions[ruby]=3.11.2
protobuf_versions[php]=3.11.2
protobuf_versions[csharp]=3.11.2
# Protobuf Java dependency must match grpc-java's protobuf dep.
# https://github.com/grpc/grpc-java/blob/18e099d9d37163905fc61febd2aee983e298a066/build.gradle#L51
protobuf_versions[java]=3.11.0

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
  && hash -r pip3 && pip3 install grpcio>=1.21.1 \
    grpcio-tools==1.21.1 \
    protobuf==${protobuf_versions[python]}
