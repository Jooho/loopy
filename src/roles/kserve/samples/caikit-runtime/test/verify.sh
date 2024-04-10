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

echo
info "Wait until runtime is READY"

wait_for_pods_ready "serving.kserve.io/inferenceservice=caikit-tgis-example-isvc-rest" "${TEST_NAMESPACE}"
oc wait --for=condition=ready pod -l serving.kserve.io/inferenceservice=caikit-tgis-example-isvc-rest -n ${TEST_NAMESPACE} --timeout=300s

echo
info "Testing all token in a single call"
echo

export KSVC_HOSTNAME=$(oc get ksvc caikit-tgis-example-isvc-rest-predictor -n ${TEST_NAMESPACE} -o jsonpath='{.status.url}' | cut -d'/' -f3)
curl -kL -H 'Content-Type: application/json' -d '{"model_id": "flan-t5-small-caikit", "inputs": "At what temperature does Nitrogen boil?"}' https://${KSVC_HOSTNAME}/api/v1/task/text-generation

echo
info "Testing streams of token"
echo

curl -kL -H 'Content-Type: application/json' -d '{"model_id": "flan-t5-small-caikit", "inputs": "At what temperature does Nitrogen boil?"}' https://${KSVC_HOSTNAME}/api/v1/task/server-streaming-text-generation



if [[ $? == 0 ]]
then
  success "[SUCCESS] Role($role_name) sanity test"
  info "Start to clean up"
  # $current_dir/clean.sh ${root_directory}  ${current_dir} ${role_name}
else
  error "[FAIL] Role($role_name) sanity test"
fi
