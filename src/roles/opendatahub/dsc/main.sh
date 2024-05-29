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
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
dsc_manifests=$(yq e '.role.manifests.datasciencecluster' $current_dir/config.yaml)
dsc_manifests_path=$root_directory/$dsc_manifests


if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi
check_oc_status

if [[ ${OPENDATAHUB_TYPE} == "rhoai" ]]
then
  opendatahub_namespace="redhat-ods-applications"
else
  opendatahub_namespace="opendatahub"
fi

oc get ns $opendatahub_namespace > /dev/null 2>&1 ||  oc new-project $opendatahub_namespace > /dev/null 2>&1
############# Logic ############
if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]]
then
  # To-Do: need to be removed soon
  # Deprecated: https://github.com/opendatahub-io/kserve/issues/138
  # if [[ $CLUSTER_TYPE == 'ROSA' || $CLUSTER_TYPE == 'rosa' ]]
  # then
  #   info "Cluster type is ROSA so it will update SMCP security"
  #   oc::wait::object::availability "oc get smcp data-science-smcp -n istio-system" 6 10
  #   oc patch smcp data-science-smcp --type merge --patch '{"spec":{"security":{"identity":{"type":"ThirdParty"}}}}' -n istio-system
  # fi

  # Wait for istio pods are running
  oc get ns istio-system > /dev/null 2>&1 ||  oc new-project istio-system > /dev/null 2>&1
  info "Wait for istio pods are running"
  wait_for_pods_ready "app=istiod" "istio-system"
  wait_for_pods_ready "app=istio-ingressgateway" "istio-system"
  wait_for_pods_ready "app=istio-egressgateway" "istio-system"

  oc wait --for=condition=ready pod -l app=istiod -n istio-system --timeout=10s
  oc wait --for=condition=ready pod -l app=istio-ingressgateway -n istio-system --timeout=10s
  oc wait --for=condition=ready pod -l app=istio-egressgateway -n istio-system --timeout=10s

  success "[SUCCESS] ISTIO pods are running properly" 
fi

info "Create DSC"

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
        s+%enable_workbenches%+$ENABLE_WORKBENCHES+g"  $dsc_manifests_path > ${ROLE_DIR}/$(basename $dsc_manifests_path)

oc apply -f ${ROLE_DIR}/$(basename $dsc_manifests_path)


# Custom Manifests
if [[ $ENABLE_KSERVE == "Managed" ]]
then
  if [ -n "$CUSTOM_KSERVE_MANIFESTS" ]; then
    kserve_patch_json_array+=("{\"contextDir\": \"config\",\"sourcePath\": \"overlays/odh\",\"uri\": \"$CUSTOM_KSERVE_MANIFESTS\"}")
  fi

  if [ -n "$CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS" ]; then
      kserve_patch_json_array+=("{\"contextDir\": \"config\",\"uri\": \"$CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS\"}")
  fi
fi

if [[ $ENABLE_MODELMESH == "Managed" ]]
then
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
    kserve_patch_json_array=$(IFS=, ; echo "[" "${kserve_patch_json_array[*]}" "]")

    # Apply the KServe JSON string to the oc patch command
    oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p="[{'op': 'add', 'path': '/spec/components/kserve/devFlags', 'value': {'manifests': $kserve_patch_json_array}}]"
else
    echo "No custom manifests for the Kserve/odh manifests. Skipping oc patch."
fi

# Check if the modelmesh array is not empty
if [ ${#mm_patch_json_array[@]} -gt 0 ]; then
    # Convert Modelmesh array to JSON string
    mm_patch_json_array=$(IFS=, ; echo "[" "${mm_patch_json_array[*]}" "]")

    # Apply the Modelmesh JSON string to the oc patch command
    oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p="[{'op': 'add', 'path': '/spec/components/modelmeshserving/devFlags', 'value': {'manifests': $mm_patch_json_array}}]"
else
    echo "No custom manifests for the Modelmesh/odh manifests. Skipping oc patch."
fi

if [[ $CUSTOM_DASHBOARD_MANIFESTS != "" ]]
  then  
    oc patch DataScienceCluster ${DATASCIENCECLUSTER_NAME} --type='json' -p='[{"op": "add", "path": "/spec/components/dashboard/devFlags", "value": {"manifests":[{"contextDir": "manifests","uri": "'$CUSTOM_DASHBOARD_MANIFESTS'"}]}}]'
  fi    

############# VERIFY #############
info "Veirfy role"
errorHappened=0 # 0 is true, s1 is false
result=0
if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]] && [[ ${ENABLE_KSERVE} == "Managed" ]]
then
  knative_result=1
  info "- Checking if KNATIVE pods are running"
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
  if [[ $? == 0 ]]
  then
    success "[SUCCESS] KNative pods are running properly" 
    knative_result=0
  else
    error "[FAIL] Failed to deploy KNative pods" 
    errorHappened=1
    result=1
  fi
