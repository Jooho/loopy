#!/usr/bin/env bash

if [[ $DEBUG == "0" ]]
then 
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
  if [[ $DEBUG == "0" ]]; then echo "The root directory is: $root_directory" ;fi
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
done <<< "$manifests"

if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi
check_oc_status

# Deploy a sample model
oc get ns ${TEST_NAMESPACE}  > /dev/null 2>&1 ||  oc new-project ${TEST_NAMESPACE} > /dev/null 2>&1

use_data_connection=$(is_positive ${USE_DATA_CONNECTION})
if [[ ${use_data_connection} == "0" ]]
then
   sed -e \
    "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g; \
    s+%minio_region%+$MINIO_REGION+g" $data_connection_secret_manifests_path > ${ROLE_DIR}/$(basename $data_connection_secret_manifests_path)

    oc apply -f ${ROLE_DIR}/$(basename $data_connection_secret_manifests_path)
else
  if [[ ${STORAGE_CONFIG_TYPE} == "json" ]] 
  then  
    sed -e \
    "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g; \
    s+%minio_region%+$MINIO_REGION+g" $storage_config_json_manifests_path > ${ROLE_DIR}/$(basename $storage_config_json_manifests_path)

    oc apply -f ${ROLE_DIR}/$(basename $storage_config_json_manifests_path)
  else
    sed -e \
    "s+%minio_access_key_id%+$MINIO_ACCESS_KEY_ID+g; \
    s+%minio_secret_access_key%+$MINIO_SECRET_ACCESS_KEY+g; \
    s+%minio_s3_svc_url%+$MINIO_S3_SVC_URL+g; \
    s+%minio_region%+$MINIO_REGION+g" $storage_config_annotation_manifests_path > ${ROLE_DIR}/$(basename $storage_config_annotation_manifests_path)

    oc apply -f ${ROLE_DIR}/$(basename $storage_config_annotation_manifests_path)
    oc apply -f ${ROLE_DIR}/$(basename $storage_config_serviceaccount_manifests_path)
  fi
fi
caikit_type=$(echo ${CAIKIT_ARCH_TYPE}|sed 's/-/_/g')

servingruntime_manifests=$(eval "echo \${${caikit_type}_serving_runtime_manifests_path}")
inferenceservice_manifests=$(eval "echo \${${caikit_type}_isvc_${ISVC_STORAGE_PATH_TYPE}_${PROTOCOL}_manifests_path}")

cp $servingruntime_manifests  ${ROLE_DIR}/.
sed -e \
"s+%minio_default_bucket_name%+$MINIO_DEFAULT_BUCKET_NAME+g" $inferenceservice_manifests > ${ROLE_DIR}/$(basename $inferenceservice_manifests)

if [[ ${ISVC_DEPLOYMENT_MODE} == "RawDeployment" ]]
then
  yq e 'del(.metadata.annotations."serving.knative.openshift.io/enablePassthrough")' -i  ${ROLE_DIR}/$(basename $inferenceservice_manifests) 
  yq e 'del(.metadata.annotations."sidecar.istio.io/inject")' -i  ${ROLE_DIR}/$(basename $inferenceservice_manifests) 
  yq e 'del(.metadata.annotations."sidecar.istio.io/rewriteAppHTTPProbers")' -i  ${ROLE_DIR}/$(basename $inferenceservice_manifests) 
  yq eval '.metadata.annotations += {"serving.kserve.io/deploymentMode": "RawDeployment"}'  -i ${ROLE_DIR}/$(basename $inferenceservice_manifests) 
fi

if [[ ${STORAGE_CONFIG_TYPE} != "json" ]]
then
  yq -i  ".spec.predictor.serviceAccountName=\"sa\""  ${ROLE_DIR}/$(basename $inferenceservice_manifests)
fi

echo "oc apply -f ${ROLE_DIR}/$(basename $servingruntime_manifests) -n ${TEST_NAMESPACE}"
echo "oc apply -f ${ROLE_DIR}/$(basename $inferenceservice_manifests) -n ${TEST_NAMESPACE}"
oc apply -f ${ROLE_DIR}/$(basename $servingruntime_manifests) -n ${TEST_NAMESPACE}
if [[ $? != "0" ]]
then
  errorHappened=0
fi

