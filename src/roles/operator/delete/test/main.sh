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
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)
subs_manifests=$(yq e '.role.manifests.subscription' $current_dir/config.yaml)
subs_manifests_path=$root_directory/$subs_manifests

ARTIFACTS_DIR=/tmp/a
sed -e \
"s+%subscription-name%+$SUBSCRIPTION_NAME+g; \
 s+%operator-namespace%+$OPERATOR_NAMESPACE+g; \
 s+%channel%+$CHANNEL+g; \
 s+%install-approval%+$INSTALL_APPROVAL+g; \
 s+%operator-name%+$OPERATOR_NAME+g; \
 s+%catalogsource-name%+$CATALOGSOURCE_NAME+g; \
 s+%catalogsource-namespace%+$CATALOGSOURCE_NAMESPACE+g" \
   $subs_manifests_path > ${ARTIFACTS_DIR}/$(basename $subs_manifests_path)

oc create -f ${ARTIFACTS_DIR}/$(basename $subs_manifests_path)

############# VERIFY #############
wait_for_just_created_pod_ready ${OPERATOR_NAMESPACE}


############# OUTPUT #############


############# REPORT #############
echo ${role_name}::${OPERATOR_NAME}::$? >> ${OUTPUT_DIR}/${REPORT_FILE}
