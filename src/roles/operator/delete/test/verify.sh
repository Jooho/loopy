#!/usr/bin/env bash

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
oc get pod -n $OPERATOR_NAMESPACE|grep $OPERATOR_NAME|awk '{print $1}'

if [[ $? == 0 ]]
then
  success "[SUCCESS] Role($role_name) sanity test"
else
  error "[FAIL] Role($role_name) sanity test"
fi
