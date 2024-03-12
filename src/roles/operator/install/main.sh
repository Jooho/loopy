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
og_manifests=$(yq e '.role.manifests.operatorgroup' $current_dir/config.yaml)
og_manifests_path=$root_directory/$og_manifests

subs_manifests=$(yq e '.role.manifests.subscription' $current_dir/config.yaml)
subs_manifests_path=$root_directory/$subs_manifests

catalogsource_manifests=$(yq e '.role.manifests.catalogsource' $current_dir/config.yaml)
catalogsource_manifests_path=$root_directory/$catalogsource_manifests

errorHappened=1 # 0 is true, 1 is false

if [[ z${CLUSTER_TOKEN} != z ]]
then
  oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
else  
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} ${CLUSTER_API_URL}
fi

check_oc_status

if [[ $OPERATOR_NAMESPACE != 'openshift-operators' ]]
then
  oc get ns $OPERATOR_NAMESPACE || oc new-project $OPERATOR_NAMESPACE
  if [[ $? != 0 ]]
  then
    error "[FAIL] It failed to create the project($OPERATOR_NAMESPACE)" 
    exit 1
  fi

  sed -e \
  "s+%operatorgroup-name%+$SUBSCRIPTION_NAME+g; \
   s+%operatorgroup-namespace%+$OPERATOR_NAMESPACE+g"  $og_manifests_path > ${ROLE_DIR}/$(basename $og_manifests_path)
  oc apply -f ${ROLE_DIR}/$(basename $og_manifests_path)
fi

sed -e \
"s+%subscription-name%+$SUBSCRIPTION_NAME+g; \
 s+%operator-namespace%+$OPERATOR_NAMESPACE+g; \
 s+%channel%+$CHANNEL+g; \
 s+%install-approval%+$INSTALL_APPROVAL+g; \
 s+%operator-name%+$OPERATOR_NAME+g; \
 s+%catalogsource-name%+$CATALOGSOURCE_NAME+g; \
 s+%catalogsource-namespace%+$CATALOGSOURCE_NAMESPACE+g" $subs_manifests_path > ${ROLE_DIR}/$(basename $subs_manifests_path)

if [[ ${OPERATOR_VERSION} != 'latest' ]]
then
  sed -e \
  "s+%operator-version%+.$OPERATOR_VERSION+g" -i ${ROLE_DIR}/$(basename $subs_manifests_path)
else
  sed -i '/startingCSV/d' ${ROLE_DIR}/$(basename $subs_manifests_path)
fi

## Set Config env for subscription
if [[ z${CONFIG_ENV} != z ]]
then
  IFS='=' read -r name value <<< "$CONFIG_ENV"
  yq -i ".spec.config.env += [{\"$name\": \"$value\"}]" ${ROLE_DIR}/$(basename $subs_manifests_path)
fi

# Check if catalogsource is needed or not
if [[ ${CATALOGSOURCE_NAME} == "community-operators" || ${CATALOGSOURCE_NAME} == "redhat-operators" || ${CATALOGSOURCE_NAME} == "redhat-marketplace" || ${CATALOGSOURCE_NAME} == "certified-operators" ]]
then
  echo "The catalogsource(${CATALOGSOURCE_NAME}) is official one"
else
  echo "The catalogsource(${CATALOGSOURCE_NAME}) is NOT official one so it will create a catalogsource with catalog image{${CATALOGSOURCE_IMAGE}}"

  if [[ -z ${CATALOGSOURCE_IMAGE} ]];
  then
    error "catalogsource image is required. please provide it"
    exit 1
  fi

  sed -e \
  "s+%catalogsource-displayname%+$CATALOGSOURCE_DISPLAYNAME+g; \
   s+%catalogsource-publisher%+$CATALOGSOURCE_PUBLISHER+g; \
   s+%catalogsource-image%+$CATALOGSOURCE_IMAGE+g; \
   s+%catalogsource-name%+$CATALOGSOURCE_NAME+g; \
   s+%catalogsource-namespace%+$CATALOGSOURCE_NAMESPACE+g" $catalogsource_manifests_path > ${ROLE_DIR}/$(basename $catalogsource_manifests_path)

   oc apply -f ${ROLE_DIR}/$(basename $catalogsource_manifests_path)
fi
if [[ $? != 0 ]]
then
  error "[FAIL] It failed to apply the catalogsource(${ROLE_DIR}/$(basename $catalogsource_manifests_path) " 
  exit 1
fi

# Create final subscription
oc apply -f ${ROLE_DIR}/$(basename $subs_manifests_path)
if [[ $? != 0 ]]
then
  error "[FAIL] It failed to apply the subscription(${ROLE_DIR}/$(basename $subs_manifests_path) " 
  exit 1
fi

############# VERIFY #############
if [[ z$OPERATOR_POD_PREFIX != z && $OPERATOR_POD_PREFIX != "NONE" ]]
then
  wait_counter=0
  while true; do
    pod_name=$(oc get pod -n ${OPERATOR_NAMESPACE}|grep ${OPERATOR_POD_PREFIX}|awk '{print $1}')
    if [[ $pod_name == "" ]]
    then
      wait_counter=$((wait_counter + 1))
      echo " Waiting 10 secs ..."
      sleep 10
      if [[ $wait_counter -ge 30 ]]; then
        echo
        oc get pods -n $OPERATOR_NAMESPACE
        error "Timed out after $((30 * wait_counter / 60)) minutes waiting for pod with prefix: $OPERATOR_POD_PREFIX"
        errorHappened="0"
        break
      fi
    else 
      echo "Detected a new pod name: ${pod_name}"
      break
    fi
  done
else
  errorHappened=$(wait_for_pods_ready "${OPERATOR_LABEL}" "${OPERATOR_NAMESPACE}" | tail -n 1)
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


############# REPORT #############
echo "${index_role_name}::${OPERATOR_NAME}::$?" >> ${REPORT_FILE}
