#!/bin/bash

# First step, grab your token in the Jenkins instance.
# - go to User/Configure/Add new Token, copy then save.
# To run this script use:
# ./uninstall.sh <JENKINS_USER> <JENKINS_USER_TOKEN> <USER_EMAIL>

# Check if yq command exists
if ! command -v yq &> /dev/null
then
    echo "yq could not be found"
    exit
fi

# Default values for parameters
ODS_CI_RUN_SCRIPT_ARGS="--extra-robot-args '-i ODS-127'"
CLUSTER_TYPE="selfmanaged"
TEST_CLUSTER="serving-ods-ci-fips-ms"
CLUSTER_ACTION_POST_EXECUTION="Delete"
TEST_PLATFORM="stage"
JENKINS_BASE_URL=""
USER=""
TOKEN=""

# Function to display help menu
display_help() {
    echo "Usage: $0 [option...]" >&2
    echo
    echo "   -u, --user                         Set Jenkins USER"
    echo "   -t, --token                        Set Jenkins USER TOKEN"
    echo "   -j, --job-url                      Set Jenkins JENKINS_JOB_URL - the full job url, including the job name, usually ends with /build."
    echo "   -a, --args                         Set ODS_CI_RUN_SCRIPT_ARGS"
    echo "   -c, --cluster-action               Set CLUSTER_ACTION_POST_EXECUTION"
    echo "   -ct, --cluster-type                Set CLUSTER_TYPE, possible values are managed and selfmanaged, defaults to selfmanaged."
    echo "   -n, --cluster                      Set TEST_CLUSTER - is the cluster name that will be deleted, defaults to ${TEST_CLUSTER}, comma separated."
    echo "   -tp, --test-platform               Set TEST_PLATFORM - available values are stage and prod, defaults to stage."
    echo "   -h, --help                         Display help menu"
    echo
    exit 1
}

# Parse command line arguments
while (( "$#" )); do
  case "$1" in
    -u|--user)
      USER="$2"
      if [ -z "$USER" ]; then
        echo "Jenkins user must be set."
        exit 1
      fi
      shift 2
      ;;
    -t|--token)
      TOKEN="$2"
      if [ -z "$TOKEN" ]; then
        echo "Jenkins token must be set."
        exit 1
      fi
      shift 2
      ;;
    -j|--job-url)
      JENKINS_JOB_URL="$2"
      if [ -z "$JENKINS_JOB_URL" ]; then
        echo "Jenkins job url must be set."
        exit 1
      fi
      JENKINS_BASE_URL=$(echo $JENKINS_JOB_URL | awk -F"/job" '{print $1}')
      echo "JENKINS_BASE_URL: $JENKINS_BASE_URL"
      shift 2
      ;;
    -a|--args)
      ODS_CI_RUN_SCRIPT_ARGS="$2"
      shift 2
      ;;
    -c|--cluster-action)
      CLUSTER_ACTION_POST_EXECUTION="$2"
      shift 2
      ;;
    -ct|--cluster-type)
      CLUSTER_TYPE="$2"
      shift 2
      ;;
    -n|--cluster)
      TEST_CLUSTER="$2"
      shift 2
      ;;
    -to|--test-platform)
      TEST_PLATFORM="$2"
      shift 2
      ;;
    -em|--email)
      JENKINS_USER_EMAIL="$2"
      shift 2
      ;;
    -h|--help)
      display_help
      ;;
    --) # end argument parsing
      shift
      break
      ;;
    -*|--*=) # unsupported flags
      echo "Error: Unsupported flag $1" >&2
      display_help
      ;;
    *) # preserve positional arguments
      PARAMS="$PARAMS $1"
      shift
      ;;
  esac
done
# set positional arguments in their proper place
eval set -- "$PARAMS"

# Check if variables are set
if [ -z "$USER" ] || [ -z "$TOKEN" ] || [ -z "$JENKINS_JOB_URL" ]; then
    echo "All Jenkins parameters must be set."
    exit 1
fi

