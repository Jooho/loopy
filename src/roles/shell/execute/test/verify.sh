#!/usr/bin/env bash

set -e 
if [[ $DEBUG == "0" ]]
then 
  set -x 
fi  

root_directory=$1
current_dir=$2
role_name=$3
source $current_dir/test-variables.sh
source $root_directory/commons/scripts/utils.sh

#Verify
while IFS= read -r line; do
  IFS='::' read -ra ADDR <<< "$line"
  last_element=${ADDR[-1]}
  if [ "$last_element" == "0" ]; then
    success "[SUCCESS] report result is 0"
  else
    die "[FAIL] Report result is NOT 0"
  fi
done < ${REPORT_FILE}


while IFS= read -r line; do
  IFS='::' read -ra ADDR <<< "$line"
  last_element=${ADDR[-1]}
  if [[ "$last_element" == "Linux" || "$last_element" == "jhouse.example.com" ]]; then
    success "[SUCCESS] Command result is Linux,jhosue.example.com"
  else
    die "[FAIL] Command result is NOT Linux"
  fi
done < ${ROLE_DIR}/commands.txt


if [[ $? == 0 ]]
then
  success "[SUCCESS] Role($role_name) sanity test"
  info "Start to clean up"
  # $current_dir/clean.sh ${root_directory}  ${current_dir} ${role_name}
else
  error "[FAIL] Role($role_name) sanity test"
fi
