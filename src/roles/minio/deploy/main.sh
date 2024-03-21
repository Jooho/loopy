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
minio_deployment_manifests=$(yq e '.role.manifests.minio_deployment' $current_dir/config.yaml)
minio_deployment_manifests_path=$current_dir/$minio_deployment_manifests

errorHappened=1 # 0 is true, 1 is false
if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi
check_oc_status

oc get ns ${MINIO_NAMESPACE}  > /dev/null 2>&1 ||  oc new-project ${MINIO_NAMESPACE} > /dev/null 2>&1 
oc label namespace ${MINIO_NAMESPACE} pod-security.kubernetes.io/enforce=baseline --overwrite
oc label namespace ${MINIO_NAMESPACE} pod-security.kubernetes.io/warn=baseline --overwrite
oc label namespace ${MINIO_NAMESPACE} pod-security.kubernetes.io/audit=baseline  --overwrite

sed -e \
"s+%access_key_id%+$ACCESS_KEY_ID+g; \
 s+%secret_access_key%+$SECRET_ACCESS_KEY+g; \
 s+%minio_namespace%+$MINIO_NAMESPACE+g; \
 s+%minio_image%+$MINIO_IMAGE+g" $minio_deployment_manifests_path > ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

enable_ssl=$(is_positive ${ENABLE_SSL})
if [[ ${enable_ssl} == "0" ]]
then
  info "MINIO SSL Enabled"
  echo "${ROOT_CA_CERT_FILE_PATH}"
  if [[ ! -n ${ROOT_CA_CERT_FILE_PATH} || ! -n ${CERT_FILE_PATH} || ! -n ${KEY_FILE_PATH} ]]
  then
    echo "Required values(ROOT_CA_CERT_FILE_PATH,CERT_FILE_PATH,KEY_FILE_PATH) are NOT provided."
    exit 1
  fi
  cp ${ROOT_CA_CERT_FILE_PATH} ${ROLE_DIR}/root.crt
  cp ${CERT_FILE_PATH} ${ROLE_DIR}/minio.crt
  cp ${KEY_FILE_PATH} ${ROLE_DIR}/minio.key

  oc create secret generic minio-tls --from-file="${ROLE_DIR}/minio.key" --from-file="${ROLE_DIR}/minio.crt" --from-file="${ROLE_DIR}/root.crt" -n ${MINIO_NAMESPACE}

  yq -i eval '.spec.containers[0].volumeMounts += [{"name": "minio-tls", "mountPath": "/home/modelmesh/.minio/certs"}] | .spec.volumes += [{"name": "minio-tls", "projected": {"defaultMode": 420, "sources": [{"secret": {"items": [{"key": "minio.crt", "path": "public.crt"}, {"key": "minio.key", "path": "private.key"}, {"key": "root.crt", "path": "CAs/root.crt"}], "name": "minio-tls"}}]}}]' ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)
else
 error "We set the ENABLE_SSL($ENABLE_SSL) as a FALSE"
 errorHappened=0
fi
oc apply -f ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

############# VERIFY #############
errorHappened=$(wait_for_pods_ready "app=minio" ${MINIO_NAMESPACE})
oc wait --for=condition=ready pod -l app=minio -n ${MINIO_NAMESPACE} --timeout=10s

result=$?
if [[ $result == 0 ]]
then
  success "[SUCCESS] MINIO is running"
  result=0
else
  error "[FAIL] MINIO is NOT running"
  errorHappened=0
fi

if [[ $errorHappened == "0" ]]
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
if [[ ${enable_ssl} == "0" ]]
then
  echo "MINIO_S3_SVC_URL=https://minio.${MINIO_NAMESPACE}.svc.cluster.local:9000" >> ${OUTPUT_ENV_FILE}
else 
  echo "MINIO_S3_SVC_URL=http://minio.${MINIO_NAMESPACE}.svc.cluster.local:9000" >> ${OUTPUT_ENV_FILE}
fi
echo "MINIO_DEFAULT_BUCKET_NAME=${DEFAULT_BUCKET_NAME}" >> ${OUTPUT_ENV_FILE}
echo "MINIO_ACCESS_KEY_ID=${ACCESS_KEY_ID}" >> ${OUTPUT_ENV_FILE}
echo "MINIO_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}" >> ${OUTPUT_ENV_FILE}
echo "MINIO_REGION=${MINIO_REGION}" >> ${OUTPUT_ENV_FILE}

############# REPORT #############
echo "${index_role_name}::$?" >> ${REPORT_FILE}
