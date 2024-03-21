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
index_role_name=$(basename $ROLE_DIR)

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

# create the working namespace
oc new-project ${WORKING_NAMESPACE}

manifests_dir="${current_dir}/manifests"
for yaml in `find ${manifests_dir} -name "*.yaml"`; do
  echo "Applying yaml file: $yaml"
  oc apply -f $yaml;
done

echo "Triggering the pipeline caikit-e2e-inference-pipeline with the following parameters: ${PARAMS}"
tkn pipeline start caikit-e2e-inference-pipeline  \
  ${PARAMS} \
  -w name=shared-workspace,volumeClaimTemplateFile=${current_dir}/pvc.yaml \
  --use-param-defaults --showlog

############# VERIFY #############
if [ $? -ne 0 ]; then
  result="1"
else
  result="0"
fi

############# OUTPUT #############
if [ "${KEEP_NAMESPACE}" = "true" ]; then
  echo "Keeping the namespace ${WORKING_NAMESPACE}"
else
  for yaml in `find ${manifests_dir} -name "*.yaml"`; do
    echo "Deleting resource: $yaml"
    oc delete -f $yaml;
  done
  oc delete project ${WORKING_NAMESPACE}
fi
############# REPORT #############
echo ${index_role_name}::${caikit-pipeline}::$result >> ${REPORT_FILE}
