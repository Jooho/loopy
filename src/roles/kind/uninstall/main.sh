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
source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

#################################################################
# Get role information from config
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)

# Check if kind is installed
if ! command -v kind &> /dev/null; then
  fatal "kind could not be found: try make download-cli"  
fi

############# UNINSTALL #############
# Initialize result variable to track success/failure
result=0

# Check if cluster exists before attempting deletion
if ! kind get clusters | grep -q "^${KIND_CLUSTER_NAME}$"; then
    info "Kind cluster ${KIND_CLUSTER_NAME} does not exist"
    result=0  # Not an error if cluster doesn't exist
else
    # Delete the kind cluster if it exists
    if ! kind delete cluster --name ${KIND_CLUSTER_NAME}; then
        fail "Failed to delete kind cluster ${KIND_CLUSTER_NAME}"
        result=1
    else
        success "Successfully deleted kind cluster ${KIND_CLUSTER_NAME}"
    fi
fi

############# VERIFY #############
# Verify that the cluster is actually deleted
# Retry checking cluster deletion for up to 2 minutes (120 seconds) with 5 second intervals
if ! retry 120 5 "! kind get clusters | grep -q '^${KIND_CLUSTER_NAME}$'" "Waiting for cluster ${KIND_CLUSTER_NAME} to be fully deleted"; then
    fail "Kind cluster ${KIND_CLUSTER_NAME} still exists after 2 minutes"
    result=1
fi

############# REPORT #############
# Write the result to the report file in the format "role_name::result"
echo "${index_role_name}::${result}" >>${REPORT_FILE} 