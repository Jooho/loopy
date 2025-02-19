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
## INIT END ##

#################################################################
source $root_directory/commons/scripts/utils.sh
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
manifests=$(yq e '.role.manifests' "$current_dir/config.yaml")

errorHappened=1 # 0 is true, 1 is false

while IFS=: read -r manifest_name manifest_path; do
  variable_name=$(echo "$manifest_name" | awk '{ gsub(/[^a-zA-Z0-9_]/, "", $0); print }')
  manifest_path=$(echo "$manifest_path" | awk '{$1=$1};1')
  declare "${variable_name}_manifests_path"="${current_dir}/${manifest_path}"
  temp_name=${variable_name}_manifests_path
done <<<"$manifests"

if [[ z${CLUSTER_TOKEN} != z ]]; then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi
check_oc_status

# Deploy a sample model
oc get ns ${TEST_NAMESPACE} >/dev/null 2>&1 || oc new-project ${TEST_NAMESPACE}
use_data_connection=$(is_positive ${USE_DATA_CONNECTION})
if [[ ${use_data_connection} == "0" ]]; then
  sed -e \
    "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g; \
    s+%minio_region%+$MINIO_REGION+g" $data_connection_secret_manifests_path >${ROLE_DIR}/$(basename $data_connection_secret_manifests_path)

  oc apply -f ${ROLE_DIR}/$(basename $data_connection_secret_manifests_path)
else
  if [[ ${STORAGE_CONFIG_TYPE} == "json" ]]; then
    sed -e \
      "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g; \
    s+%minio_region%+$MINIO_REGION+g" $storage_config_json_manifests_path >${ROLE_DIR}/$(basename $storage_config_json_manifests_path)

    oc apply -f ${ROLE_DIR}/$(basename $storage_config_json_manifests_path)
  else
    sed -e \
      "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_region%+$MINIO_REGION+g" $storage_config_annotation_manifests_path >${ROLE_DIR}/$(basename $storage_config_annotation_manifests_path)

    oc apply -f ${ROLE_DIR}/$(basename $storage_config_annotation_manifests_path)
    oc apply -f ${ROLE_DIR}/$(basename $storage_config_serviceaccount_manifests_path)
  fi
fi

#### Customize for Runtime
MODEL_NAME=sklearn
ISVC_NAME=sklearn-example-isvc-iris-v2-${PROTOCOL}
servingruntime_manifests=$(eval "echo \${${MODEL_NAME}_runtime_manifests_path}")
inferenceservice_manifests=$(eval "echo \${${MODEL_NAME}_isvc_iris_v2_${ISVC_STORAGE_PATH_TYPE}_${PROTOCOL}_manifests_path}")
input_data=$(eval "echo \${${MODEL_NAME}_isvc_iris_v2_input_${PROTOCOL}_manifests_path}")
grpc_predict_v2=$(eval "echo \${grpc_predict_v2_protoc_manifests_path}")

cp $servingruntime_manifests ${ROLE_DIR}/.
cp $input_data ${ROLE_DIR}/.
cp $grpc_predict_v2 ${ROLE_DIR}/.
echo $servingruntime_manifests
echo ${MODEL_NAME}_isvc_iris_v2_${ISVC_STORAGE_PATH_TYPE}_${PROTOCOL}_manifests_path
sed -e "s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g" $inferenceservice_manifests >${ROLE_DIR}/$(basename $inferenceservice_manifests)

if [[ ${ISVC_DEPLOYMENT_MODE} == "RawDeployment" ]]; then
  yq e 'del(.metadata.annotations."serving.knative.openshift.io/enablePassthrough")' -i ${ROLE_DIR}/$(basename $inferenceservice_manifests)
  yq e 'del(.metadata.annotations."sidecar.istio.io/inject")' -i ${ROLE_DIR}/$(basename $inferenceservice_manifests)
  yq e 'del(.metadata.annotations."sidecar.istio.io/rewriteAppHTTPProbers")' -i ${ROLE_DIR}/$(basename $inferenceservice_manifests)
  yq eval '.metadata.annotations += {"serving.kserve.io/deploymentMode": "RawDeployment"}' -i ${ROLE_DIR}/$(basename $inferenceservice_manifests)
  yq eval '.metadata.annotations += {"serving.kserve.io/autoscalerClass": "external"}' -i ${ROLE_DIR}/$(basename $inferenceservice_manifests)
  yq eval '.metadata.labels += {"networking.kserve.io/visibility": "exposed"}' -i ${ROLE_DIR}/$(basename $inferenceservice_manifests)
