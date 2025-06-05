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

# If DELETE is true (non-zero), force delete
delete_crc_vm=$(is_positive ${DELETE})
crc_status=$(crc status 2>&1)
if [[ ${delete_crc_vm} == "0" ]]; then
  info "DELETE is set. Deleting CRC environment..."
  if ! echo "$crc_status" | grep -q "Machine does not exist"; then
    if ! crc delete --force; then
      die "crc delete failed"
    fi  
  fi
else 
  info "CRC VM is being stopped"  
  stop_output=$(crc stop 2>&1)
  if ! echo "$stop_output" | grep -q "Stopped the instance\|Instance is already stopped"; then
    die "crc stop failed"
  else
    info "CRC VM is stopped"
  fi
fi

# If CLEANUP is true (non-zero), force cleanup
cleanup_crc=$(is_positive ${CLEANUP})
if [[ ${cleanup_crc} == "0" ]]; then
  info "CLEANUP is set. Cleaning up CRC environment..."
  if ! crc cleanup; then
    die "crc cleanup failed"
  fi
fi

############# VERIFY #############
result=0

# Verify openshift local cluster is stopped
crc_status=$(crc status 2>&1)
if echo "$crc_status" | grep -iq "Machine does not exist\|crc does not seem to be setup correctly" || [ "$(crc status -o json | jq -r .openshiftStatus)" = "Stopped" ]; then
    success "OpenShift local cluster is properly stopped"
else
    fail "OpenShift local cluster is not properly stopped"
    result=1
fi


############# OUTPUT #############


############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}
