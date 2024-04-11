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

info "Delete all isvc,servingruntime,namespace"
oc delete revisions,pod,isvc,servingruntime --all -n ${TEST_NAMESPACE} --force --grace-period=0

oc delete secret storage-config

oc delete ns ${TEST_NAMESPACE} --force --grace-period=0 --wait > /dev/null 2>&1 

# oc::wait::object::availability "oc get ns ${MINIO_NAMESPACE}" 1 10
success "Clean up $role_name test"
