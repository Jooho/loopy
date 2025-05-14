#!/usr/bin/env bash
## INIT START ##
if [[ $DEBUG == "0" ]]; then
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
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
dsci_manifests=$(yq e '.role.manifests.dsci' $current_dir/config.yaml)
dsci_manifests_path=$root_directory/$dsci_manifests

result=1 # 0 is "succeed", 1 is "fail"

cp $dsci_manifests_path ${ROLE_DIR}/$(basename $dsci_manifests_path)

if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi
if [[ ${ENABLE_SERVICEMESH} == "Managed" ]]; then
  oc get ns ${ISTIO_NAMESPACE} >/dev/null 2>&1 || oc new-project ${ISTIO_NAMESPACE} >/dev/null 2>&1
fi

if [[ ${OPENDATAHUB_TYPE} == "opendatahub" ]]; then
  APPLICATION_NAMESPACE="opendatahub"
else
  APPLICATION_NAMESPACE="redhat-ods-applications"
fi

oc get ns ${APPLICATION_NAMESPACE} >/dev/null 2>&1 || oc new-project ${APPLICATION_NAMESPACE} >/dev/null 2>&1

############# Logic ############
info "Create DataScienceClusterInitialize(DSCI)"
sed -e "s+%dsci_name%+$DSCI_NAME+g; \
        s+%monitoring_namespace%+$MONITORING_NAMESPACE+g; \
        s+%application_namespace%+$APPLICATION_NAMESPACE+g; \
        s+%enable_monitoring%+$ENABLE_MONITORING+g; \
        s+%istio_namespace%+$ISTIO_NAMESPACE+g; \
        s+%enable_servicemesh%+$ENABLE_SERVICEMESH+g; \
        s+%enable_trustedCABundle%+$ENABLE_TRUSTEDCABUNDLE+g" $dsci_manifests_path >${ROLE_DIR}/$(basename $dsci_manifests_path)

debug "oc apply -f ${ROLE_DIR}/$(basename $dsci_manifests_path)"
oc apply -f ${ROLE_DIR}/$(basename $dsci_manifests_path)

############# VERIFY #############
result=1
dsci_count=$(oc get dsci --no-headers | wc -l)
if [[ $dsci_count == 1 ]]; then
  result=0
fi

############# OUTPUT #############

############# REPORT #############
echo ${index_role_name}::$result >>${REPORT_FILE}

############# STOP WHEN RESULT IS FAIL #############
if [[ $result != "0" ]]; then
  info "The role failed"
  should_stop=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${should_stop} == "0" ]]; then
    die "[CRITICAL] STOP_WHEN_FAILED(${should_stop}) is set so it will be stoppped."
  else
    info "STOP_WHEN_FAILED(${should_stop}) is NOT set so skip this error."
  fi
fi
