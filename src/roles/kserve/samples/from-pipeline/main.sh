#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]
then
  set -x
fi

# Check if tkn command exists
if ! command -v tkn &> /dev/null
then
    echo "Tekton CLI (tkn) could not be found"
    exit 1
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

## Parameters Preparation #######################################

# Define the environment variables
if [ "${CLUSTER_TOKEN}" = "" ]; then
  if [ "${CLUSTER_ADMIN_ID}" != "" ] && [ "${CLUSTER_ADMIN_PW}" != "" ]; then
    echo "Trying to login to the cluster to get the token for user ${CLUSTER_ADMIN_ID}"
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
    CLUSTER_TOKEN=$(oc whoami -t)
  else
    echo "TOKEN, CLUSTER_ADMIN_ID and CLUSTER_ADMIN_PW are not set, please set the credentials or the token"
  fi
fi

declare envs=(
    "GIT_URL=${GIT_URL}"
    "GIT_REVISION=${GIT_REVISION}"
    "CLUSTER_API_URL=${CLUSTER_API_URL}"
    "CLUSTER_TOKEN=${CLUSTER_TOKEN}"
    "MINIO_ACCESS_KEY_ID=${MINIO_ACCESS_KEY_ID}"
    "MINIO_SECRET_ACCESS_KEY=${MINIO_SECRET_ACCESS_KEY}"
    "MINIO_S3_SVC_URL=${MINIO_S3_SVC_URL}"
    "WORKING_NAMESPACE=${WORKING_NAMESPACE}"
    "PYTHON_IMAGE=${PYTHON_IMAGE}"
    "OC_IMAGE=${OC_IMAGE}"
    "ISVC_DEPLOYMENT_VERBOSE=${ISVC_DEPLOYMENT_VERBOSE}"
    "DEFAULT_BUCKET_NAME=${DEFAULT_BUCKET_NAME}"
    "MINIO_REGION=${MINIO_REGION}"
)

# Loop through the environment variables and remove the empty ones
PARAMS=""
for env in "${envs[@]}"; do
    # Split the environment variable into name and value
    IFS='=' read -r name value <<< "$env"
    # Check if the value is empty
    if [ -n "$value" ]; then
        # use only the set parameters
        PARAMS+="--param ${name}=${value} "
    fi
done
## Parameters Preparation End ###################################

#################################################################
source $root_directory/commons/scripts/utils.sh
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
index_role_name=$(basename $ROLE_DIR)
errorHappened=1 # 0 is true, 1 is false

# create the working namespace
oc get ns ${WORKING_NAMESPACE} > /dev/null 2>&1 ||  oc new-project ${WORKING_NAMESPACE} > /dev/null 2>&1
oc project

manifests_dir="${current_dir}/manifests"
for yaml in `find ${manifests_dir} -name "*.yaml"`; do
  if [ "${yaml}" != "pvc.yaml" ]; then
    echo "Applying yaml file: $yaml"
    oc apply -f $yaml;
  fi
done

result=1
echo "Triggering the pipeline caikit-e2e-inference-pipeline with the following parameters: ${PARAMS}"
tkn pipeline start caikit-e2e-inference-pipeline  \
  ${PARAMS} \
  -w name=shared-workspace,volumeClaimTemplateFile=${manifests_dir}/pvc.yaml \
  --use-param-defaults --showlog --pipeline-timeout=30m
succeded_pipeline=$(oc get pipelinerun $(oc get pipelinerun --no-headers|awk '{print $1}') -ojsonpath='{.status.conditions[0].status}')

############# VERIFY #############
if [[ ${succeded_pipeline} != "False" ]]
then
  result="0"
else  
  errorHappened="0"
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
echo ${index_role_name}::$result >> ${REPORT_FILE}

############# CLEAN UP #############
if [ "${KEEP_NAMESPACE}" == "true" ]; then
  echo "Keeping the namespace ${WORKING_NAMESPACE}"
else
  for yaml in `find ${manifests_dir} -name "*.yaml"`; do
    echo "Deleting resource: $yaml"
    oc delete -f $yaml;
  done
  oc delete project ${WORKING_NAMESPACE}
fi
