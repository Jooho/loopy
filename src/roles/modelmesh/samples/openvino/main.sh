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
  if [[ $DEBUG == "0" ]]; then echo "The root directory is: $root_directory"; fi
else
  echo "Error: Unable to find .github folder."
fi
source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

#################################################################
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
openvino_serving_runtime_manifests=$(yq e '.role.manifests.openvino_serving_runtime' $current_dir/config.yaml)
data_connection_manifests=$(yq e '.role.manifests.data_connection' $current_dir/config.yaml)
onnx_mnist_isvc_manifests=$(yq e '.role.manifests.onnx_mnist_isvc' $current_dir/config.yaml)
input_onnx_manifests=$(yq e '.role.manifests.input_onnx' $current_dir/config.yaml)
openvino_serving_runtime_manifests_path=$current_dir/$openvino_serving_runtime_manifests
data_connection_secret_manifests_path=$current_dir/$data_connection_manifests
onnx_mnist_isvc_manifests_path=$current_dir/$onnx_mnist_isvc_manifests
input_onnx_manifests_path=$current_dir/$input_onnx_manifests

result=1 # 0 is "succeed", 1 is "fail"

if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

# Deploy a sample model
oc get ns ${TEST_NAMESPACE} >/dev/null 2>&1 || oc new-project ${TEST_NAMESPACE}
oc label namespace ${TEST_NAMESPACE} modelmesh-enabled=true --overwrite=true

sed -e \
  "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g; \
    s+%minio_region%+$MINIO_REGION+g" $data_connection_secret_manifests_path >${ROLE_DIR}/$(basename $data_connection_secret_manifests_path)

oc apply -f ${ROLE_DIR}/$(basename $data_connection_secret_manifests_path)

cp $openvino_serving_runtime_manifests_path ${ROLE_DIR}/$(basename $openvino_serving_runtime_manifests_path)
cp $onnx_mnist_isvc_manifests_path ${ROLE_DIR}/$(basename $onnx_mnist_isvc_manifests_path)
cp $input_onnx_manifests_path ${ROLE_DIR}/$(basename $input_onnx_manifests_path)

debug "oc apply -f ${ROLE_DIR}/$(basename $openvino_serving_runtime_manifests_path) -n ${TEST_NAMESPACE}"
oc apply -f ${ROLE_DIR}/$(basename $openvino_serving_runtime_manifests_path) -n ${TEST_NAMESPACE}
result=?
if [[ $result != "0" ]]; then
  error "Failed to create ServingRuntime"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

debug "oc apply -f ${ROLE_DIR}/$(basename $data_connection_secret_manifests_path) -n ${TEST_NAMESPACE}"
oc apply -f ${ROLE_DIR}/$(basename $data_connection_secret_manifests_path) -n ${TEST_NAMESPACE}
result=?
if [[ $result != "0" ]]; then
  error "Failed to create a DataConnection"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

debug "oc apply -f ${ROLE_DIR}/$(basename $onnx_mnist_isvc_manifests_path) -n ${TEST_NAMESPACE}"
oc apply -f ${ROLE_DIR}/$(basename $onnx_mnist_isvc_manifests_path) -n ${TEST_NAMESPACE}
result=?
if [[ $result != "0" ]]; then
  error "Failed to create InferenceService"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

############# VERIFY #############
result=0

info "Wait until runtime is READY"
wait_for_pods_ready "app.kubernetes.io/managed-by=modelmesh-controller" ${TEST_NAMESPACE}

temp_result=$?
if [[ $temp_result == "0" ]]; then
  success "ModelMesh Openvino runtime is running "
  result=0
else
  error "ModelMesh Openvino runtime is NOT running"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

if [[ $result == "0" ]]; then
  max_retries=3
  retry_interval=10

  modelmesh_result=""

  retry_if_http_code_is_not_200() {
    local retries=$1
    local interval=$2
    local result_var=$3
    shift 3
    local cmd=("$@")
    local result

    for ((i = 0; i < retries; i++)); do
      result=$("${cmd[@]}")
      if [[ $result == "200" ]]; then
        eval "$result_var=\"$result\""
        return 0
      else
        info "return code is not 200. retry"
        sleep $interval
      fi
    done
    eval "$result_var=\"$result\""
    return 1
  }
  info "Testing Openvino runtime mddel"

  export HOST_URL=$(oc get route example-onnx-mnist -ojsonpath='{.spec.host}' -n ${TEST_NAMESPACE})
  export HOST_PATH=$(oc get route example-onnx-mnist -ojsonpath='{.spec.path}' -n ${TEST_NAMESPACE})

  curl --silent --location --fail --show-error --insecure https://${HOST_URL}${HOST_PATH}/infer -d @${ROLE_DIR}/$(basename $input_onnx_manifests_path)

  retry_if_http_code_is_not_200 $max_retries $retry_interval modelmesh_result curl -s -o /dev/null -w "%{http_code}" -kL -H 'Content-Type: application/json' --insecure https://${HOST_URL}${HOST_PATH}/infer -d @${ROLE_DIR}/$(basename $input_onnx_manifests_path)

  # show return value
  echo ""
  info "modelmesh call result: $modelmesh_result"

  # Save output to log file
  curl -s -o /dev/null -w "%{http_code}" -kL -H 'Content-Type: application/json' --insecure https://${HOST_URL}${HOST_PATH}/infer -d @${ROLE_DIR}/$(basename $input_onnx_manifests_path)

  if [[ $modelmesh_result == "200" ]]; then
    success "Modelmesh runtime return correct data"
    result=0
  else
    error "Modelmesh runtime DID NOT return correct data"
    result=1
  fi
else
  error "Skip api call test"
  result=1
fi

############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::$result" >>${REPORT_FILE}

############# STOP WHEN RESULT IS FAIL #############
if [[ $result != "0" ]]; then
  info "The role failed"
  should_stop=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${should_stop} == "0" ]]; then
    die "[CRITICAL] STOP_WHEN_FAILED(${should_stop}) is set so it will be stoppped."
  else
    info "STOP_WHEN_FAILED(${should_stop}) is NOT set so skip this error."
  fi
fi
############# CLEAN UP #############
if [ "${KEEP_NAMESPACE}" = "true" ]; then
  echo "Keeping the namespace ${TEST_NAMESPACE}"
else
  oc delete project ${TEST_NAMESPACE}
fi
