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

source $current_dir/test-variables.sh
source $root_directory/commons/scripts/utils.sh

role_dir=$(dirname "$current_dir")
role_name=$(yq e '.role.name' ${role_dir}/config.yaml)

rm -rf ${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}
mkdir -p ${ROLE_DIR} 
mkdir -p ${OUTPUT_DIR}
touch ${REPORT_FILE}
touch ${OUTPUT_ENV_FILE}

# Prerequisite script
oc get ns istio-system openshift-serverless redhat-ods-operator
if [[ $? != 0 ]]
then
  $current_dir/pre-requisite.sh ${root_directory} ${current_dir} ${role_name}
fi

# Target Script
${role_dir}/main.sh

# Verify Script
result=$($current_dir/verify.sh ${root_directory} ${current_dir} ${role_name})
