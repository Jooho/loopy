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

oc delete subscription ${SUBSCRIPTION_NAME} -n ${OPERATOR_NAMESPACE}
csv_name=$(oc get csv -n ${OPERATOR_NAMESPACE} | grep ${OPERATOR_NAME}|awk '{print $1}')
oc delete csv $csv_name -n ${OPERATOR_NAMESPACE}

rm -rf ${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}

success "Clean up $role_name test"
