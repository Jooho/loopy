#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]; then
  set -x
fi

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

### Main logic ###

############# VERIFY #############
check_oc_status
result=$?
if [[ $result == 0 ]]; then
  success "Openshift cluster login successfully done"
  result=0
else
  error "Openshift cluster login failed"
  errorHappened=0
fi

############# OUTPUT #############
echo "CLUSTER_CONSOLE_URL=${cluster_console_url}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_API_URL=${cluster_api_url}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_ID=${cluster_admin_id}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_PW=${cluster_admin_pw}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_TOKEN=${cluster_token}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_TYPE=${cluster_type}" >>${OUTPUT_ENV_FILE}

############# REPORT #############
echo ${role_name}::$? >>${REPORT_FILE}
