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

info "Delete role directory"
rm -rf  ${ROLE_DIR}

# oc::wait::object::availability "oc get ns ${MINIO_NAMESPACE}" 1 10
success "Clean up $role_name test"
