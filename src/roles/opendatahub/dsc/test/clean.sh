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

oc delete dsc dsc-test --all --force --grace-period=0

oc delete isvc,servingruntime,pod --all -n kserve-demo --force
oc delete ns kserve-demo minio --force --grace-period=0
oc delete all --all --force --grace-period=0 -n opendatahub
oc delete dsci,dsc --all --force
oc delete subs serverless-operator -n rhoai-serverless
oc delete subs servicemeshoperator -n openshift-operators 
oc delete subs opendatahub-operator -n openshift-operators

success "Clean up $role_name test"
