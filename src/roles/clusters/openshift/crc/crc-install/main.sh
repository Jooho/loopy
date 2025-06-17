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
  echo "Unable to find .github folder"
fi

source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

#################################################################
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)


# Check if crc is installed
if ! command -v crc &> /dev/null; then
  die "crc could not be found: try make download-cli"  
fi

# Check if CRC is already set up
crc_status=$(crc status 2>&1)
if ! echo "$crc_status" | grep -q "CRC VM"; then
  info "CRC not initialized. Running setup..."
  if ! crc setup; then
    die "crc setup failed"
  fi
fi

# If RESET_CRC_SETUP is true (non-zero), force reset
force_reset=$(is_positive ${RESET_CRC_SETUP})
if [[ ${force_reset} == "0" ]]; then
  echo "[INFO] RESET_CRC_SETUP is set. Resetting CRC environment..."
  
  if ! crc delete --force; then
    die "crc delete failed"
  fi

  if ! crc cleanup; then
    die "crc cleanup failed"
  fi

  if ! crc setup; then
    die "crc setup failed"
  fi
fi

crc_status=$(crc status 2>&1)
if ! echo "$crc_status" | grep -q "Running"; then
  # Set crc config
  if echo "$crc_status" | grep -q "Machine does not exist"; then
    info "Configuring CRC VM..."    
    crc config set memory ${MEMORY} >/dev/null 2>&1
    crc config set cpus ${CPU} >/dev/null 2>&1
    crc config set disk-size ${DISK_SIZE} >/dev/null 2>&1
    crc config set kubeadmin-password ${KUBEADMIN_PASSWORD} >/dev/null 2>&1
    crc config set enable-cluster-monitoring ${ENABLE_MONITORING} >/dev/null 2>&1
  else
    info "CRC VM is already configured"
  fi

  if [ ! -f "${PULL_SECRET_PATH}" ] && [ ! -f "$(eval echo ${PULL_SECRET_PATH})" ]; then
    die "Pull secret file not found at ${PULL_SECRET_PATH}"
  fi

  # Start crc
  info "Starting CRC VM..."
  debug "crc start -p $(eval echo ${PULL_SECRET_PATH})"
  crc_start_output=$(crc start -p $(eval echo ${PULL_SECRET_PATH}))
  if ! echo "$crc_start_output" | grep -q "Started the instance"; then
    die "Failed to start CRC cluster"
  fi
else
  info "CRC is already running, skipping start"
fi


############# VERIFY #############
result=0

# Verify openshift local cluster is running
if ! retry 60 5 "crc status -o json|jq -r .openshiftStatus | grep -q Running" "Waiting for openshift local cluster to be ready"; then
    fail "Openshift local cluster is not running properly after 5 minutes"
    result=1
else
    success "Openshift local cluster is running properly"
fi


############# OUTPUT #############
if [[ $result -eq 0 ]]; then

  oc login -u kubeadmin -p ${KUBEADMIN_PASSWORD} --insecure-skip-tls-verify=true >/dev/null 2>&1
  if [[ $(is_positive ${ADD_CLUSTER_ADMIN_TO_DEVELOPER}) == "0" ]]; then
    oc adm policy add-cluster-role-to-user cluster-admin developer >/dev/null 2>&1
  fi
   
  cluster_console_url=$(crc console --url)
  cluster_api_url=$(oc whoami --show-server)
  cluster_admin_id=kubeadmin
  cluster_admin_pw=${KUBEADMIN_PASSWORD}
  cluster_token=$(oc whoami -t)
  cluster_type="openshift-local"
  

  echo "CLUSTER_CONSOLE_URL=${cluster_console_url}" >>${OUTPUT_ENV_FILE}
  echo "CLUSTER_API_URL=${cluster_api_url}" >>${OUTPUT_ENV_FILE}
  echo "CLUSTER_ADMIN_ID=${cluster_admin_id}" >>${OUTPUT_ENV_FILE}
  echo "CLUSTER_ADMIN_PW=${cluster_admin_pw}" >>${OUTPUT_ENV_FILE}
  echo "CLUSTER_TOKEN=${cluster_token}" >>${OUTPUT_ENV_FILE}
  echo "CLUSTER_TYPE=${cluster_type}" >>${OUTPUT_ENV_FILE}
fi

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}
