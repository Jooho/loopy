#!/usr/bin/env bash

if [[ $DEBUG == "0" ]]
then 
  set -x 
fi  

root_directory=$1
current_dir=$2
role_name=$3
source $current_dir/test-variables.sh
source $root_directory/src/commons/scripts/utils.sh

info "Delete seaweedfs pod"
oc delete pod seaweedfs -n ${SEAWEEDFS_NAMESPACE}

info "Delete namespace ${SEAWEEDFS_NAMESPACE}"
oc delete ns ${SEAWEEDFS_NAMESPACE} --force --grace-period=0 --wait > /dev/null 2>&1 

# oc::wait::object::availability "oc get ns ${MINIO_NAMESPACE}" 1 10
success "Clean up $role_name test"
