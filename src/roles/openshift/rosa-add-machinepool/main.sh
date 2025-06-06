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
index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)

result=1 # 0 is "succeed", 1 is "fail"

check_rosa_access

info "rosa create machinepool --cluster=$CLUSTER_NAME --name=$MACHINE_POOL_NAME --replicas=$MACHINE_POOL_REPLICA_COUNT --instance-type=$NEW_MACHINE_POOL_TYPE --use-spot-instances --subnet=xxxx -y"
rosa create machinepool --cluster=$CLUSTER_NAME --name=$MACHINE_POOL_NAME --replicas=$MACHINE_POOL_REPLICA_COUNT --instance-type=$NEW_MACHINE_POOL_TYPE --use-spot-instances --subnet=$PRIVATE_SUBNET -y

result=$?
if [[ $result != "0" ]]; then
  fail "ROSA failed to add a new machinepool"
  result=1
  stop_when_error_happened $result $index_role_name $REPORT_FILE true
fi

############# VERIFY #############
# check if the new machinepool is added and ready
check_machinepool_ready() {
  rosa list machinepools --cluster "$CLUSTER_NAME" --output json | jq -r --arg pool_name "$MACHINE_POOL_NAME" '.[] | select(.id == $pool_name) | if .status.current_replicas == .replicas then "ready" else "Not Ready" end'
}

if [[ $result == "0" ]]; then
  # Periodically check the machinepool status.
  # Retry logic variables
  MAX_RETRIES=30
  RETRY_INTERVAL=60 # Interval between retries in seconds
  RETRY_COUNT=0

  info "Verify if new machinepool is added"
  while true; do
    NEW_MACHINEPOOL_STATUS=$(check_machinepool_ready)
    RETRY_COUNT=$((RETRY_COUNT + 1))

    info "Attempt ${RETRY_COUNT} of $MAX_RETRIES."

    if ((RETRY_COUNT >= MAX_RETRIES)); then
      error "The new machinepool($MACHINE_POOL_NAME) is added but it did NOT become READY within the given time."
      result=1
      stop_when_error_happened $result $index_role_name $REPORT_FILE
      break
    fi

    if [ "$NEW_MACHINEPOOL_STATUS" == "ready" ]; then
      result=0
      break
    else
      info "MachinePool status: $NEW_MACHINEPOOL_STATUS. Waiting for it to become ready..."
    fi

    sleep $RETRY_INTERVAL
  done
fi

if [[ $result == 0 ]]; then
  success "MachinePool is created and ready!"
else
  fail "The new machinepool($MACHINE_POOL_NAME) failed to be added properly"
fi

############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}

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
