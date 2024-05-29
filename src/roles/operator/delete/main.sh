#!/usr/bin/env bash
## INIT START ##
if [[ $DEBUG == "0" ]]
then 
  set -x 
fi  
# Get the directory where this script is located
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Traverse up the directory tree to find the .github folder
github_dir="$current_dir"
while [ ! -d "$github_dir/.git" ] && [ "$github_dir" != "/" ]; do
  github_dir="$(dirname "$github_dir")"
done
# If the .github folder is found, set root_directory
if [ -d "$github_dir/.git" ]; then
  root_directory="$github_dir"
  if [[ $DEBUG == "0" ]]; then echo "The root directory is: $root_directory"; fi
else
  echo "Error: Unable to find .github folder."
fi
## INIT END ##

#################################################################
source $root_directory/commons/scripts/utils.sh
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)

if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi

oc delete subscription ${SUBSCRIPTION_NAME} -n ${OPERATOR_NAMESPACE} --force --grace-period=0

if [[ ${OPERATOR_NAMESPACE} == 'openshift-operators' || $(is_positive "${CSV_DELETE}") == 0 ]]
then
  csv_name=$(oc get csv -n ${OPERATOR_NAMESPACE} | grep ${OPERATOR_NAME}|awk '{print $1}')
  echo "Delete CSV ${csv_name}"
  oc delete csv $csv_name -n ${OPERATOR_NAMESPACE}
fi

if [[ $(is_positive "${CATALOGSOURCE_DELETE}") == 0 ]] 
then
  info "Delete the catalogsource($CATALOGSOURCE_NAME)"
  oc delete catalogsource $CATALOGSOURCE_NAME -n $CATALOGSOURCE_NAMESPACE
fi


############# VERIFY #############
oc get subscription ${SUBSCRIPTION_NAME} -n ${OPERATOR_NAMESPACE} >> /dev/null

result=$?
if [[ $result == 1 ]]
then
  success "[SUCCESS] Operator(${OPERATOR_NAME}) is removed"
  result=0
else
  error "[FAIL] Operator(${OPERATOR_NAME}) still exist"
fi

############# OUTPUT #############

############# REPORT #############
echo ${role_name}::${OPERATOR_NAME}::$result >> ${REPORT_FILE}
