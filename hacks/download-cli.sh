#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]; then
  set -x
fi

TEST_ENV="local"
if [[ $1 == "ci" ]]; then
  TEST_ENV="ci"
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

if [[ -z root_directory ]]; then
  die "Error: Unable to find .github folder."
fi

## INIT END ##
#############################################################
if [[ ! -d ${root_directory}/bin ]]; then
  mkdir ${root_directory}/bin
fi

if [[  -d /tmp/loopy_temp ]]; then
  rm -rf /tmp/loopy_temp
fi
mkdir /tmp/loopy_temp
cd /tmp/loopy_temp

check_binary_exists() {
    binary_path=$1
    if [[ -f "$binary_path" ]]; then
        echo "✅ Binary already exists: $binary_path"
        return 0
    fi
    return 1
}


# Install JQ (mandatory)
if ! check_binary_exists "${root_directory}/bin/jq"; then
    echo "⬇️ Downloading JQ (Latest)..."
    wget --progress=bar:force:noscroll "https://github.com/jqlang/jq/releases/latest/download/jq-linux64" -O jq
    chmod +x jq
    rm -rf "${root_directory}/bin/jq"
    mv jq "${root_directory}/bin/jq"
    echo "✅ JQ installed successfully!"
fi


# Function to get the latest release version from GitHub API
get_latest_release() {
    repo=$1  
    curl -s "https://api.github.com/repos/${repo}/releases/latest" | jq -r '.tag_name'
}

delete_if_exists() {
    file_path=$1
    if [[ -f "$file_path" ]]; then
        echo "🗑️ Removing existing file: $file_path"
        rm -f "$file_path"
    fi
}

echo "📂 Installing tools in ${root_directory}/bin"

# Install YQ
YQ_VERSION=$(get_latest_release "mikefarah/yq" | sed 's/v//')
if ! check_binary_exists "${root_directory}/bin/yq"; then
    echo "⬇️ Downloading YQ (v${YQ_VERSION})..."
    wget --progress=bar:force:noscroll "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64" -O yq
    chmod +x yq
    delete_if_exists "${root_directory}/bin/yq"
    mv yq "${root_directory}/bin/yq"
    echo "✅ YQ installed successfully!"
fi


# Install GRPCURL
GRPC_CURL_VERSION=$(get_latest_release "fullstorydev/grpcurl" | sed 's/v//')
if ! check_binary_exists "${root_directory}/bin/grpcurl"; then
    echo "⬇️ Downloading GRPCURL (v${GRPC_CURL_VERSION})..."
    wget --progress=bar:force:noscroll "https://github.com/fullstorydev/grpcurl/releases/download/v${GRPC_CURL_VERSION}/grpcurl_${GRPC_CURL_VERSION}_linux_x86_64.tar.gz"
    tar xf "grpcurl_${GRPC_CURL_VERSION}_linux_x86_64.tar.gz"
    delete_if_exists "${root_directory}/bin/grpcurl"
    mv grpcurl "${root_directory}/bin/grpcurl"
    chmod +x "${root_directory}/bin/grpcurl"
    echo "✅ GRPCURL installed successfully!"
fi

# Install OC and KUBECTL
if ! check_binary_exists "${root_directory}/bin/oc" || ! check_binary_exists "${root_directory}/bin/kubectl"; then
    echo "⬇️ Downloading OpenShift CLI (OC & Kubectl)..."
    wget --progress=bar:force:noscroll "https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz"
    tar xf openshift-client-linux.tar.gz
    delete_if_exists "${root_directory}/bin/oc"
    delete_if_exists "${root_directory}/bin/kubectl"
    mv oc kubectl "${root_directory}/bin/"
    echo "✅ OpenShift CLI (OC & Kubectl) installed successfully!"
fi

# Install KUSTOMIZE
KUSTOMIZE_VERSION=$(get_latest_release "kubernetes-sigs/kustomize" | sed 's/kustomize\///')
if ! check_binary_exists "${root_directory}/bin/kustomize"; then
    echo "⬇️ Downloading Kustomize (v${KUSTOMIZE_VERSION})..."
    wget --progress=bar:force:noscroll "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz"
    tar xf "kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz"
    delete_if_exists "${root_directory}/bin/kustomize"
    mv kustomize "${root_directory}/bin/kustomize"
    chmod +x "${root_directory}/bin/kustomize"
    echo "✅ Kustomize installed successfully!"
fi

# Check and install OpenSSL if not installed
echo "🔍 Checking for OpenSSL..."
if ! openssl version &>/dev/null; then
  echo "⚠️ OpenSSL not found! Installing..."
  sudo dnf -y install openssl
  echo "✅ OpenSSL installed successfully!"
else
  echo "✅ OpenSSL is already installed!"
fi

# Install TKN
TKN_VERSION=$(get_latest_release "tektoncd/cli" | sed 's/v//')
if ! check_binary_exists "${root_directory}/bin/tkn"; then
    echo "⬇️ Downloading Tekton CLI (TKN v${TKN_VERSION})..."
    wget --progress=bar:force:noscroll "https://github.com/tektoncd/cli/releases/download/v${TKN_VERSION}/tkn_${TKN_VERSION}_Linux_x86_64.tar.gz"
    tar xf "tkn_${TKN_VERSION}_Linux_x86_64.tar.gz"
    delete_if_exists "${root_directory}/bin/tkn"
    mv tkn "${root_directory}/bin/tkn"
    chmod +x "${root_directory}/bin/tkn"
    echo "✅ Tekton CLI installed successfully!"
fi

if [[ $TEST_ENV == "local" ]]; then
  # Install ROSA
  if ! check_binary_exists "${root_directory}/bin/rosa"; then
      echo "⬇️ Downloading ROSA CLI..."
      wget --progress=bar:force:noscroll "https://github.com/openshift/rosa/releases/latest/download/rosa_Linux_x86_64.tar.gz"
      tar xf rosa_Linux_x86_64.tar.gz    
      delete_if_exists "${root_directory}/bin/rosa"
      mv rosa "${root_directory}/bin/rosa"
      chmod +x "${root_directory}/bin/rosa"
      echo "✅ ROSA CLI installed successfully!"
  fi

  # Install OCM
  if ! check_binary_exists "${root_directory}/bin/ocm"; then
      echo "⬇️ Downloading OCM CLI..."
      wget --progress=bar:force:noscroll "https://github.com/openshift-online/ocm-cli/releases/latest/download/ocm-linux-amd64" -O ocm
      chmod +x ocm
      delete_if_exists "${root_directory}/bin/ocm"
      mv ocm "${root_directory}/bin/ocm"
      echo "✅ OCM CLI installed successfully!"
  fi
  # Install kind
  if ! check_binary_exists "${root_directory}/bin/kind"; then
      echo "⬇️ Downloading kind (Latest)..."
      wget --progress=bar:force:noscroll "https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64" -O kind
      chmod +x kind
      rm -rf "${root_directory}/bin/kind"
      mv kind "${root_directory}/bin/kind"
      echo "✅ kind installed successfully!"
  fi
fi


chmod -R 777 ${root_directory}/bin
echo "🎉 All tools have been successfully installed with the latest versions!"
