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
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
index_role_name=$(basename $ROLE_DIR)

result=1 # 0 is "succeed", 1 is "fail"
### Main logic ###
if [ ${CLUSTER_TYPE} = "FIPS" ]; then
  if [ "${EXTRA_PARAMS}" = "-h" ]; then
    ${current_dir}/scripts/uninstall.sh -h
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE true

  fi
fi

# call the install.sh script
info "Calling the uninstall.sh script with the following parameters: -u ${JENKINS_USER} -t *** -j ${JENKINS_JOB_URL} -n ${CLUSTER_NAME} ${EXTRA_PARAMS}"
${current_dir}/scripts/uninstall.sh -u ${JENKINS_USER} -t ${JENKINS_TOKEN} -j ${JENKINS_URL}/${JENKINS_JOB_URI} -n ${CLUSTER_NAME} ${EXTRA_PARAMS}

result_text=$(cat ${ROLE_DIR}/result)
if [[ $result_text == "SUCCESS" ]]; then
  success "FIPS Openshift Cluster is successfully uninstalled"
  result=0
else
  error "Failed to delete FIPS cluster(s): ${CLUSTER_NAME}"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

############# VERIFY #############
# TBD

############# OUTPUT #############

############# REPORT #############
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
