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
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
index_role_name=$(basename $ROLE_DIR)

### Main logic ###
# call the install.sh script
echo "Calling the install.sh script with the following parameters: -u ${JENKINS_USER} -t *** -j ${JENKINS_JOB_URL} ${EXTRA_PARAMS}"
${current_dir}/scripts/install.sh -u ${JENKINS_USER} -t ${JENKINS_TOKEN} -j ${JENKINS_JOB_URL} ${EXTRA_PARAMS}

if [ $? -ne 0 ]; then
  error "Failed to install FIPS cluster"
  exit 1
else
  # Read the file - it is downloaded by the install script
  file_content=$(cat /tmp/test-variables.yml)

  # Extract the values
  cluster_admin_id=$(echo "$file_content" | yq -r ".OCP_ADMIN_USER.USERNAME")
  cluster_admin_pw=$(echo "$file_content" | yq -r ".OCP_ADMIN_USER.PASSWORD")
  cluster_console_url=$(echo "$file_content" | yq -r ".OCP_CONSOLE_URL")

  # set the cluster api and retrieve the user token
  cluster_name=$(echo $cluster_console_url | sed 's/.*\.apps\.\(.*\)\..*/\1/')
  cluster_api_url="https://api.$cluster_name"
  oc login -u "${cluster_admin_id}" -p ${cluster_admin_pw} --server=${cluster_api_url} --insecure-skip-tls-verify=true >/dev/null
  cluster_token=$(oc whoami -t)
fi

############# VERIFY #############
check_oc_status
result=$?
if [[ $result == 0 ]]
then
  success "[SUCCESS] Openshift cluster login successfully done"
  result=0
else
  error "[FAIL] Openshift cluster login failed"
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
echo "CLUSTER_CONSOLE_URL=${cluster_console_url}" >> ${OUTPUT_ENV_FILE}
echo "CLUSTER_API_URL=${cluster_api_url}" >> ${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_ID=${cluster_admin_id}" >> ${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_PW=${cluster_admin_pw}" >> ${OUTPUT_ENV_FILE}
echo "CLUSTER_TOKEN=${cluster_token}" >> ${OUTPUT_ENV_FILE}
echo "CLUSTER_TYPE=${cluster_type}" >> ${OUTPUT_ENV_FILE}

############# REPORT #############
echo ${index_role_name}::$result >> ${REPORT_FILE}
