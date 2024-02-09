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
minio_deployment_manifests=$(yq e '.role.manifests.minio_deployment' $current_dir/config.yaml)
minio_deployment_manifests_path=$current_dir/$minio_deployment_manifests

if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
fi
check_oc_status

sed -e \
"s+%access_key_id%+$ACCESS_KEY_ID+g; \
 s+%secret_access_key%+$SECRET_ACCESS_KEY+g; \
 s+%minio_namespace%+$MINIO_NAMESPACE+g; \
 s+%minio_image%+$MINIO_IMAGE+g" $minio_deployment_manifests_path > ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

oc get ns ${MINIO_NAMESPACE}  > /dev/null 2>&1 ||  oc new-project ${MINIO_NAMESPACE} > /dev/null 2>&1 
oc apply -f ${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

############# VERIFY #############
wait_for_pods_ready "app=minio" ${MINIO_NAMESPACE}
oc wait --for=condition=ready pod -l app=minio -n ${MINIO_NAMESPACE} --timeout=10s

result=$?
if [[ $result == 0 ]]
then
  success "[SUCCESS] MINIO is running"
  result=0
else
  error "[FAIL] MINIO is NOT running"
fi

############# OUTPUT #############
echo "MINIO_S3_SVC_URL=http://minio.${MINIO_NAMESPACE}.svc.cluster.local:9000" >> ${OUTPUT_ENV_FILE}
echo "MINIO_DEFAULT_BUCKET_NAME=${DEFAULT_BUCKET_NAME}" >> ${OUTPUT_ENV_FILE}
echo "MINIO_ACCESS_KEY_ID=${ACCESS_KEY_ID}" >> ${OUTPUT_ENV_FILE}
echo "MINIO_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}" >> ${OUTPUT_ENV_FILE}
echo "MINIO_REGION=${MINIO_REGION}" >> ${OUTPUT_ENV_FILE}

############# REPORT #############
echo "${role_name}::$?" >> ${REPORT_FILE}