oc apply -f ${ROLE_DIR}/$(basename $inferenceservice_manifests) -n ${TEST_NAMESPACE}
if [[ $? != "0" ]]
then
  errorHappened=0
fi

############# VERIFY #############
result=0

info "Wait until runtime is READY"
errorHappened=$(wait_for_pods_ready "serving.kserve.io/inferenceservice=${CAIKIT_ARCH_TYPE}-example-isvc-${PROTOCOL}" ${TEST_NAMESPACE})

if [[ $? == 0 ]]
then
errorHappened=$(wait_pod_containers_ready "serving.kserve.io/inferenceservice=${CAIKIT_ARCH_TYPE}-example-isvc-${PROTOCOL}" ${TEST_NAMESPACE})

  temp_result=$?
  if [[ $temp_result == "0" ]]
  then
    success "[SUCCESS] Caikit runtime is running "
    result=0
  else
    error "[FAIL] Caikit runtime is NOT running"
    errorHappened=0
  fi

  if [[ $result == "0" ]]
  then
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

        for ((i=0; i<retries; i++)); do
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
    if [[ ${ISVC_DEPLOYMENT_MODE} == "RawDeployment" ]]
    then
      export ISVC_HOSTNAME="http://localhost:8080"
      deployment_name=$(oc get deploy -n ${TEST_NAMESPACE} --no-headers|awk '{print $1}')
      oc port-forward deploy/${deployment_name} 8080:8080 &
    else
      export ISVC_HOSTNAME="https://$(oc get isvc ${CAIKIT_ARCH_TYPE}-example-isvc-${PROTOCOL} -n ${TEST_NAMESPACE} -o jsonpath='{.status.url}' | cut -d'/' -f3)"
    fi
    
    info "Testing all token in a single call"
    retry $max_retries $retry_interval single_call_result curl -s -o /dev/null -w "%{http_code}" -kL -H 'Content-Type: application/json' -d '{"model_id": "flan-t5-small-caikit", "inputs": "At what temperature does Nitrogen boil?"}' "${ISVC_HOSTNAME}/api/v1/task/text-generation"
    
    info "Testing streams of token"
    retry $max_retries $retry_interval streaming_call_result curl -s -o /dev/null -w "%{http_code}" -kL -H 'Content-Type: application/json' -d '{"model_id": "flan-t5-small-caikit", "inputs": "At what temperature does Nitrogen boil?"}' "${ISVC_HOSTNAME}/api/v1/task/server-streaming-text-generation"

    # show return value
    echo "Single call result: $single_call_result"
    echo "Streaming call result: $streaming_call_result"

    if [[ ${ISVC_DEPLOYMENT_MODE} == "RawDeployment" ]]
    then
      port_forward_pid=$(ps aux | grep "port-forward" | grep -v grep | awk '{print $2}')
      sudo kill -9 $port_forward_pid
    fi

    # Save output to log file
    curl -s -kL -H 'Content-Type: application/json' -d '{"model_id": "flan-t5-small-caikit", "inputs": "At what temperature does Nitrogen boil?"}' https://${ISVC_HOSTNAME}/api/v1/task/text-generation -o ${ROLE_DIR}/server-single-text-generation.out

    curl -s -kL -H 'Content-Type: application/json' -d '{"model_id": "flan-t5-small-caikit", "inputs": "At what temperature does Nitrogen boil?"}' https://${ISVC_HOSTNAME}/api/v1/task/server-streaming-text-generation -o ${ROLE_DIR}/server-streaming-text-generation.out
    if [[ $single_call_result == "200" || $streaming_call_result == "200" ]]
    then
      success "[SUCCESS] Caikit runtime return correct data"
      result=0
    else
      error "[FAIL] Caikit runtime DID NOT return correct data"
      result=1
      errorHappened=0
    fi
  fi
else
  error "Skip api call test"
  errorHappened=0
fi

if [[ $errorHappened == "0" ]]
then
  info "There are some errors in the role"
  stop_when_failed=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${stop_when_failed} == "0" ]]
  then
    die "STOP_WHEN_FAILED(${STOP_WHEN_FAILED}) is set and there are some errors detected so stop all process"
  else
    info "STOP_WHEN_FAILED(${STOP_WHEN_FAILED}) is NOT set so skip this error."
  fi
fi  
############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::$result" >> ${REPORT_FILE}
