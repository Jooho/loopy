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
nfs_provisioner_operator_manifests=$(yq e '.role.manifests.nfs_provisioner_operator' $current_dir/config.yaml)
nfs_provisioner_operator_manifests_path=$current_dir/$nfs_provisioner_operator_manifests
nfs_provisioner_cr_manifests=$(yq e '.role.manifests.nfs_provisioner_cr' $current_dir/config.yaml)
nfs_provisioner_cr_manifests_path=$current_dir/$nfs_provisioner_cr_manifests

result=1 # 0 is "succeed", 1 is "fail"

if [[ z${TEST_KIND} == z ]]; then
  if [[ z${CLUSTER_TOKEN} != z ]]; then
    oc login --token=${CLUSTER_TOKEN} --server=${CLUSTER_API_URL}
  else
    oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  fi
  check_oc_status
fi

# Check if the storageclass exist
oc get sc ${PVC_STORAGECLASS_NAME} >/dev/null 2>&1
pvcSCExist=$?
if [[ $pvcSCExist != 0 ]]; then
  result=1
  error "StorageClass(${PVC_STORAGECLASS_NAME} does not exist)"
  stop_when_error_happended $result $index_role_name $REPORT_FILE true
fi
pass "Checked the PVC StorageClass(${PVC_STORAGECLASS_NAME}) exist"

# Check if nfs storageclass exist
oc get sc ${NFS_STORAGECLASS_NAME} >/dev/null 2>&1
nfsSCExsit=$?
if [[ $nfsSCExsit == 0 ]]; then
  result=1
  error "[WARNING] StorageClass(${NFS_STORAGECLASS_NAME}) exist. Please remove this sc for proper installation"
  info "oc delete sc ${NFS_STORAGECLASS_NAME} --force --grace-period=0 --wait=true"
  stop_when_error_happended $result $index_role_name $REPORT_FILE true
fi
pass "Checked the nfs StorageClass does not exist"

# Update manifests
sed -e \
  "s+%nfs_provisioner_name%+$NFS_PROVISIONER_NAME+g; \
 s+%nfs_provisioner_ns%+$NFS_PROVISIONER_NS+g; \
 s+%storage_size%+$STORAGE_SIZE+g; \
 s+%pvc_storageclass_name%+$PVC_STORAGECLASS_NAME+g; \
 s+%nfs_storgeclass_name%+$NFS_STORAGECLASS_NAME+g" $nfs_provisioner_cr_manifests_path >${ROLE_DIR}/$(basename $nfs_provisioner_cr_manifests_path)

# Create NFS Provisioner namespace if it does not exist
info "Create a namespace(${NFS_PROVISIONER_NS}) if it does not exist"
oc get ns ${NFS_PROVISIONER_NS} >/dev/null 2>&1 || oc new-project ${NFS_PROVISIONER_NS}

# Install NFS Provisioner operator if it is not installed.
exist_nfs_csv=$(oc get csv -n openshift-operators | grep nfs-provisioner-operator | grep Succeeded | wc -l)
if [[ ${exist_nfs_csv} == 1 ]]; then
  info "NFS Provisioner Operator is already installed so skip the operator installation"
else
  info "Install NFS Provisioner Operator in openshift-operators namespace"

  debug "oc apply -f ${nfs_provisioner_operator_manifests_path}"
  oc apply -f ${nfs_provisioner_operator_manifests_path}
  oc::wait::return::true "oc get csv -n openshift-operators|grep nfs-provisioner-operator |grep Succeeded" 6 50 # 5 min
  csvNotInstalled=$?
  if [[ $csvNotInstalled == 1 ]]; then
    result=1
    error "CSV is NOT installed"
    stop_when_error_happended $result $index_role_name $REPORT_FILE true
  fi
fi

# Create NFS Provisioner CR if it does not exist
exist_nfs_cr=$(oc get nfsprovisioner ${NFS_PROVISIONER_NAME} -n ${NFS_PROVISIONER_NS} | wc -l)
if [[ ${exist_nfs_cr} == 1 ]]; then
  info "NFS Provisioner CR exist so skip to create the CR"
else
  info "Create NFS Provisioner CR in the namespace(${NFS_PROVISIONER_NS})"

  debug "oc apply -f ${ROLE_DIR}/$(basename $nfs_provisioner_cr_manifests_path)
  wait_for_pods_ready "app=nfs-provisioner" ${NFS_PROVISIONER_NS}"
  oc apply -f ${ROLE_DIR}/$(basename $nfs_provisioner_cr_manifests_path)
  wait_for_pods_ready "app=nfs-provisioner" ${NFS_PROVISIONER_NS}
fi

############# VERIFY #############
wait_for_pods_ready "app=nfs-provisioner" ${NFS_PROVISIONER_NS}

oc wait --for=condition=ready pod -l app=nfs-provisioner -n ${NFS_PROVISIONER_NS} --timeout=10s
result=$?

if [[ $result == 0 ]]; then
  success "NFS Provisioner is running"
else
  result=1
  error "NFS Provisioner is NOT running"
fi

############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::$result" >>${REPORT_FILE}

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
