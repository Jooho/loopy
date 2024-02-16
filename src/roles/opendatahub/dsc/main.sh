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
while [ ! -d "$github_dir/.github" ] && [ "$github_dir" != "/" ]; do
  github_dir="$(dirname "$github_dir")"
done

# If the .github folder is found, set root_directory
if [ -d "$github_dir/.github" ]; then
  root_directory="$github_dir"
  if [[ $DEBUG == "0" ]]; then echo "The root directory is: $root_directory" ;fi
else
  echo "Error: Unable to find .github folder."
fi
## INIT END ##

#################################################################
source $root_directory/commons/scripts/utils.sh
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

############# Logic ############
if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]]
then
  if [[ $CLUSTER_TYPE == 'ROSA' || $CLUSTER_TYPE == 'rosa' ]]
  then
    info "Cluster type is ROSA so it will update SMCP security"
    oc patch smcp data-science-smcp --type merge --patch '{"spec":{"security":{"identity":{"type":"ThirdParty"}}}}' -n istio-system
  fi

  # Wait for istio pods are running
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

############# VERIFY #############
info "Veirfy role"
result=1
if [[ ${ENABLE_KSERVE_KNATIVE} == "Managed" ]] && [[ ${ENABLE_KSERVE} == "Managed" ]]
then
  info "- Checking if KNATIVE pods are running"
  wait_for_pods_ready "app=controller" "knative-serving"
  wait_for_pods_ready "app=net-istio-controller" "knative-serving"
  wait_for_pods_ready "app=net-istio-webhook" "knative-serving"
  wait_for_pods_ready "app=autoscaler-hpa" "knative-serving"
  wait_for_pods_ready "app=domain-mapping" "knative-serving"
  wait_for_pods_ready "app=webhook" "knative-serving"
  wait_for_pods_ready "app=activator" "knative-serving"
  wait_for_pods_ready "app=autoscaler" "knative-serving"

  oc wait --for=condition=ready pod -l app=controller -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=net-istio-controller -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=net-istio-webhook -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=autoscaler-hpa -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=domain-mapping -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=webhook -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=activator -n knative-serving --timeout=10s
  oc wait --for=condition=ready pod -l app=autoscaler -n knative-serving --timeout=10s
  if [[ $? == 0 ]]
  then
    success "[SUCCESS] KNative pods are running properly" 
    result=0
  fi
fi

if [[ ${ENABLE_KSERVE} == "Managed" ]]
then
  info "- Checking if KServer pod is running"
  wait_for_pods_ready "control-plane=kserve-controller-manager" "${opendatahub_namespace}"
  if [[ $? == 0 ]]
  then
    success "[SUCCESS] Successfully deployed KServe operator!"
    result=0
  fi 
fi

if [[ ${ENABLE_MODELMESH} == "Managed" ]]
then
  info "- Checking if Modelmesh pods are running"
  wait_for_pods_ready "control-plane=modelmesh-controller" "${opendatahub_namespace}"
  wait_for_pods_ready "control-plane=odh-model-controller" "${opendatahub_namespace}"
  if [[ $? == 0 ]]
  then
    success "[SUCCESS] Successfully deployed KServe operator!"
    modelmesh_result=0
  fi
fi
############# OUTPUT #############


############# REPORT #############
echo ${role_name}::create-dsc::$result >> ${REPORT_FILE}
