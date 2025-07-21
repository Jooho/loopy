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

result=1                   # 0 is "succeed", 1 is "fail"
failed_to_create_cluster=1 # 0 is true(fail), 1 is false(succeed)

check_rosa_access
cluster_exists=no # 1 
if rosa list clusters | grep -q "$CLUSTER_NAME"; then
    cluster_exists=yes  #0
    STATUS=$(rosa describe cluster -c "$CLUSTER_NAME" --output json | jq -r '.state')
    if [[ "$STATUS" == "ready" ]]; then
        echo "Cluster '$CLUSTER_NAME' exists and is READY."
    else
        echo "Cluster '$CLUSTER_NAME' exists but is in state: $STATUS"
    fi
else
    echo "Cluster '$CLUSTER_NAME' does not exist."
fi

if [[  $(is_positive $cluster_exists) == 0 ]]; then
  info "Cluster '$CLUSTER_NAME' already exists. Skipping cluster creation."
  result=0
else
  rosa create cluster --sts --oidc-config-id $OIDC_CONFIG_ID --cluster-name=$CLUSTER_NAME --replicas=$WORKER_NODE_COUNT --sts --mode=auto --hosted-cp --subnet-ids=$PRIVATE_SUBNET,$PUBLIC_SUBNET --compute-machine-type $MACHINE_POOL_TYPE --role-arn=$INSTALLER_ROLE --support-role-arn=$SUPPORT_ROLE --worker-iam-role=$WORKER_ROLE
  result=$?
fi


if [[ $(is_positive $cluster_exists) == 0 ]]; then

  if [[ $result != "0" ]]; then
    error "ROSA failed to create a cluster"
    result=1
    failed_to_create_cluster=0
    stop_when_error_happened $result $index_role_name $REPORT_FILE
  else
    info "The ROSA cluster has been created. Please wait until it's ready!"
  fi

  if [[ $failed_to_create_cluster != 0 ]]; then
    # Function to check the cluster status
    check_cluster_status() {
      rosa describe cluster -c "$CLUSTER_NAME" --output json | jq -r '.status.state'
    }

    # Periodically check the cluster status. (60m)
    # Retry logic variables
    MAX_RETRIES=60
    RETRY_INTERVAL=60 # Interval between retries in seconds
    RETRY_COUNT=0

    # Infinite loop to check the cluster status
    while true; do
      STATUS=$(check_cluster_status)
      RETRY_COUNT=$((RETRY_COUNT + 1))

      info "Attempt ${RETRY_COUNT} of $MAX_RETRIES."

      case "$STATUS" in
      "ready")
        success "The ROSA cluster is now ready!"
        result=0
        break
        ;;
      "error")
        error "Cluster status: $STATUS."
        rosa describe cluster -c "$CLUSTER_NAME" --output json
        result=1
        stop_when_error_happened $result $index_role_name $REPORT_FILE
        ;;
      *)
        info "Cluster status: $STATUS. Waiting for it to become ready..."
        ;;
      esac

      if ((RETRY_COUNT >= MAX_RETRIES)); then
        error "Cluster failed to be created after $MAX_RETRIES attempts."
        result=1
        stop_when_error_happened $result $index_role_name $REPORT_FILE
      fi

      sleep $RETRY_INTERVAL
    done

    info "Add a openshift user($OCP_ADMIN_ID)"
    rosa create idp --cluster=$CLUSTER_NAME --type=htpasswd -u $OCP_ADMIN_ID:$OCP_ADMIN_PW --name htpasswd
    if [[ $? != 0 ]]; then
      error "Failed to create a default user"
      result=1
      stop_when_error_happened $result $index_role_name $REPORT_FILE
    fi

    info "add cluster-admin role to the user($OCP_ADMIN_ID)"
    rosa grant user cluster-admin --user=$OCP_ADMIN_ID --cluster=$CLUSTER_NAME
    if [[ $? != 0 ]]; then
      error "Failed to grant cluster-admin role to the default user"
      result=1
      stop_when_error_happened $result $index_role_name $REPORT_FILE
    fi
    sleep 10
    IsUserAdded=$(rosa list users --cluster=$CLUSTER_NAME | grep $OCP_ADMIN_ID | grep cluster-admin | wc -l)

    if [[ $IsUserAdded != 1 ]]; then
      error "Openshift cluster user failed to be added"
      rosa list users --cluster=$CLUSTER_NAME
      result=1
      stop_when_error_happened $result $index_role_name $REPORT_FILE
    else
      success "The OpenShift cluster-admin user has been successfully added."
    fi
  fi
fi

############# VERIFY #############
# check if cluster is created
# check if user is added with right permission

# Retry logic variables
MAX_RETRIES=30
RETRY_INTERVAL=60 # Interval between retries in seconds
RETRY_COUNT=0

# Function to get cluster info as JSON
check_cluster_json() {
  rosa describe cluster -c "$CLUSTER_NAME" --output json
}

# Infinite loop to check the cluster status
info "Verifying if the cluster has been created and the user has been added"
while true; do
  # Fetch cluster information
  cluster_info_json=$(check_cluster_json)
  RETRY_COUNT=$((RETRY_COUNT + 1))

  info "Attempt ${RETRY_COUNT} of $MAX_RETRIES."

  # Check if the retry count has exceeded the maximum limit
  if ((RETRY_COUNT > MAX_RETRIES)); then
    error "Failed to create the cluster after $MAX_RETRIES attempts."
    echo "${index_role_name}::1" >>"${REPORT_FILE}"
    break
  fi
  # Extract URLs from the JSON
  cluster_console_url=$(echo "$cluster_info_json" | jq -r '.console.url')
  cluster_api_url=$(echo "$cluster_info_json" | jq -r '.api.url')

  # Check if the console URL is present
  if [[ -z "$cluster_console_url" ]]; then
    error "[ERROR] Console URL not available yet. Waiting..."
    ((RETRY_COUNT++))
  else
    info "Cluster console URL: $cluster_console_url"

    # Check if the API URL is present
    if [[ $cluster_console_url == null ]]; then
      info "API URL not available yet. Waiting..."
    else
      info "Cluster API URL: $cluster_api_url"

      # Attempt to login to the cluster
      info "oc login -u $OCP_ADMIN_ID -p XXX --server $cluster_api_url --insecure-skip-tls-verify=true"
      oc login -u "$OCP_ADMIN_ID" -p "$OCP_ADMIN_PW" --server "$cluster_api_url" --insecure-skip-tls-verify=true
      oc_logined=$?
      if [[ $oc_logined -eq 0 ]]; then
        cluster_token=$(oc whoami -t)
        result=0
        break # Exit the loop since the cluster is successfully created
      else
        error "[ERROR] Login to OpenShift failed. Retrying..."
      fi
    fi
  fi

  sleep "$RETRY_INTERVAL"
done

if [[ $result == 0 ]]; then
  success "Loopy has verified that the OpenShift cluster ($CLUSTER_NAME) has been successfully created and the user ($OCP_ADMIN_ID) has been added"
else
  error "Failed to create OpenShift cluster($CLUSTER_NAME)"
fi

############# OUTPUT #############
echo "CLUSTER_CONSOLE_URL=${cluster_console_url}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_API_URL=${cluster_api_url}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_ID=${OCP_ADMIN_ID}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_ADMIN_PW=${OCP_ADMIN_PW}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_TOKEN=${cluster_token}" >>${OUTPUT_ENV_FILE}
echo "CLUSTER_TYPE=${CLUSTER_TYPE}" >>${OUTPUT_ENV_FILE}

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
