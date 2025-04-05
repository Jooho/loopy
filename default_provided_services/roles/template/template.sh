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
  echo "The root directory is: $root_directory"
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

sed -e \
  "s+%access_key_id%+$ACCESS_KEY_ID+g; \
 s+%secret_access_key%+$SECRET_ACCESS_KEY+g; \
 s+%minio_namespace%+$MINIO_NAMESPACE+g; \
 s+%minio_image%+$MINIO_IMAGE+g" $minio_deployment_manifests_path >${ROLE_DIR}/$(basename $minio_deployment_manifests_path)

############# VERIFY #############
result=0

############# OUTPUT #############
echo "MINIO_S3_SVC_URL=http://minio.${MINIO_NAMESPACE}.svc.cluster.local:9000" >>${OUTPUT_ENV_FILE}

############# REPORT #############
echo "${index_role_name}::$?" >>${REPORT_FILE}