# Add all parameters here, in order to pass them to the Jenkins job encoded
declare -a parameters_array=(
    "ODS_CI_RUN_SCRIPT_ARGS=$ODS_CI_RUN_SCRIPT_ARGS"
    "CLUSTER_ACTION_POST_EXECUTION=$CLUSTER_ACTION_POST_EXECUTION"
    "TEST_CLUSTERS=$TEST_CLUSTER"
    "CLUSTER_TYPE=$CLUSTER_TYPE"
    "TEST_PLATFORM=$TEST_PLATFORM"
)

#format the parameters
PARAMETERS=""
for parameter in "${parameters_array[@]}"; do
    echo $parameter
    # Encode parameters that contains spaces, quotes or commas
    IFS='=' read -r name value <<< "${parameter}"
    if [ ! -z "$value" ]; then
        value="$(echo "${value}" | sed "s/'/%27/g" | sed 's/ /%20/g'  | sed "s/,/%2C/g")"
        # If url_parameters is not empty, add an & before the parameter
        if [ -n "$PARAMETERS" ]; then
            PARAMETERS+="&"
        fi
        # Add the parameter to url_parameters
        PARAMETERS+="$name=$value"
    fi
done

# Get the Jenkins crumb
CRUMB=$(curl -s -k "$JENKINS_BASE_URL/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)" -u $USER:$TOKEN)
if [ -z "$CRUMB" ]; then
    echo "Failed to get Jenkins crumb."
    exit 1
fi

# Trigger the Jenkins build job, the url should end with "build"
response=$(curl -k -s -i -vv -X POST "${JENKINS_JOB_URL}WithParameters?${PARAMETERS}" -H "$CRUMB" -u "$USER:$TOKEN")

# Extract the queue location from the response headers
queue_location=$(echo "$response" | grep -Fi Location: | awk '{print $2}' | tr -d '\r')
if [ -z "$queue_location" ]; then
    echo "Failed to get queue location."
    exit 1
else
    echo "Job triggered successfully, queue location: $queue_location"
fi


# # Wait for the job to start and get the job ID
while true; do
    # Get the JSON data for the queued item
    queue_data=$(curl -k -s "${queue_location}api/json" -u "$USER:$TOKEN")

    # Check if the job has started
    if [ "$(echo "$queue_data" | jq -r .executable.url)" != "null" ]; then
        # Extract the job ID
        job_id=$(echo "$queue_data" | jq -r .executable.number)
        break
    fi

    # Wait before checking again
    sleep 1
done

echo "Job ID: $job_id"
BUILD_URL="${JENKINS_BASE_URL}/job/tools/job/openshift/job/cluster-operations"
# Get the initial console output
build_logs=$(curl -k -s "${BUILD_URL}/${job_id}/consoleText" -u "$USER:$TOKEN")

# Print the initial console output
echo "$build_logs"

# Poll the console output until the job is finished
while true; do
    # Get the job status
    job=$(curl -k -s "${BUILD_URL}/${job_id}/api/json" -u "$USER:$TOKEN")
    job_status=$(echo $job | jq -r .result)

    # Break the loop if the job is finished
    if [ "$job_status" == "SUCCESS" ]; then
        echo "Cluster ${TEST_CLUSTER} deleted."
        echo "SUCCESS" > ${ROLE_DIR}/result
        exit 0
    elif [ "$job_status" != "null" ]; then
        echo "JOB STATUS: $job_status"
        echo "$job_status" > ${ROLE_DIR}/result
        break
    fi

    # Get the new console output
    new_build_logs=$(curl -k -s "${BUILD_URL}/${job_id}/consoleText" -u "$USER:$TOKEN")

    # Print the new lines
    # Check if new logs are different from the previous logs
    if [[ "$new_build_logs" != "$build_logs" ]]; then
      # Print the new lines
      echo "${new_build_logs:$((${#build_logs}+1))}"
    fi
    # Update the build logs
    build_logs="$new_build_logs"
    echo ${build_logs} > ${ROLE_DIR}/build.log
    # Wait before polling the logs again
    sleep 2
done
