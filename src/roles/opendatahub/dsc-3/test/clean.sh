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


kubectl patch DataScienceCluster dsc-test -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch dsci default-dsci -p '{"metadata":{"finalizers":[]}}' --type=merge
oc delete dsci,dsc --all --force

oc delete subs rhods-operator -n redhat-ods-operator

oc delete ns opendatahub redhat-ods-monitoring redhat-ods-operator --force --grace-period=0

success "Clean up $role_name test"
