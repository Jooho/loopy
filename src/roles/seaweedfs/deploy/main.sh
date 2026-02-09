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
seaweedfs_deployment_manifests=$(yq e '.role.manifests.seaweedfs_deployment' $current_dir/config.yaml)
seaweedfs_deployment_manifests_path=$current_dir/$seaweedfs_deployment_manifests

result=1 # 0 is "succeed", 1 is "fail"
if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

oc get ns ${SEAWEEDFS_NAMESPACE} >/dev/null 2>&1 || oc create ns ${SEAWEEDFS_NAMESPACE} >/dev/null 2>&1
oc label namespace ${SEAWEEDFS_NAMESPACE} pod-security.kubernetes.io/enforce=baseline --overwrite
oc label namespace ${SEAWEEDFS_NAMESPACE} pod-security.kubernetes.io/warn=baseline --overwrite
oc label namespace ${SEAWEEDFS_NAMESPACE} pod-security.kubernetes.io/audit=baseline --overwrite

sed -e \
  "s+%access_key_id%+$ACCESS_KEY_ID+g; \
 s+%secret_access_key%+$SECRET_ACCESS_KEY+g; \
 s+%seaweedfs_namespace%+$SEAWEEDFS_NAMESPACE+g; \
 s+%seaweedfs_image%+$SEAWEEDFS_IMAGE+g" $seaweedfs_deployment_manifests_path >${ROLE_DIR}/$(basename $seaweedfs_deployment_manifests_path)

edge_enable_ssl=$(is_positive ${EDGE_ENABLE_SSL})

# Apply seaweedfs deployment manifests
oc apply -f ${ROLE_DIR}/$(basename $seaweedfs_deployment_manifests_path)

# Create route for seaweedfs
if [[ ${edge_enable_ssl} == "0" && (${CLUSTER_TYPE} == "OCP" || ${CLUSTER_TYPE} == "CRC" || ${CLUSTER_TYPE} == "ROSA") ]]; then
  oc expose service seaweedfs -n ${SEAWEEDFS_NAMESPACE} --name=s3 --port=s3
  oc expose service seaweedfs -n ${SEAWEEDFS_NAMESPACE} --name=admin-ui  --port=admin-ui
  oc expose service seaweedfs -n ${SEAWEEDFS_NAMESPACE} --name=master-ui  --port=master-ui
  oc expose service seaweedfs -n ${SEAWEEDFS_NAMESPACE} --name=filer-ui  --port=filer-ui
  oc expose service seaweedfs -n ${SEAWEEDFS_NAMESPACE} --name=volume  --port=volume
fi


############# VERIFY #############
if [[ -n ${SEAWEEDFS_IMAGE} ]]; then
  wait_for_pods_ready "app=seaweedfs" ${SEAWEEDFS_NAMESPACE} 100
else
  wait_for_pods_ready "app=seaweedfs" ${SEAWEEDFS_NAMESPACE}
fi 

debug "oc wait --for=condition=ready pod -l app=seaweedfs -n ${SEAWEEDFS_NAMESPACE} --timeout=10s"
oc wait --for=condition=ready pod -l app=seaweedfs -n ${SEAWEEDFS_NAMESPACE} --timeout=10s

result=$?
if [[ $result == 0 ]]; then
  success "SEAWEEDFS is running"
  result=0
else
  error "SEAWEEDFS is NOT running"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

############# OUTPUT #############
seaweedfs_svc_protocol="http"
seaweedfs_svc_url="seaweedfs.${SEAWEEDFS_NAMESPACE}.svc.cluster.local:9000"

if [[ ${CLUSTER_TYPE} == "OCP" || ${CLUSTER_TYPE} == "CRC" || ${CLUSTER_TYPE} == "ROSA" ]]; then
  seaweedfs_svc_url=$(oc get route seaweedfs -o jsonpath="{.spec.host}" -n ${SEAWEEDFS_NAMESPACE})
fi

echo "S3_SVC_URL=${seaweedfs_svc_protocol}://${seaweedfs_svc_url}" >>${OUTPUT_ENV_FILE}
echo "S3_DEFAULT_BUCKET_NAME=${DEFAULT_BUCKET_NAME}" >>${OUTPUT_ENV_FILE}
echo "S3_ACCESS_KEY_ID=${ACCESS_KEY_ID}" >>${OUTPUT_ENV_FILE}
echo "S3_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}" >>${OUTPUT_ENV_FILE}
echo "S3_REGION=${SEAWEEDFS_REGION}" >>${OUTPUT_ENV_FILE}

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}

############# STOP WHEN RESULT IS FAIL #############
if [[ $result != "0" ]]; then
  info "The role(${index_role_name}) failed"
  should_stop=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${should_stop} == "0" ]]; then
    die "[CRITICAL] STOP_WHEN_FAILED(${should_stop}) is set so it will be stoppped."
  else
    info "STOP_WHEN_FAILED(${should_stop}) is NOT set so skip this error."
  fi
fi
