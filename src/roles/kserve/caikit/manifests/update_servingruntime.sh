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
ROOT_DIR=/tmp
RUNTIME_DIR="${ROOT_DIR}/latest_runtime"
LATEST_OOTB_RUNTIME_PATH="${RUNTIME_DIR}/ootb_runtime.yaml"
RUNTIME_MANIFESTS_DIR="${ROOT_DIR}/odh-dashboard/manifests/modelserving"
if [[ ! -d "${ROOT_DIR}/odh-dashboard" ]]
then
  git clone git@github.com:red-hat-data-services/odh-dashboard.git ${ROOT_DIR}/odh-dashboard
fi  
if [[ ! -d ${RUNTIME_DIR} ]]
then
  mkdir ${RUNTIME_DIR}
fi  
kubectl kustomize ${RUNTIME_MANIFESTS_DIR}  > $LATEST_OOTB_RUNTIME_PATH
echo $LATEST_OOTB_RUNTIME_PATH
last_line=$(sed -n '$=' $LATEST_OOTB_RUNTIME_PATH)
delimeter_lines=$(cat ${LATEST_OOTB_RUNTIME_PATH} -n |grep '\-\-\-'|cut -f1)
delimeter_lines+=($last_line)
start_line=1
for end_line in ${delimeter_lines[@]}
do
  sed -n "${start_line},$((end_line-1))p" "${LATEST_OOTB_RUNTIME_PATH}" > "${RUNTIME_DIR}/temp_output_file.yaml"
  start_line=$(( end_line+1 ))
  kind=$(yq '.kind' "${RUNTIME_DIR}/temp_output_file.yaml")
  if [[ $kind == 'Template' ]]
  then
     yq '.objects[0]' "${RUNTIME_DIR}/temp_output_file.yaml" > "${RUNTIME_DIR}/temp_runtime.yaml"
     runtime_name=$(cat "${RUNTIME_DIR}/temp_runtime.yaml" | yq '.metadata.name')     
     mv "${RUNTIME_DIR}/temp_runtime.yaml" "${RUNTIME_DIR}/${runtime_name}.yaml"
  fi
done

for file in $(ls ${RUNTIME_DIR}); do
    filename=$(basename "$file")
    if [[ "$filename" == "caikit-tgis-runtime.yaml" ]]; then
        cp "${RUNTIME_DIR}/$file" "${current_dir}/caikit-tgis/caikit-tgis-servingruntime.yaml"
    elif [[ "$filename" == "tgis-grpc-runtime.yaml" ]]; then

        cp "${RUNTIME_DIR}/$file" "${current_dir}/caikit-standalone/tgis-servingruntime.yaml"
    fi
done
