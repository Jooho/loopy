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

success "Clean up $role_name test"
