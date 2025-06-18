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
  echo "Error: Unable to find .github folder."
fi
source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

#################################################################
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
route_manifests_dir=$(yq e '.role.manifests.route_manifests_dir' $current_dir/config.yaml)
kvcache_manifests_dir=$(yq e '.role.manifests.kvcache_manifests_dir' $current_dir/config.yaml)
scheduler_manifests_dir=$(yq e '.role.manifests.scheduler_manifests_dir' $current_dir/config.yaml)
prefill_manifests_dir=$(yq e '.role.manifests.prefill_manifests_dir' $current_dir/config.yaml)
decode_manifests_dir=$(yq e '.role.manifests.decode_manifests_dir' $current_dir/config.yaml)
test_requests_file=$(yq e '.role.files.test_requests_file' $current_dir/config.yaml)
test_requests_file_path=$current_dir/$test_requests_file

# Copy all required manifests to the temp directory
cp -R ${current_dir}/manifests ${ROLE_DIR}/.

# Update Namespace
find ${ROLE_DIR}/manifests -type f -exec sed -i  "s+%test_namespace%+$TEST_NAMESPACE+g" {} +
# Update Model ID
find ${ROLE_DIR}/manifests -type f -exec sed -i  "s+%model_id%+$MODEL_ID+g" {} +

# Set simulator manifests foler if USE_SIMULATOR is true
is_simulator_enabled=$(is_positive $USE_SIMULATOR)
if [[ $is_simulator_enabled == "0" ]]; then
  echo "Use VLLM Simulator"
  prefill_manifests_dir=$(yq e '.role.manifests.simulator_prefill_manifests_dir' $current_dir/config.yaml)
prefill_manifests_dir_path=$current_dir/$prefill_manifests_dir
  decode_manifests_dir=$(yq e '.role.manifests.simulator_decode_manifests_dir' $current_dir/config.yaml)  
decode_manifests_dir_path=$current_dir/$decode_manifests_dir
PORT=80
fi

# Install CRDs
oc apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/${GATEWAY_API_CRD_VERSION}/experimental-install.yaml
oc apply -f https://github.com/kubernetes-sigs/gateway-api-inference-extension/releases/download/${GIE_CRD_VERSION}/manifests.yaml

# Install GATEWAY API Implementation
case $GIE_BACKEND in
  "istio")
    helm upgrade -i istio-base oci://$ISTIO_HUB/charts/base --version $ISTIO_HUB_VERSION -n istio-system --create-namespace
    helm upgrade -i istiod oci://$ISTIO_HUB/charts/istiod --version $ISTIO_HUB_VERSION -n istio-system --set tag=$ISTIO_HUB_VERSION --set hub=$ISTIO_HUB --wait
    ;;
  *)
    fatal "Invalid GIE backend: $GIE_BACKEND"
    exit 1
    ;;
esac

# Create namespace
info "Create namespace ${TEST_NAMESPACE}"
oc create namespace ${TEST_NAMESPACE}

# Deploy KVCache
info "Deploy KVCache"
oc apply -f ${ROLE_DIR}/${kvcache_manifests_dir}

# Deploy Scheduler
info "Deploy Scheduler"
oc apply -f ${ROLE_DIR}/${scheduler_manifests_dir}

# Deploy Prefill
info "Deploy Prefill"
oc apply -f ${ROLE_DIR}/${prefill_manifests_dir}

# Deploy Decode
info "Deploy Decode"
oc apply -f ${ROLE_DIR}/${decode_manifests_dir}/

# Deploy Route
info "Deploy Route"
oc apply -f ${ROLE_DIR}/${route_manifests_dir}

# Wating Pods to be ready
info "Wating Pods to be ready"
oc wait --for=condition=ready pod -l llm-d.ai/epp=meta-llama-llama-3-2-3b-instruct-epp -n ${TEST_NAMESPACE} --timeout=10m
oc wait --for=condition=ready pod -l llm-d.ai/model=meta-llama-llama-3-2-3b-instruct -n ${TEST_NAMESPACE} --timeout=10m
oc wait --for=condition=ready pod -l gateway.istio.io/managed=istio.io-gateway-controller -n ${TEST_NAMESPACE} --timeout=10m
oc wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n ${TEST_NAMESPACE} --timeout=10m

############# VERIFY #############
result=0

$test_requests_file_path -n ${TEST_NAMESPACE} -m ${MODEL_ID}
if [[ $? -ne 0 ]]; then
  result=1
fi

############# OUTPUT #############


############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}
