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
minio_deployment_manifests=$(yq e '.role.manifests.minio_deployment' $current_dir/config.yaml)
minio_deployment_manifests_path=$current_dir/$minio_deployment_manifests

result=1 # 0 is "succeed", 1 is "fail"
if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

oc get ns ${MINIO_NAMESPACE} >/dev/null 2>&1 || oc create ns ${MINIO_NAMESPACE} >/dev/null 2>&1
oc label namespace ${MINIO_NAMESPACE} pod-security.kubernetes.io/enforce=baseline --overwrite
oc label namespace ${MINIO_NAMESPACE} pod-security.kubernetes.io/warn=baseline --overwrite
oc label namespace ${MINIO_NAMESPACE} pod-security.kubernetes.io/audit=baseline --overwrite

sed -e \
  "s+%access_key_id%+$ACCESS_KEY_ID+g; \
 s+%secret_access_key%+$SECRET_ACCESS_KEY+g; \
 s+%minio_namespace%+$MINIO_NAMESPACE+g; \
 s+%minio_image%+$MINIO_IMAGE+g" $minio_deployment_manifests_path >${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

enable_ssl=$(is_positive ${ENABLE_SSL})
if [[ ${enable_ssl} == "0" ]]; then
  info "MINIO SSL Enabled"
  info "ROOT_CA_CERT_FILE_PATH: ${ROOT_CA_CERT_FILE_PATH}"
  if [[ ! -n ${ROOT_CA_CERT_FILE_PATH} || ! -n ${CERT_FILE_PATH} || ! -n ${KEY_FILE_PATH} ]]; then
    fail "Required values(ROOT_CA_CERT_FILE_PATH,CERT_FILE_PATH,KEY_FILE_PATH) are NOT provided."
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE true
  fi
  cp ${ROOT_CA_CERT_FILE_PATH} ${ROLE_DIR}/root.crt
  cp ${CERT_FILE_PATH} ${ROLE_DIR}/minio.crt
  cp ${KEY_FILE_PATH} ${ROLE_DIR}/minio.key

  oc create secret generic minio-tls --from-file="${ROLE_DIR}/minio.key" --from-file="${ROLE_DIR}/minio.crt" --from-file="${ROLE_DIR}/root.crt" -n ${MINIO_NAMESPACE}
  yq -i eval '.spec.containers[0].volumeMounts += [{"name": "minio-tls", "mountPath": "/home/modelserving/.minio/certs"}] | .spec.volumes += [{"name": "minio-tls", "projected": {"defaultMode": 420, "sources": [{"secret": {"items": [{"key": "minio.crt", "path": "public.crt"}, {"key": "minio.key", "path": "private.key"}, {"key": "root.crt", "path": "CAs/root.crt"}], "name": "minio-tls"}}]}}]' ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)
else
  info "We set the ENABLE_SSL($ENABLE_SSL) as a FALSE"
  # result=1
  # stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

# Apply minio deployment manifests
oc apply -f ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

can_create_route=0
if [[ ${edge_enable_ssl} == "0" && ${enable_ssl} == "0" ]]; then
  fail "EDGE_ENABLE_SSL and ENABLE_SSL cannot be set at the same time"
  can_create_route=1
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE true
fi

# Create route for minio
if [[ ${can_create_route} == "0" && (${CLUSTER_TYPE} == "OCP" || ${CLUSTER_TYPE} == "CRC" || ${CLUSTER_TYPE} == "ROSA") ]]; then
  if [[ ${enable_ssl} == "0" ]]; then
    oc create route reencrypt minio --service=minio --port=minio-client-port --dest-ca-cert ${ROLE_DIR}/root.crt -n ${MINIO_NAMESPACE}
    oc create route reencrypt minio-ui --service=minio --port=minio-ui-port --dest-ca-cert ${ROLE_DIR}/root.crt -n ${MINIO_NAMESPACE}
  elif [[ ${edge_enable_ssl} == "0" ]]; then
    oc create route edge minio --service=minio --port=minio-client-port -n ${MINIO_NAMESPACE}
    oc create route edge minio-ui --service=minio --port=minio-ui-port -n ${MINIO_NAMESPACE}
  else
    oc expose service minio -n ${MINIO_NAMESPACE} --name=minio --port=minio-client-port
    oc expose service minio -n ${MINIO_NAMESPACE} --name=minio-ui  --port=minio-ui-port 
  fi
fi


############# VERIFY #############
if [[ -n ${MINIO_IMAGE} ]]; then
  wait_for_pods_ready "app=minio" ${MINIO_NAMESPACE} 100
else
  wait_for_pods_ready "app=minio" ${MINIO_NAMESPACE}
fi 

debug "oc wait --for=condition=ready pod -l app=minio -n ${MINIO_NAMESPACE} --timeout=10s"
oc wait --for=condition=ready pod -l app=minio -n ${MINIO_NAMESPACE} --timeout=10s

result=$?
if [[ $result == 0 ]]; then
  success "MINIO is running"
  result=0
else
  error "MINIO is NOT running"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

############# OUTPUT #############
minio_svc_protocol="http"
minio_svc_url="minio.${MINIO_NAMESPACE}.svc.cluster.local:9000"

if [[ ${enable_ssl} == "0" ]]; then
  minio_svc_protocol="https"
fi

if [[ ${CLUSTER_TYPE} == "OCP" || ${CLUSTER_TYPE} == "CRC" || ${CLUSTER_TYPE} == "ROSA" ]]; then
  minio_svc_url=$(oc get route minio -o jsonpath="{.spec.host}" -n ${MINIO_NAMESPACE})
fi

echo "MINIO_S3_SVC_URL=${minio_svc_protocol}://${minio_svc_url}" >>${OUTPUT_ENV_FILE}
echo "MINIO_DEFAULT_BUCKET_NAME=${DEFAULT_BUCKET_NAME}" >>${OUTPUT_ENV_FILE}
echo "MINIO_ACCESS_KEY_ID=${ACCESS_KEY_ID}" >>${OUTPUT_ENV_FILE}
echo "MINIO_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}" >>${OUTPUT_ENV_FILE}
echo "MINIO_REGION=${MINIO_REGION}" >>${OUTPUT_ENV_FILE}

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
