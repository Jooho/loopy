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

#Verify
openssl x509 -in ${ROLE_DIR}/${CERT_NAME} -text
openssl verify -CAfile ${ROLE_DIR}/${ROOT_CA_CERT_NAME} ${ROLE_DIR}/${CERT_NAME}

if [[ $? == 0 ]]
then
  success "[SUCCESS] Role($role_name) sanity test"
  info "Start to clean up"
  # $current_dir/clean.sh ${root_directory}  ${current_dir} ${role_name}
else
  error "[FAIL] Role($role_name) sanity test"
fi