fi

if [[ ${STORAGE_CONFIG_TYPE} != "json" ]]; then
  yq -i ".spec.predictor.serviceAccountName=\"sa\"" ${ROLE_DIR}/$(basename $inferenceservice_manifests)
fi

echo "oc apply -f ${ROLE_DIR}/$(basename $servingruntime_manifests) -n ${TEST_NAMESPACE}"
echo "oc apply -f ${ROLE_DIR}/$(basename $inferenceservice_manifests) -n ${TEST_NAMESPACE}"
oc apply -f ${ROLE_DIR}/$(basename $servingruntime_manifests) -n ${TEST_NAMESPACE}
if [[ $? != "0" ]]; then
  errorHappened=0
fi

oc apply -f ${ROLE_DIR}/$(basename $inferenceservice_manifests) -n ${TEST_NAMESPACE}
if [[ $? != "0" ]]; then
  errorHappened=0
fi

############# VERIFY #############
result=0

info "Wait until runtime is READY"
errorHappened=$(wait_for_pods_ready "serving.kserve.io/inferenceservice=${ISVC_NAME}" ${TEST_NAMESPACE})

if [[ $? == 0 ]]; then
  errorHappened=$(wait_pod_containers_ready "serving.kserve.io/inferenceservice=${ISVC_NAME}" ${TEST_NAMESPACE})

  temp_result=$?
  if [[ $temp_result == "0" ]]; then
    success "${MODEL_NAME} runtime is running "
    result=0
  else
    error "${MODEL_NAME} runtime is NOT running"
    errorHappened=0
  fi

  if [[ $result == "0" ]]; then
    max_retries=3
    retry_interval=10

    single_call_result=""
    streaming_call_result=""

    retry() {
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
          info "return code($result) is not 200. retry"
          sleep $interval
        fi
      done
      eval "$result_var=\"$result\""
      return 1
    }

    retry_grpc() {
      local retries=$1
      local interval=$2
      local result_var=$3
      shift 3
      local cmd=("$@")
      local result

      for ((i = 0; i < retries; i++)); do
        result=$("${cmd[@]}")
        result=$(echo $result | jq .ready)

        if [[ $result == "true" ]]; then
          eval "$result_var=\"$result\""
          return 0
        else
          info "Service is Not Ready($result). retry"
          sleep $interval
        fi
      done
      eval "$result_var=\"$result\""
      return 1
    }

    # Setup for testing
    export TLS_ENALBED=false

    if [[ ${ISVC_DEPLOYMENT_MODE} == "RawDeployment" ]]; then
      export HTTPS_PROTOCOL="http"
      export ISVC_HOSTNAME="localhost:8080"
      deployment_name=$(oc get deploy -n ${TEST_NAMESPACE} --no-headers | grep ${PROTOCOL} | awk '{print $1}')

      if [[ ${PROTOCOL} == "rest" ]]; then
        oc port-forward deploy/${deployment_name} 8080:8080 &
      else
        oc port-forward deploy/${deployment_name} 8081:8081 &
        ISVC_HOSTNAME="localhost:8081"
      fi
    else
      export HTTPS_PROTOCOL="$(echo https://sklearn-example-isvc-iris-v2-rest-kserve-demo.apps.rosa.jooho.n1ai.p3.openshiftapps.com | cut -d':' -f1)"
      export ISVC_HOSTNAME="$(oc get isvc ${ISVC_NAME} -n ${TEST_NAMESPACE} -o jsonpath='{.status.url}' | cut -d'/' -f3)"

      if [[ ${PROTOCOL} == "grpc" ]]; then
        ISVC_HOSTNAME="${ISVC_HOSTNAME}:443"
      fi

      if [[ ${HTTPS_PROTOCOL} == 'https' ]]; then
        TLS_ENALBED=true
      fi
    fi

    if [[ ${TLS_ENALBED} == true ]]; then
      export HTTPS_PROTOCOL="https"
      export GRPC_TLS_OPTION='-insecure'
      export REST_TLS_OPTION='-k'
    else
      export HTTPS_PROTOCOL="http"
      export GRPC_TLS_OPTION='-plaintext'
      export REST_TLS_OPTION=''
    fi

    # Send a request
    info "Testing ${ISVC_NAME}: URL($ISVC_HOSTNAME)"

    if [[ ${PROTOCOL} == "rest" ]]; then
      echo "curl -s -o /dev/null -w "%{http_code}" -kL -H 'Content-Type: application/json' -d @${input_data} ${HTTPS_PROTOCOL}://${ISVC_HOSTNAME}/v2/models/${ISVC_NAME}/infer"

      retry $max_retries $retry_interval model_result curl -s -o /dev/null -w "%{http_code}" ${REST_TLS_OPTION} -L -H 'Content-Type: application/json' -d @${input_data} "${HTTPS_PROTOCOL}://${ISVC_HOSTNAME}/v2/models/${ISVC_NAME}/infer"

      # Save output to log file
      curl -s ${REST_TLS_OPTION} -L -H 'Content-Type: application/json' -d @${input_data} ${HTTPS_PROTOCOL}://${ISVC_HOSTNAME}/v2/models/${ISVC_NAME}/infer -o ${ROLE_DIR}/model-result.out
    else
      echo "grpcurl ${GRPC_TLS_OPTION} -import-path ${ROLE_DIR}  -proto  grpc_predict_v2.proto  -d @  ${ISVC_HOSTNAME}  inference.GRPCInferenceService.ModelInfer <<< ${input_data})"

      retry_grpc $max_retries $retry_interval model_result grpcurl ${GRPC_TLS_OPTION} -import-path ${ROLE_DIR} -proto grpc_predict_v2.proto ${ISVC_HOSTNAME} inference.GRPCInferenceService.ServerReady

      # Save output to log file
      grpcurl ${GRPC_TLS_OPTION} -import-path ${ROLE_DIR} -proto grpc_predict_v2.proto -d @ ${ISVC_HOSTNAME} inference.GRPCInferenceService.ModelInfer <<<$(cat ${input_data}) >${ROLE_DIR}/model-result.out

      model_result=$?
    fi

    # show return value
    echo "Model($ISVC_NAME) call result: $model_result"

    # Clean up
    if [[ ${ISVC_DEPLOYMENT_MODE} == "RawDeployment" ]]; then
      port_forward_pid=$(ps aux | grep "port-forward" | grep ${PROTOCOL} | grep -v grep | awk '{print $2}')
      sudo kill -9 $port_forward_pid
    fi

    if [[ $model_result == "200" ]] || [[ $model_result == 0 ]]; then
      success "${MODEL_NAME} runtime return correct data"
      result=0
    else
      error "${MODEL_NAME} runtime DID NOT return correct data"
      result=1
      errorHappened=0
    fi
  fi
else
  error "Skip api call test"
  errorHappened=0
fi

if [[ $errorHappened == "0" ]]; then
  info "There are some errors in the role"
  stop_when_failed=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${stop_when_failed} == "0" ]]; then
    die "STOP_WHEN_FAILED(${STOP_WHEN_FAILED}) is set and there are some errors detected so stop all process"
  else
    info "STOP_WHEN_FAILED(${STOP_WHEN_FAILED}) is NOT set so skip this error."
  fi
fi
############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::$result" >>${REPORT_FILE}

############# CLEAN UP #############
if [ "${KEEP_NAMESPACE}" == "true" ]; then
  echo "Keeping the namespace ${TEST_NAMESPACE}"
else
  oc delete project ${TEST_NAMESPACE}
fi
