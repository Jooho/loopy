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
test_notebook=$(yq e '.role.manifests.test_notebook' $current_dir/config.yaml)
service_manifests=$(yq e '.role.manifests.service_manifests' $current_dir/config.yaml)
statefulset_manifests=$(yq e '.role.manifests.statefulset_manifests' $current_dir/config.yaml)
test_notebook_path=$current_dir/${test_notebook}
service_manifests_path=$current_dir/${service_manifests}
statefulset_manifests_path=$current_dir/${statefulset_manifests}
errorHappened=1 # 0 is true, 1 is false
## Parameters Preparation #######################################

if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

declare envs=(
  "S3_ACCESS_KEY=${MINIO_ACCESS_KEY_ID}"
  "S3_SECRET_KEY=${MINIO_SECRET_ACCESS_KEY}"
  "TEST_NAMESPACE=${TEST_NAMESPACE}"
  "CLUSTER_ADMIN_ID=${CLUSTER_ADMIN_ID}"
  "CLUSTER_ADMIN_PW=${CLUSTER_ADMIN_PW}"
  "CLUSTER_API_URL=${CLUSTER_API_URL}"
)

# Loop through the environment variables and remove the empty ones
PARAMS=""
for env in "${envs[@]}"; do
  # Split the environment variable into name and value
  IFS='=' read -r name value <<<"$env"
  # Check if the value is empty
  if [ -n "$value" ]; then
    # use only the set parameters
    PARAMS+="--param ${name}=${value} "
  fi
done
## Parameters Preparation End ###################################

# create the working namespace
oc get ns ${TEST_NAMESPACE} >/dev/null 2>&1 || oc new-project ${TEST_NAMESPACE} >/dev/null 2>&1
oc project

oc label namespace ${TEST_NAMESPACE} "opendatahub.io/dashboard=true" --overwrite=true

if [ "${USE_MINIO}" != "true" ]; then
  MINIO_S3_SVC_URL="https://s3.amazonaws.com"
  MODEL_PATH="kserve-samples/mnist/"
else
  MINIO_S3_SVC_URL=${MINIO_S3_SVC_URL}
  MODEL_PATH=${MODEL_PATH}
fi

# replacing variables in the notebook body
sed -e "s@%s3_access_key%@${MINIO_ACCESS_KEY_ID}@g" \
  -e "s@%s3_secret_key%@${MINIO_SECRET_ACCESS_KEY}@g" \
  -e "s@%test_namespace%@${TEST_NAMESPACE}@g" \
  -e "s@%cluster_admin_id%@${CLUSTER_ADMIN_ID}@g" \
  -e "s@%cluster_admin_pw%@${CLUSTER_ADMIN_PW}@g" \
  -e "s@%cluster_api_url%@${CLUSTER_API_URL}@g" \
  -e "s@%s3_url%@${MINIO_S3_SVC_URL}@g" \
  -e "s@%model_path%@${MODEL_PATH}@g" \
  ${test_notebook_path} >${ROLE_DIR}/test_notebook.ipynb

if [ "${USE_MINIO}" != "true" ]; then
  yq e 'del(.stringData.AWS_ACCESS_KEY_ID)' -i ${ROLE_DIR}/test_notebook.ipynb
  yq e 'del(.stringData.AWS_SECRET_ACCESS_KEY)' -i ${ROLE_DIR}/test_notebook.ipynb
fi

# deploy the notebook server
cp ${service_manifests_path} ${ROLE_DIR}/.
cp ${statefulset_manifests_path} ${ROLE_DIR}/.

oc apply -f ${ROLE_DIR}/statefulset.yaml
oc apply -f ${ROLE_DIR}/service.yaml

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
  errorHappened="0"
else
  result=0
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
echo ${index_role_name}::$result >>${REPORT_FILE}

############# CLEAN UP #############
if [ "${KEEP_NAMESPACE}" == "true" ]; then
  echo "Keeping the namespace ${TEST_NAMESPACE}"
else
  oc delete project ${TEST_NAMESPACE}
fi
