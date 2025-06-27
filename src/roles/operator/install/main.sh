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
og_manifests=$(yq e '.role.manifests.operatorgroup' $current_dir/config.yaml)
og_manifests_path=$root_directory/$og_manifests

subs_manifests=$(yq e '.role.manifests.subscription' $current_dir/config.yaml)
subs_manifests_path=$root_directory/$subs_manifests

catalogsource_manifests=$(yq e '.role.manifests.catalogsource' $current_dir/config.yaml)
catalogsource_manifests_path=$root_directory/$catalogsource_manifests

result=1 # 0 is "succeed", 1 is "fail"

if [[ z${USE_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

if [[ $OPERATOR_NAMESPACE != 'openshift-operators' ]] || [[ z${USE_KIND} != z ]]; then  
  oc get ns $OPERATOR_NAMESPACE || oc create ns $OPERATOR_NAMESPACE
  result=$?
  if [[ $result != 0 ]]; then
    error "Failed to create the project($OPERATOR_NAMESPACE)"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
  oc project $OPERATOR_NAMESPACE
  
  sed -e \
    "s+%operatorgroup-name%+$OPERATORGROUP_NAME+g; \
   s+%operatorgroup-namespace%+$OPERATOR_NAMESPACE+g" $og_manifests_path >${ROLE_DIR}/$(basename $og_manifests_path)

  if [[ z${TARGET_NAMESPACES} != "z" ]]; then
    # Convert the comma-separated string to an array
    IFS=',' read -r -a namespaces <<<"$TARGET_NAMESPACES"

    # Convert the array to a JSON array format for yq
    target_namespaces=$(printf '%s\n' "${namespaces[@]}" | jq -R . | jq -s .)

    yq eval ".spec.targetNamespaces = $target_namespaces" -i "${ROLE_DIR}/$(basename "$og_manifests_path")"
  fi
  debug "oc apply -f ${ROLE_DIR}/$(basename $og_manifests_path)"
  oc apply -f ${ROLE_DIR}/$(basename $og_manifests_path)
fi

sed -e \
  "s+%subscription-name%+$SUBSCRIPTION_NAME+g; \
 s+%operator-namespace%+$OPERATOR_NAMESPACE+g; \
 s+%channel%+$CHANNEL+g; \
 s+%install-approval%+$INSTALL_APPROVAL+g; \
 s+%operator-name%+$OPERATOR_NAME+g; \
 s+%catalogsource-name%+$CATALOGSOURCE_NAME+g; \
 s+%catalogsource-namespace%+$CATALOGSOURCE_NAMESPACE+g" $subs_manifests_path >${ROLE_DIR}/$(basename $subs_manifests_path)

if [[ ${OPERATOR_VERSION} != 'latest' ]]; then
  sed -e \
    "s+%operator-version%+.$OPERATOR_VERSION+g" -i ${ROLE_DIR}/$(basename $subs_manifests_path)
else
  sed -i '/startingCSV/d' ${ROLE_DIR}/$(basename $subs_manifests_path)
fi

## Set Config env for subscription
if [[ z${CONFIG_ENV} != z ]]; then
  IFS='=' read -r name value <<<"$CONFIG_ENV"
  yq -i ".spec.config.env += [{\"$name\": \"$value\"}]" ${ROLE_DIR}/$(basename $subs_manifests_path)
fi

info "Check if catalogsource is needed or not"
if [[ ${CATALOGSOURCE_NAME} == "operatorhubio-catalog"||${CATALOGSOURCE_NAME} == "community-operators" || ${CATALOGSOURCE_NAME} == "redhat-operators" || ${CATALOGSOURCE_NAME} == "redhat-marketplace" || ${CATALOGSOURCE_NAME} == "certified-operators" ]]; then
  info "The catalogsource(${CATALOGSOURCE_NAME}) is official one"
else
  info "The catalogsource(${CATALOGSOURCE_NAME}) is NOT official one so it will create a catalogsource with catalog image{${CATALOGSOURCE_IMAGE}}"

  if [[ -z ${CATALOGSOURCE_IMAGE} ]]; then
    error "catalogsource image is required. please provide it"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi

  sed -e \
    "s+%catalogsource-displayname%+$CATALOGSOURCE_DISPLAYNAME+g; \
   s+%catalogsource-publisher%+$CATALOGSOURCE_PUBLISHER+g; \
   s+%catalogsource-image%+$CATALOGSOURCE_IMAGE+g; \
   s+%catalogsource-name%+$CATALOGSOURCE_NAME+g; \
   s+%catalogsource-namespace%+$CATALOGSOURCE_NAMESPACE+g" $catalogsource_manifests_path >${ROLE_DIR}/$(basename $catalogsource_manifests_path)

  debug "oc apply -f ${ROLE_DIR}/$(basename $catalogsource_manifests_path)"
  oc apply -f ${ROLE_DIR}/$(basename $catalogsource_manifests_path)
  result=$?
  if [[ $result != 0 ]]; then
    error "It failed to apply the catalogsource(${ROLE_DIR}/$(basename $catalogsource_manifests_path) "
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
fi

info "Create final subscription"
debug "oc apply -f ${ROLE_DIR}/$(basename $subs_manifests_path)"
oc apply -f ${ROLE_DIR}/$(basename $subs_manifests_path)
result=$?
if [[ $result != 0 ]]; then
  error "Failed to create the subscription(${ROLE_DIR}/$(basename $subs_manifests_path)"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE
fi

if [[ $INSTALL_APPROVAL == "Manual" ]]; then
  sleep 5
  oc::wait::return::true "oc get installplan -n $OPERATOR_NAMESPACE |grep ${OPERATOR_NAME} |grep ${OPERATOR_VERSION}|grep ${INSTALL_APPROVAL} |grep 'false'" 5 3

  install_plan=$(oc get installplan -n $OPERATOR_NAMESPACE | grep ${OPERATOR_NAME} | grep ${OPERATOR_VERSION} | grep ${INSTALL_APPROVAL} | grep 'false' | awk '{print $1}')
  info "installplan name: ${install_plan}"
  oc patch installplan $install_plan -n $OPERATOR_NAMESPACE -p '{"spec":{"approved": true}}' --type=merge
  result=$?
  if [[ $result != "0" ]]; then
    error "Failed to patch installplan"
    result=1
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  fi
fi

############# VERIFY #############
if [[ z$OPERATOR_POD_PREFIX != z && $OPERATOR_POD_PREFIX != "NONE" ]]; then
  info "OPERATOR_POD_PREFIX is set: ${OPERATOR_POD_PREFIX}"
  wait_counter=0
  while true; do
    pod_name=$(oc get pod -n ${OPERATOR_NAMESPACE} | grep ${OPERATOR_POD_PREFIX} | awk '{print $1}')
    if [[ $pod_name == "" ]]; then
      wait_counter=$((wait_counter + 1))
      pending " Waiting 10 secs ..."
      sleep 10
      if [[ $wait_counter -ge 30 ]]; then
        echo
        oc get pods -n $OPERATOR_NAMESPACE
        error "Timed out after $((30 * wait_counter / 60)) minutes waiting for pod with prefix: $OPERATOR_POD_PREFIX"
        result="0"
        break
      fi
    else
      info "Detected a new pod name: ${pod_name}"
      break
    fi
  done
  wait_for_pod_name_ready ${pod_name} ${OPERATOR_NAMESPACE}
else
  wait_for_pods_ready "${OPERATOR_LABEL}" "${OPERATOR_NAMESPACE}"
  result=$?
fi
############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::${OPERATOR_NAME}::$?" >>${REPORT_FILE}

############# STOP WHEN RESULT IS FAIL #############
if [[ $result != "0" ]]; then
  info "The role failed"
  should_stop=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${should_stop} == "0" ]]; then
    die "[CRITICAL] STOP_WHEN_FAILED(${should_stop}) is set so it will be stoppped."
  else
    info "STOP_WHEN_FAILED(${should_stop}) is NOT set so skip this error."
  fi
fi
