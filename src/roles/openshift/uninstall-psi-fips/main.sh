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

errorHappened=1 # 0 is true, 1 is false
### Main logic ###
if [ ${CLUSTER_TYPE} = "FIPS" ]; then
  if [ "${EXTRA_PARAMS}" = "-h" ]; then
    ${current_dir}/scripts/uninstall.sh -h
    exit 0
  fi
fi

# call the install.sh script
echo "Calling the uninstall.sh script with the following parameters: -u ${JENKINS_USER} -t *** -j ${JENKINS_JOB_URL} -n ${CLUSTER_NAME} ${EXTRA_PARAMS}"
${current_dir}/scripts/uninstall.sh -u ${JENKINS_USER} -t ${JENKINS_TOKEN} -j ${JENKINS_URL}/${JENKINS_JOB_URI} -n ${CLUSTER_NAME} ${EXTRA_PARAMS}

result=1
result_text=$(cat ${ROLE_DIR}/result)
if [[ $result_text == "SUCCESS" ]]
then
  success "[SUCCESS] FIPS Openshift Cluster is successfully uninstalled"
  result=0
else
  error "Failed to delete FIPS cluster(s): ${CLUSTER_NAME}"
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

############# VERIFY #############
# TBD

############# OUTPUT #############


############# REPORT #############
echo ${index_role_name}::$result >> ${REPORT_FILE}
