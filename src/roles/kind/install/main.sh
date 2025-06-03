#!/usr/bin/env bash
## INIT START ##
if [[ $DEBUG == "0" ]]; then
  set -x
fi

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
  echo "The root directory is: $root_directory"
else
  echo "Unable to find .github folder"
fi

source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

#################################################################
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
kind_ingress_config=$(yq e '.role.files.kind-ingress-config' $current_dir/config.yaml)
kind_ingress_config_path=$current_dir/$kind_ingress_config


# Check if docker/podman is installed
if ! command -v $CONTAINER_RUNTIME &> /dev/null; then
  fatal "docker/podman could not be found"
fi

# Check if kind is installed
if ! command -v kind &> /dev/null; then
  fatal "kind could not be found: try make download-cli"  
fi

kind_options=""
if [[ $(is_positive ${ENABLE_INGRESS}) == "0" ]]; then
  kind_options+=" --config=$kind_ingress_config_path"
fi

# Create kind cluster
if kind get clusters | grep -q "^${KIND_CLUSTER_NAME}$"; then
  info "Kind cluster ${KIND_CLUSTER_NAME} already exists, skipping creation"
else
  info "Creating kind cluster with ingress config"  
  kind create cluster --name "$KIND_CLUSTER_NAME" $kind_options
fi

if [[ $(is_positive ${ENABLE_INGRESS}) == "0" ]]; then  
  info "Installing nginx ingress controller"
  kubectl label node/${KIND_CLUSTER_NAME}-control-plane ingress-ready=true --overwrite
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v${NGINX_INGRESS_VERSION}/deploy/static/provider/kind/deploy.yaml
fi

# Install OLM
if [[ $(is_positive ${ENABLE_OLM}) == "0" ]]; then
  info "Installing OLM"
  curl -sL https://raw.githubusercontent.com/operator-framework/operator-lifecycle-manager/refs/heads/master/deploy/upstream/quickstart/install.sh | bash -s $OLM_VERSION
fi


############# VERIFY #############
result=0

# Verify kind cluster is running
if ! retry 60 5 "kubectl cluster-info &>/dev/null" "Waiting for kind cluster to be ready"; then
    fail "Kind cluster is not running properly after 5 minutes"
    result=1
else
    success "Kind cluster is running properly"
fi

# Verify ingress if enabled
if [[ $(is_positive ${ENABLE_INGRESS}) == "0" ]]; then
    if ! retry 60 5 "kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller &>/dev/null" "Waiting for ingress controller to be ready"; then
        fail "Ingress controller is not running properly after 5 minutes"
        result=1
    else
        success "Ingress controller is running properly"
    fi
fi

# Verify OLM if enabled
if [[ $(is_positive ${ENABLE_OLM}) == "0" ]]; then
    if ! retry 60 5 "kubectl get pods -n olm -l app=olm-operator &>/dev/null" "Waiting for OLM operator to be ready"; then
        fail "OLM operator is not running properly after 5 minutes"
        result=1
    else
        success "OLM operator is running properly"
    fi
fi

############# OUTPUT #############
if [[ $result -eq 0 ]]; then
    # Get the kind kubeconfig path
    if [[ ${KUBECONFIG_PATH} != '~/.kube/config' ]]; then
      kind get kubeconfig --name ${KIND_CLUSTER_NAME} > ${KUBECONFIG_PATH}
    fi
    # Write to output environment file
    info "Writing environment variables to output file"    
    echo "KUBECONFIG_PATH=${KUBECONFIG_PATH}" >>${OUTPUT_ENV_FILE}
fi

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}
