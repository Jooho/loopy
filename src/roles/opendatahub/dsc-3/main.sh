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
source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

#################################################################
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
dsc_manifests=$(yq e '.role.manifests.datasciencecluster_3' $current_dir/config.yaml)
dsc_manifests_path=$root_directory/$dsc_manifests

if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

if [[ ${OPENDATAHUB_TYPE} == "rhoai" ]]; then
  opendatahub_namespace="redhat-ods-applications"
  DATASCIENCECLUSTER_NAME="default-dsc"
else
  opendatahub_namespace="opendatahub"
  DATASCIENCECLUSTER_NAME="default-dsc"
fi

oc get ns $opendatahub_namespace >/dev/null 2>&1 || oc new-project $opendatahub_namespace >/dev/null 2>&1

############# Logic ############
info "Create DataScienceCluster(DSC) v2"

sed -e "s+%datasciencecluster_name%+$DATASCIENCECLUSTER_NAME+g; \
        s+%enable_kserve%+$ENABLE_KSERVE+g; \
        s+%enable_kserve_nim%+${ENABLE_KSERVE_NIM:-Removed}+g; \
        s+%modelregistry_namespace%+${MODELREGISTRY_NAMESPACE:-odh-model-registries}+g; \
        s+%enable_modelregistry%+$ENABLE_MODELREGISTRY+g; \
        s+%enable_feastoperator%+${ENABLE_FEASTOPERATOR:-Removed}+g; \
        s+%enable_trustyai%+$ENABLE_TRUSTYAI+g; \
        s+%enable_aipipelines%+${ENABLE_AIPIPELINES:-Removed}+g; \
        s+%enable_ray%+$ENABLE_RAY+g; \
        s+%enable_kueue%+$ENABLE_KUEUE+g; \
        s+%enable_workbenches%+$ENABLE_WORKBENCHES+g; \
        s+%enable_mlflowoperator%+${ENABLE_MLFLOWOPERATOR:-Removed}+g; \
        s+%enable_dashboard%+$ENABLE_DASHBOARD+g; \
        s+%enable_llamastackoperator%+${ENABLE_LLAMASTACKOPERATOR:-Removed}+g; \
        s+%enable_trainingoperator%+$ENABLE_TRAININGOPERATOR+g" $dsc_manifests_path >${ROLE_DIR}/$(basename $dsc_manifests_path)

debug "oc apply -f ${ROLE_DIR}/$(basename $dsc_manifests_path)"
oc apply -f ${ROLE_DIR}/$(basename $dsc_manifests_path)

# Custom Manifests
if [[ $ENABLE_KSERVE == "Managed" ]]; then
  if [ -n "$CUSTOM_KSERVE_MANIFESTS" ]; then
    kserve_patch_json_array+=("{\"contextDir\": \"config\",\"sourcePath\": \"overlays/odh\",\"uri\": \"$CUSTOM_KSERVE_MANIFESTS\"}")
  fi

  if [ -n "$CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS" ]; then
    kserve_patch_json_array+=("{\"contextDir\": \"config\",\"uri\": \"$CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS\"}")
  fi
fi

# Check if the kserve array is not empty
if [ ${#kserve_patch_json_array[@]} -gt 0 ]; then
  # Convert KServe array to JSON string
  kserve_patch_json_array=$(
    IFS=,
    echo "[" "${kserve_patch_json_array[*]}" "]"
  )

  # Apply the KServe JSON string to the oc patch command
  oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p="[{'op': 'add', 'path': '/spec/components/kserve/devFlags', 'value': {'manifests': $kserve_patch_json_array}}]"
else
  info "No custom manifests for the Kserve/odh manifests. Skipping oc patch."
fi

if [[ $CUSTOM_DASHBOARD_MANIFESTS != "" ]]; then
  oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p='[{"op": "add", "path": "/spec/components/dashboard/devFlags", "value": {"manifests":[{"contextDir": "manifests","uri": "'$CUSTOM_DASHBOARD_MANIFESTS'"}]}}]'
fi

############# VERIFY #############
info "Verify ROLE($index_role_name)"

result=0

if [[ ${ENABLE_KSERVE} == "Managed" ]]; then
  kserve_result=1
  odh_model_controller_result=1
  info "Checking if KServe pod is running"
  wait_for_pods_ready "control-plane=kserve-controller-manager" "${opendatahub_namespace}"
  kserve_result=$?
  wait_for_pods_ready "control-plane=odh-model-controller" "${opendatahub_namespace}"
  odh_model_controller_result=$?
  if [[ kserve_result != 1 && odh_model_controller_result != 1 ]]; then
    success "Successfully deployed KServe/odh-model-controller operator!"
    kserve_result=0
  else
    error "KServe: ${kserve_result}/ odh-model-controller: ${odh_model_controller_result}"
    error "Failed to deploy KServe operator!"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
fi

if [[ ${ENABLE_DASHBOARD} == "Managed" ]]; then
  dashboard_result=1
  info "Checking if Dashboard pods are running"
  if [[ ${OPENDATAHUB_TYPE} == "rhoai" ]]; then
    wait_for_pods_ready "deployment=rhods-dashboard" "${opendatahub_namespace}"
  else
    wait_for_pods_ready "deployment=odh-dashboard" "${opendatahub_namespace}"
  fi

  if [[ $? == 0 ]]; then
    success "Successfully deployed Dashboard!"
    dashboard_result=0
  else
    error "Failed to deploy Dashboard!"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
fi

############# OUTPUT #############

############# REPORT #############
echo ${index_role_name}::$result >>${REPORT_FILE}

if [[ ${ENABLE_KSERVE} == "Managed" ]]; then
  echo "#${index_role_name}::kserve::$kserve_result" >>${REPORT_FILE}
fi
if [[ ${ENABLE_DASHBOARD} == "Managed" ]]; then
  echo "#${index_role_name}::dashboard::$dashboard_result" >>${REPORT_FILE}
fi

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
