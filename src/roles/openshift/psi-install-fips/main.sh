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
source $root_directory/src/commons/scripts/utils.sh
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
index_role_name=$(basename $ROLE_DIR)

result=1 # 0 is "succeed", 1 is "fail"

# call the install.sh script
if [[ ${CLUSTER_NAME} != "serving-fips" ]]; then
  EXTRA_PARAMS="${EXTRA_PARAMS} -n ${CLUSTER_NAME}"
fi

info "Calling the install.sh script with the following parameters: -u ${JENKINS_USER} -t *** -j ${JENKINS_JOB_URL} ${EXTRA_PARAMS}"
${current_dir}/scripts/install.sh -u ${JENKINS_USER} -r ${ODS_RELEASE_VERSION} -p ${PRODUCT_TYPE} -t ${JENKINS_TOKEN} -j ${JENKINS_URL}/${JENKINS_JOB_URI} ${EXTRA_PARAMS}

result=?
if [[ $result != "0" ]]; then
  error "Failed to install FIPS cluster"
  result=1
  stop_when_error_happended $result $index_role_name $REPORT_FILE true
fi

# Read the file - it is downloaded by the install script
file_content=$(cat /tmp/test-variables.yml)

# Extract the values
cluster_admin_id=$(echo "$file_content" | yq -r ".OCP_ADMIN_USER.USERNAME")
cluster_admin_pw=$(echo "$file_content" | yq -r ".OCP_ADMIN_USER.PASSWORD")
cluster_console_url=$(echo "$file_content" | yq -r ".OCP_CONSOLE_URL")

# set the cluster api and retrieve the user token
cluster_name=$(echo $cluster_console_url | sed 's/.*\.apps\.\(.*\..*\)/\1/')
cluster_api_url="https://api.$cluster_name:6443"
oc login -u "${cluster_admin_id}" -p ${cluster_admin_pw} --server=${cluster_api_url} --insecure-skip-tls-verify=true >/dev/null
cluster_token=$(oc whoami -t)

############# VERIFY #############
if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

result=$?
if [[ $result == 0 ]]; then
  success "Openshift cluster login successfully done"
  result=0
else
  error "Openshift cluster login failed"
  result=1
  stop_when_error_happended $result $index_role_name $REPORT_FILE
fi

############# OUTPUT #############
echo "CLUSTER_CONSOLE_URL=${cluster_console_url}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_API_URL=${cluster_api_url}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_ID=${cluster_admin_id}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_PW=${cluster_admin_pw}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_TOKEN=${cluster_token}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_TYPE=${CLUSTER_TYPE}" >>${OUTPUT_ENV_FILE}

############ REPORT #############
echo ${index_role_name}::$result >>${REPORT_FILE}

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
