#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]; then
  set -x
fi

## INIT START ##
# Get the directory where this script is located
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Traverse up the directory tree to find the .github folder
github_dir="$current_dir"
while [ ! -d "$github_dir/.git" ] && [ "$github_dir" != "/" ]; do
  github_dir="$(dirname "$github_dir")"
done

# If the .github folder is found, set root_directory
if [ -d "$github_dir/.git" ]; then
  root_directory="$github_dir"
  if [[ $DEBUG == "0" ]]; then echo "The root directory is: $root_directory"; fi
else
  echo "Error: Unable to find .github folder."
fi
## INIT END ##
#############################################################
if [[ ! -d ${root_directory}/bin ]]; then
  mkdir ${root_directory}/bin
fi

mkdir /tmp/loopy_temp
cd /tmp/loopy_temp

# YQ
YQ_VERSION=4.40.7
wget https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64
#https://github.com/mikefarah/yq/releases/download/v4.40.7/yq_darwin_amd64
chmod 777 yq_linux_amd64
rm -rf ${root_directory}/bin/yq
mv yq_linux_amd64 ${root_directory}/bin/yq

# JQ
JQ_VERSION=1.7.1
wget https://github.com/stedolan/jq/releases/download/jq-${JQ_VERSION}/jq-linux64
# osx https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-macos-amd64
chmod 777 jq-linux64
rm -rf ${root_directory}/bin/jq
mv jq-linux64 ${root_directory}/bin/jq

# GRPC_CURL
GRPC_CURL=1.8.9
curl -L https://github.com/fullstorydev/grpcurl/releases/download/v${GRPC_CURL}/grpcurl_${GRPC_CURL}_linux_x86_64.tar.gz | tar xzv
#wget https://github.com/fullstorydev/grpcurl/releases/download/v${GRPC_CURL}/grpcurl_${GRPC_CURL}_osx_x86_64.tar.gz
#tar xvf grpcurl*.gz
chmod 777 grpcurl
rm -rf ${root_directory}/bin/grpcurl
mv grpcurl ${root_directory}/bin/grpcurl

# OC, KUBECTL
wget https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz
tar xvf openshift-client-linux.tar.gz
rm -rf ${root_directory}/bin/oc
rm -rf ${root_directory}/bin/kubectl
mv oc kubectl ${root_directory}/bin/.

# KUSTOMIZE
wget https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.3.0/kustomize_v5.3.0_linux_amd64.tar.gz
tar xvf kustomize_v5.3.0_linux_amd64.tar.gz
rm -rf ${root_directory}/bin/kustomize
mv kustomize ${root_directory}/bin/.

openssl version
if [[ $? != '0' ]]; then
  sudo dnf -y install openssl
fi

# TKN
wget https://github.com/tektoncd/cli/releases/download/v0.36.0/tkn_0.36.0_Linux_x86_64.tar.gz
tar xvf tkn_0.36.0_Linux_x86_64.tar.gz
rm -rf ${root_directory}/bin/tkn
mv tkn ${root_directory}/bin/.

# ROSA
# https://github.com/openshift/rosa/releases/latest
wget https://github.com/openshift/rosa/releases/latest/download/rosa_Linux_x86_64.tar.gz
tar xvf rosa_Linux_x86_64.tar.gz
rm -rf ${root_directory}/bin/rosa
mv rosa ${root_directory}/bin/.

# OCM
# https://github.com/openshift-online/ocm-cli/releases/latest
curl -L https://github.com/openshift-online/ocm-cli/releases/latest/download/ocm-linux-amd64 -o ocm
chmod +x ocm
rm -rf ${root_directory}/bin/ocm
mv ocm ${root_directory}/bin/.
