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
pod_name=$(oc get pod -n $MINIO_NAMESPACE|grep minio|awk '{print $1}')

oc wait --for=condition=ready pod/${pod_name} -n $MINIO_NAMESPACE --timeout=10s

if [[ $? == 0 ]]
then
  success "[SUCCESS] Role($role_name) sanity test"
  info "Start to clean up"
  # $current_dir/clean.sh ${root_directory}  ${current_dir} ${role_name}
else
  error "[FAIL] Role($role_name) sanity test"
fi
