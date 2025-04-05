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

result=1          # 0 is "succeed", 1 is "fail"
already_deleted=1 # 0 is true(fail), 1 is false(succeed)

check_rosa_access
# Get operator_role_prefix to clean up operator role (refer https://docs.google.com/document/d/1DQgZwj0GjCASfolFeAMXQQ1ZFRvFUp_4p1ZI_GDE42c/edit#heading=h.wmvtisowiku)
operator_role_prefix=$(rosa describe cluster -c "$CLUSTER_NAME" --output json | jq -r '.aws.sts.operator_role_prefix')

info "Start to delete the rosa cluster($CLUSTER_NAME)"
rosa delete cluster --cluster $CLUSTER_NAME -y

result=$?

if [[ $result != "0" ]]; then
  rosa delete cluster --cluster $CLUSTER_NAME -y 2>&1 | tee output.log
  if grep -q "There is no cluster with identifier" output.log; then
    already_deleted=0
  fi

  if [[ $already_deleted == 0 ]]; then
    info "The cluster($CLUSTER_NAME) does not exist"
    result=0
  else
    error "ROSA failed to delete a cluster"
    result=1
    stop_when_error_happended $result $index_role_name $REPORT_FILE
  fi
fi

if [[ $already_deleted != 0 ]]; then
  # Function to check the cluster status
  check_cluster_status() {
    rosa describe cluster -c "$CLUSTER_NAME" --output json | jq -r '.status.state'
  }

  # Retry logic variables
  MAX_RETRIES=30
  RETRY_INTERVAL=60 # Interval between retries in seconds
  RETRY_COUNT=0

  # Infinite loop to check the cluster status
  while true; do
    STATUS=$(check_cluster_status)
    RETRY_COUNT=$((RETRY_COUNT + 1))

    info "Attempt $((RETRY_COUNT)) of $MAX_RETRIES."

    case "$STATUS" in
    "uninstalling")
      info "Cluster is being uninstalled!"
      ;;
    "error")
      error "Cluster status: $STATUS."
      result=1
      rosa describe cluster -c "$CLUSTER_NAME" --output json
      stop_when_error_happended $result $index_role_name $REPORT_FILE
      break # Exit the loop as the cluster log show error
      ;;
    "")
      CLUSTER_EXISTS=$(rosa list clusters | grep "$CLUSTER_NAME" | wc -l)
      if [[ $CLUSTER_EXISTS == 0 ]]; then
        result=0
        break # Exit the loop as the cluster is successfully uninstalled
      else
        rosa delete cluster --cluster $CLUSTER_NAME -y
      fi
      ;;
    *)
      echo "[INFO] Cluster status: $STATUS. Waiting for it to change..."
      ;;
    esac

    if ((RETRY_COUNT >= MAX_RETRIES)); then
      error "Cluster failed to be deleted after $MAX_RETRIES attempts."
      result=0
      break # Exit the max attemption is reached.
    fi

    sleep $RETRY_INTERVAL
  done

  # Remove operator roles
  info "Remove operator roles for the cluster($CLUSTER_NAME)"
  rosa delete operator-roles --prefix $operator_role_prefix -m auto -y
fi
############# VERIFY #############
# Retry logic variables
MAX_RETRIES=30
RETRY_INTERVAL=60 # Interval between retries in seconds
RETRY_COUNT=0

info "Verify if cluster is uninstalled"
while true; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  info "Attempt ${RETRY_COUNT} of $MAX_RETRIES."

  # Check if the retry count has exceeded the maximum limit
  if ((RETRY_COUNT >= MAX_RETRIES)); then
    error "Cluster($CLUSTER_NAME) is still in the cluster list."
    result=1
    stop_when_error_happended $result $index_role_name $REPORT_FILE
    break
  fi

  CLUSTER_EXISTS=$(rosa list clusters | grep "$CLUSTER_NAME" | wc -l)
  if [[ $CLUSTER_EXISTS == 0 ]]; then
    result=0
    break
  fi

  sleep $RETRY_INTERVAL
done

if [[ $result == 0 ]]; then
  success "The OpenShift cluster($CLUSTER_NAME) is successfully uninstalled!"
else
  error "Cluster($CLUSTER_NAME) is NOT uninstalled."
fi

############# OUTPUT #############

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}

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
