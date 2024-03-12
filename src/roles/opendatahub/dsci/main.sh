#!/usr/bin/env bash

if [[ $DEBUG == "0" ]]
then 
  set -x 
fi  

## INIT START ##
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
  if [[ $DEBUG == "0" ]]; then echo "The root directory is: $root_directory" ;fi
else
  echo "Error: Unable to find .github folder."
fi
## INIT END ##

#################################################################
source $root_directory/commons/scripts/utils.sh
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
dsci_manifests=$(yq e '.role.manifests.dsci' $current_dir/config.yaml)
dsci_manifests_path=$root_directory/$dsci_manifests

cp $dsci_manifests_path ${ROLE_DIR}/$(basename $dsci_manifests_path)

if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi
check_oc_status

oc get ns istio-system > /dev/null 2>&1 ||  oc new-project istio-system > /dev/null 2>&1

if [[ ${OPENDATAHUB_TYPE} == "rhoai" ]]
then
  opendatahub_namespace="redhat-ods-applications"
else
  opendatahub_namespace="opendatahub"
fi
yq -i ".spec.applicationsNamespace = \"${opendatahub_namespace}\"" ${ROLE_DIR}/$(basename $dsci_manifests_path)

############# Logic ############
info "Create DSCI"

if [[ ${ENABLE_MONITORING} == "Removed" ]]
then
  yq -i ".spec.monitoring.managementState = \"${ENABLE_MONITORING}\"" ${ROLE_DIR}/$(basename $dsci_manifests_path)
fi
if [[ ${ENABLE_SERVICEMESH} == "Removed" ]]
then
 yq -i ".spec.serviceMesh.managementState = \"${ENABLE_SERVICEMESH}\"" ${ROLE_DIR}/$(basename $dsci_manifests_path)
fi

oc apply -f ${ROLE_DIR}/$(basename $dsci_manifests_path)

############# VERIFY #############
result=1
dsci_count=$(oc get dsci |wc -l)
if [[ $dsci_count == 1 ]]
then
  result=0
fi

############# OUTPUT #############


############# REPORT #############
echo ${index_role_name}::create-dsci::$result >> ${REPORT_FILE}
