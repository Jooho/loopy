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
ROLE_DIR=$root_directory/src/roles/kserve/notebook/
## Parameters Preparation #######################################

# Define the environment variables
if [ "${CLUSTER_ADMIN_ID}" != "" ] && [ "${CLUSTER_ADMIN_PW}" != "" ]; then
  echo "Trying to login to the cluster to get the token for user ${CLUSTER_ADMIN_ID}"
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
else
  echo "TOKEN, CLUSTER_ADMIN_ID and CLUSTER_ADMIN_PW are not set, please set the credentials or the token"
fi

declare envs=(
    "S3_ACCESS_KEY=${S3_ACCESS_KEY}"
    "S3_SECRET_KEY=${S3_SECRET_KEY}"
    "TEST_NAMESPACE=${TEST_NAMESPACE}"
    "CLUSTER_ADMIN_ID=${CLUSTER_ADMIN_ID}"
    "CLUSTER_ADMIN_PW=${CLUSTER_ADMIN_PW}"
    "CLUSTER_API_URL=${CLUSTER_API_URL}"
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


# create the working namespace
oc get ns ${TEST_NAMESPACE} > /dev/null 2>&1 ||  oc new-project ${TEST_NAMESPACE} > /dev/null 2>&1
oc project

oc label namespace ${TEST_NAMESPACE} "opendatahub.io/dashboard=true" --overwrite=true


if [ "${USE_MINIO}" == "true" ]; then 
  S3_URL="https://s3.amazonaws.com"
else 
  S3_URL=${MINIO_URL}
fi 

# replacing variables in the notebook body
sed -e "s@%s3_access_key%@${S3_ACCESS_KEY}@g" \
    -e "s@%s3_secret_key%@${S3_SECRET_KEY}@g" \
    -e "s@%test_namespace%@${TEST_NAMESPACE}@g" \
    -e "s@%cluster_admin_id%@${CLUSTER_ADMIN_ID}@g" \
    -e "s@%cluster_admin_pw%@${CLUSTER_ADMIN_PW}@g" \
    -e "s@%cluster_api_url%@${CLUSTER_API_URL}@g" \
    -e "s@%s3_url%@${S3_URL}@g" \
    ${ROLE_DIR}/manifests/kserve_notebook.ipynb > ${ROLE_DIR}/test_notebook.ipynb


# deploy the notebook server
oc apply -f ${ROLE_DIR}/manifests/statefulset.yaml
oc apply -f ${ROLE_DIR}/manifests/service.yaml

wait_for_pods_ready "app=notebook" ${TEST_NAMESPACE}

# copy the resuling notebook to the notebook server pod
oc cp ${ROLE_DIR}/test_notebook.ipynb notebook-0:/opt/app-root/src -c notebook 

# install the required package 
oc exec notebook-0 -- /bin/sh -c "python3 -m pip install papermill"

# use papermill to execute the copied notebook
oc exec notebook-0 -- /bin/sh -c "python3 -m papermill test_notebook.ipynb test_output.ipynb --kernel python3 --stderr-file test_error.txt"

############# VERIFY #############
output=$(oc exec notebook-0 -- /bin/sh -c "cat test_error.txt | grep error")

# Check if the output is empty (no matches)
if [ -z "$output" ]; then
    result=1
else
    result=0
fi
############# OUTPUT #############
############# REPORT #############
echo ${index_role_name}::$result >> ${REPORT_FILE}

############# CLEAN UP #############
if [ "${KEEP_NAMESPACE}" = "true" ]; then
  echo "Keeping the namespace ${TEST_NAMESPACE}"
else
  oc delete project ${TEST_NAMESPACE}
fi
