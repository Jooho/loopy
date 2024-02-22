#!/usr/bin/env bash

set -e 
set -o pipefail
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
  echo "The root directory is: $root_directory"
else
  echo "Error: Unable to find .github folder."
fi
## INIT END ##

#################################################################
source $root_directory/commons/scripts/utils.sh
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)


IFS='%%' read -ra command_list <<< "${COMMANDS}"

index=1
touch ${ROLE_DIR}/commands.txt

for command in "${command_list[@]}"; do
    if [[ $command == "" ]]
    then
      continue
    fi
    echo -n "${index}::${command}::" >> ${ROLE_DIR}/commands.txt
    eval $command >> ${ROLE_DIR}/commands.txt
    echo 
    ############# REPORT #############
    echo "${role_name}::${index}::$?" >> ${REPORT_FILE}
    ((index++))
done
