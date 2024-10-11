#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]; then
  set -x
fi

root_directory=$1
current_dir=$2
role_name=$3
source $current_dir/test-variables.sh
source $root_directory/commons/scripts/utils.sh

# Verify
oc get dsci default-dsci
if [[ $? == 0 ]]; then
  success "Role($role_name) sanity test"
  info "Start to clean up"
  # $current_dir/clean.sh ${root_directory}  ${current_dir} ${role_name}
else
  error "Role($role_name) sanity test"
fi