fi

if [[ ${ENABLE_KSERVE} == "Managed" ]]
then
  kserve_result=1
  odh_model_controller_result=1
  info "- Checking if KServe pod is running"
  wait_for_pods_ready "control-plane=kserve-controller-manager" "${opendatahub_namespace}"
  kserve_result=$?
  wait_for_pods_ready "control-plane=odh-model-controller" "${opendatahub_namespace}"
  odh_model_controller_result=$?
  if [[ kserve_result != 1 && odh_model_controller_result != 1 ]]
  then
    success "[SUCCESS] Successfully deployed KServe//odh-model-controller operator!"
    kserve_result=0
  else
    error "KServe: ${kserve_result}/ odh-model-controller: ${odh_model_controller_result}"
    error "[FAIL] Failed to deploy KServe operator!"
    errorHappened=1
    result=1  
  fi 
fi

if [[ ${ENABLE_MODELMESH} == "Managed" ]]
then
  modelmesh_result=1
  odh_model_controller_result=1
  info "- Checking if Modelmesh pods are running"
  wait_for_pods_ready "control-plane=modelmesh-controller" "${opendatahub_namespace}"
  modelmesh_result=$?
  wait_for_pods_ready "control-plane=odh-model-controller" "${opendatahub_namespace}"
  odh_model_controller_result=$?
  if [[ modelmesh_result != 1 && odh_model_controller_result != 1 ]]
  then
    success "[SUCCESS] Successfully deployed ModelMesh/odh-model-controller operator!"
    modelmesh_result=0
  else
    error "KServe: ${kserve_result}/ odh-model-controller: ${odh_model_controller_result}"
    error "[FAIL] Failed to deploy ModelMesh operator!"
    errorHappened=1
    result=1
  fi
fi

if [[ ${ENABLE_DASHBOARD} == "Managed" ]]
then
  dashboard_result=1
  info "- Checking if Dashboard pods are running"
  wait_for_pods_ready "deployment=odh-dashboard" "${opendatahub_namespace}"
  if [[ $? == 0 ]]
  then
    success "[SUCCESS] Successfully deployed Dashboard!"
    dashboard_result=0
  else
    error "[FAIL] Failed to deploy Dashboard!"
    errorHappened=1
    result=1   
  fi
fi

if [[ $errorHappened == "1" ]]
then
  info "There are some errors in the role"
  stop_when_failed=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${stop_when_failed} == "0" ]]
  then
    die "STOP_WHEN_FAILED(${STOP_WHEN_FAILED}) is set and there are some errors detected so stop all process"
  else
    info "STOP_WHEN_FAILED(${STOP_WHEN_FAILED}) is NOT set so skip this error."
  fi
fi  
############# OUTPUT #############


############# REPORT #############
echo ${index_role_name}::$result >> ${REPORT_FILE}

if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]] && [[ ${ENABLE_KSERVE} == "Managed" ]]
then
  echo "#${index_role_name}::knative::$knative_result" >> ${REPORT_FILE}
fi
if [[ ${ENABLE_KSERVE} == "Managed" ]]
then
  echo "#${index_role_name}::kserve::$kserve_result" >> ${REPORT_FILE}
fi
if [[ ${ENABLE_MODELMESH} == "Managed" ]]
then
  echo "#${index_role_name}::modelmesh::$modelmesh_result" >> ${REPORT_FILE}
fi
if [[ ${ENABLE_DASHBOARD} == "Managed" ]]
then
  echo "#${index_role_name}::dashboard::$dashboard_result" >> ${REPORT_FILE}
fi
