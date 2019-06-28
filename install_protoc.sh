#!/usr/bin/env bash

### TODO(alexander-fenster, vam-google): 
### The whole idea of this script is wrong. 
### We either should not use different protoc versions across languages,
### or should invent a better way of managing this kind of dependency. 

# Store protobuf versions in an associative array keyed by language.
declare -A protobuf_versions
declare -A override_download_location

# Please adhere to this format, as artman parses these lines for the protobuf versions.
protobuf_versions[nodejs]=3.8.0
protobuf_versions[go]=3.8.0
protobuf_versions[python]=3.8.0
protobuf_versions[ruby]=3.8.0
protobuf_versions[php]=3.9.0-rc1
protobuf_versions[csharp]=3.8.0
# Protobuf Java dependency must match grpc-java's protobuf dep.
protobuf_versions[java]=3.7.1

# RC1 url has no logic: compare rc1 in the folder name with rc-1 in the filename
override_download_location[3.9.0-rc1]=https://github.com/protocolbuffers/protobuf/releases/download/v3.9.0-rc1/protoc-3.9.0-rc-1-linux-x86_64.zip

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
pip3 install --upgrade pip==10.0.1 setuptools==39.2.0 \
  && hash -r pip3 && pip3 install grpcio>=1.21.1 \
    grpcio-tools==1.21.1 \
    protobuf==${protobuf_versions[python]}
