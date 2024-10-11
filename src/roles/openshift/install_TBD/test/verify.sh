#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]; then
  set -x
fi

root_directory=$1
current_dir=$2
role_name=$3
source $current_dir/test-variables.sh
source $root_directory/commons/scripts/utils.sh
source $OUTPUT_DIR/$OUTPUT_ENV_FILE
echo $OUTPUT_DIR/$OUTPUT_ENV_FILE

# Verify
info "login to cluster using token"
oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
check_if_result $?

info "check if the cluster is stable"
oc adm wait-for-stable-cluster --minimum-stable-period 1s
check_if_result $?

info "login to cluster using id/pw"
oc login -u ${CLUSTER_ADMIN_ID} -p ${CLUSTER_ADMIN_PW} ${CLUSTER_API_URL}
check_if_result $?

if [[ $? == 0 ]]; then
  success "Role($role_name) sanity test"
  # info "Start to clean up"
  # $current_dir/clean.sh ${root_directory}  ${current_dir} ${role_name}
else
  error "Role($role_name) sanity test"
fi
