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

### Main logic ###
if [ ${CLUSTER_TYPE} = "FIPS" ]; then
  if [ "${EXTRA_PARAMS}" = "-h" ]; then
    ${current_dir}/psi-fips/uninstall.sh -h
    exit 0
  fi

  # call the install.sh script
  echo "Calling the uninstall.sh script with the following parameters: -u ${JENKINS_USER} -t *** -j ${JENKINS_JOB_URL} -n ${TEST_CLUSTERS} ${EXTRA_PARAMS}"
  ${current_dir}/psi-fips/uninstall.sh -u ${JENKINS_USER} -t ${JENKINS_TOKEN} -j ${JENKINS_JOB_URL} -n ${TEST_CLUSTERS} ${EXTRA_PARAMS}

  if [ $? -ne 0 ]; then
    error "Failed to delete FIPS cluster(s): ${TEST_CLUSTERS}"
    exit 1
  fi
fi

############# VERIFY #############


############# OUTPUT #############


############# REPORT #############
echo ${role_name}::${uninstall-cluster}::$? >> ${REPORT_FILE}
