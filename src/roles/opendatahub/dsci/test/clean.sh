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

oc delete dsci --all --force --grace-period=0

success "Clean up $role_name test"
