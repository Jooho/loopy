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

result=1        # 0 is fail, 1 is succeed
errorHappened=1 # 0 is true(fail), 1 is false(succeed)

check_rosa_access

info "[INFO] rosa delete machinepool --cluster=$CLUSTER_NAME $MACHINE_POOL_NAME -y"
rosa delete machinepool --cluster=$CLUSTER_NAME $MACHINE_POOL_NAME -y

result=$?
if [[ $result != "0" ]]; then
  result=1
  stop_when_error_happended $result $index_role_name $REPORT_FILE
  error "[FAIL] ROSA failed to delete the machinepool($MACHINE_POOL_NAME)"
fi

############# VERIFY #############
# check if the target machinepool is deleted.

# Retry logic variables
MAX_RETRIES=30
RETRY_INTERVAL=60 # Interval between retries in seconds
RETRY_COUNT=0

info "[INFO] Verify if new machinepool is removeded"
while true; do
  # Check if the machine pool exists
  MACHINE_POOL_EXISTS=$(rosa list machinepools --cluster="$CLUSTER_NAME" --output json | jq -r --arg pool_name "$MACHINE_POOL_NAME" '.[] | select(.id == $pool_name) | .id')
  
  RETRY_COUNT=$((RETRY_COUNT + 1))  
  info "[INFO] Attempt ${RETRY_COUNT} of $MAX_RETRIES."

  # Check if the retry count has exceeded the maximum limit
  if ((RETRY_COUNT >= MAX_RETRIES)); then
    result=1
    stop_when_error_happended $result $index_role_name $REPORT_FILE
    break
  fi

  if [ -z "$MACHINE_POOL_EXISTS" ]; then
    result=0
    break
  else
    info "[INFO] Machine pool($MACHINE_POOL_NAME) is still being deleted..."
  fi

  sleep $RETRY_INTERVAL # Wait for 1 minute before the next check
done

if [[ $result == 0 ]]
then
  success "[SUCCESS] Machine pool($MACHINE_POOL_NAME) has been deleted."
else
  error "[FAIL] Cluster failed to delete the machinepool($MACHINE_POOL_NAME)"
fi

############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}

############# STOP WHEN RESULT IS FAIL #############
if [[ $result != "0" ]] 
then
  info "[INFO] The role failed"
  should_stop=$(is_positive ${STOP_WHEN_FAILED})
  if [[ ${should_stop} == "0" ]]
  then
    die "[CRITICAL] STOP_WHEN_FAILED(${should_stop}) is set so it will be stoppped."
  else
    info "[INFO] STOP_WHEN_FAILED(${should_stop}) is NOT set so skip this error."
  fi
fi  
