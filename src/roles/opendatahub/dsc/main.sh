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
source $root_directory/src/commons/scripts/utils.sh
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
dsc_manifests=$(yq e '.role.manifests.datasciencecluster' $current_dir/config.yaml)
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
if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]]; then
  # To-Do: need to be removed soon
  # Deprecated: https://github.com/opendatahub-io/kserve/issues/138
  # if [[ $CLUSTER_TYPE == 'ROSA' || $CLUSTER_TYPE == 'rosa' ]]
  # then
  #   info "Cluster type is ROSA so it will update SMCP security"
  #   oc::wait::object::availability "oc get smcp data-science-smcp -n istio-system" 6 10
  #   oc patch smcp data-science-smcp --type merge --patch '{"spec":{"security":{"identity":{"type":"ThirdParty"}}}}' -n istio-system
  # fi

  # Wait for istio pods are running
  oc get ns istio-system >/dev/null 2>&1 || oc new-project istio-system >/dev/null 2>&1
  info "Wait for istio pods are running"
  wait_for_pods_ready "app=istiod" "istio-system"
  wait_for_pods_ready "app=istio-ingressgateway" "istio-system"
  wait_for_pods_ready "app=istio-egressgateway" "istio-system"

  oc wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=10s
  oc wait --for=condition=ready pod -l app=istio-ingressgateway -n istio-system --timeout=10s
  oc wait --for=condition=ready pod -l app=istio-egressgateway -n istio-system --timeout=10s

  pass "ISTIO pods are running properly"
fi

info "Create DataScienceCluster(DSC)"

sed -e "s+%datasciencecluster_name%+$DATASCIENCECLUSTER_NAME+g; \
        s+%default_deploymentmode%+$DEFAULT_DEPLOYMENTMODE+g; \
        s+%enable_codeflare%+$ENABLE_CODEFLARE+g; \
        s+%enable_dashboard%+$ENABLE_DASHBOARD+g; \
        s+%enable_datasciencepipelines%+$ENABLE_DATASCIENCEPIPELINES+g; \
        s+%enable_kserve%+$ENABLE_KSERVE+g; \
        s+%enable_kserve_knative%+$ENABLE_KSERVE_KNATIVE+g; \
        s+%enable_modelmesh%+$ENABLE_MODELMESH+g; \
        s+%enable_ray%+$ENABLE_RAY+g; \
        s+%enable_trustyai%+$ENABLE_TRUSTYAI+g; \
        s+%enable_trainingoperator%+$ENABLE_TRAININGOPERATOR+g; \
        s+%enable_kueue%+$ENABLE_KUEUE+g; \
        s+%enable_modelregistry%+$ENABLE_MODELREGISTRY+g; \
        s+%enable_workbenches%+$ENABLE_WORKBENCHES+g" $dsc_manifests_path >${ROLE_DIR}/$(basename $dsc_manifests_path)

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

if [[ $ENABLE_MODELMESH == "Managed" ]]; then
  if [ -n "$CUSTOM_MODELMESH_MANIFESTS" ]; then
    mm_patch_json_array+=("{\"contextDir\": \"config\",\"uri\": \"$CUSTOM_MODELMESH_MANIFESTS\"}")
  fi

  if [ -n "$CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS" ]; then
    mm_patch_json_array+=("{\"contextDir\": \"config\",\"uri\": \"$CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS\"}")
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

# Check if the modelmesh array is not empty
if [ ${#mm_patch_json_array[@]} -gt 0 ]; then
  # Convert Modelmesh array to JSON string
  mm_patch_json_array=$(
    IFS=,
    echo "[" "${mm_patch_json_array[*]}" "]"
  )

  # Apply the Modelmesh JSON string to the oc patch command
  oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p="[{'op': 'add', 'path': '/spec/components/modelmeshserving/devFlags', 'value': {'manifests': $mm_patch_json_array}}]"
else
  info "No custom manifests for the Modelmesh/odh manifests. Skipping oc patch."
fi

if [[ $CUSTOM_DASHBOARD_MANIFESTS != "" ]]; then
  oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p='[{"op": "add", "path": "/spec/components/dashboard/devFlags", "value": {"manifests":[{"contextDir": "manifests","uri": "'$CUSTOM_DASHBOARD_MANIFESTS'"}]}}]'
fi

############# VERIFY #############
info "Veirfy ROLE($index_role_name)"

result=0
if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]] && [[ ${ENABLE_KSERVE} == "Managed" ]]; then
  knative_result=1
  info "Checking if KNATIVE pods are running"
  wait_for_pods_ready "app=controller" "knative-serving"
  wait_for_pods_ready "app=net-istio-controller" "knative-serving"
  wait_for_pods_ready "app=net-istio-webhook" "knative-serving"
  wait_for_pods_ready "app=autoscaler-hpa" "knative-serving"
  wait_for_pods_ready "app=webhook" "knative-serving"
  wait_for_pods_ready "app=activator" "knative-serving"
  wait_for_pods_ready "app=autoscaler" "knative-serving"

  oc wait --for=condition=ready pod -l app=controller -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=net-istio-controller -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=net-istio-webhook -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=autoscaler-hpa -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=webhook -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=activator -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=autoscaler -n knative-serving --timeout=10s
  if [[ $? == 0 ]]; then
    success "KNative pods are running properly"
    knative_result=0
  else
    error "Failed to deploy KNative pods"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
fi

if [[ ${ENABLE_KSERVE} == "Managed" ]]; then
  kserve_result=1
  odh_model_controller_result=1
  info "Checking if KServe pod is running"
  wait_for_pods_ready "control-plane=kserve-controller-manager" "${opendatahub_namespace}"
  kserve_result=$?
  wait_for_pods_ready "control-plane=odh-model-controller" "${opendatahub_namespace}"
  odh_model_controller_result=$?
  if [[ kserve_result != 1 && odh_model_controller_result != 1 ]]; then
    success "Successfully deployed KServe//odh-model-controller operator!"
    kserve_result=0
  else
    error "KServe: ${kserve_result}/ odh-model-controller: ${odh_model_controller_result}"
    error "Failed to deploy KServe operator!"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
fi

if [[ ${ENABLE_MODELMESH} == "Managed" ]]; then
  modelmesh_result=1
  odh_model_controller_result=1
  info "Checking if Modelmesh pods are running"
  wait_for_pods_ready "control-plane=modelmesh-controller" "${opendatahub_namespace}"
  modelmesh_result=$?
  wait_for_pods_ready "control-plane=odh-model-controller" "${opendatahub_namespace}"
  odh_model_controller_result=$?
  if [[ modelmesh_result != 1 && odh_model_controller_result != 1 ]]; then
    success "Successfully deployed ModelMesh/odh-model-controller operator!"
    modelmesh_result=0
  else
    error "KServe: ${kserve_result}/ odh-model-controller: ${odh_model_controller_result}"
    error "Failed to deploy ModelMesh operator!"
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

if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]] && [[ ${ENABLE_KSERVE} == "Managed" ]]; then
  echo "#${index_role_name}::knative::$knative_result" >>${REPORT_FILE}
fi
if [[ ${ENABLE_KSERVE} == "Managed" ]]; then
  echo "#${index_role_name}::kserve::$kserve_result" >>${REPORT_FILE}
fi
if [[ ${ENABLE_MODELMESH} == "Managed" ]]; then
  echo "#${index_role_name}::modelmesh::$modelmesh_result" >>${REPORT_FILE}
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
