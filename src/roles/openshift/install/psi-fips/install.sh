#!/bin/bash

# First step, grab your token in the Jenkins instance.
# - go to User/Configure/Add new Token, copy then save.
# To run this script use:
# ./install.sh <JENKINS_USER> <JENKINS_TOKEN> <JENKINS_JOB_URL>

# Check if yq command exists
if ! command -v yq &> /dev/null
then
    echo "yq could not be found"
    exit 1
fi

# Default values for parameters
PRODUCT="ODH"
ODS_CI_RUN_SCRIPT_ARGS="--extra-robot-args '-i ODS-127'"
ODS_RELEASE_VERSION="RHODS_2.8.0_GA"
TEST_ENVIRONMENT="PSI"
ENABLE_FIPS_IN_CLUSTER="true"
CLUSTER_ACTION_POST_EXECUTION="Retain Cluster Ready"
CLUSTER_TYPE="selfmanaged"
TESTBED_TO_USE="Create new OCP Cluster"
TEST_CLUSTER="ods-ci-fips-ms"
TEST_CLUSTER_DETAILS="regionOne,3,g.standard.xxl,4.14-latest,stable"
PSI_PARAMS="rhos-01,,,"
DEPLOY_RHODS_OPERATOR="true"
RHODS_DEPLOYMENT_TYPE="Cli"
OPERATOR_TYPE="RHODS Operator V2"
JENKINS_USER_EMAIL="email"
RHODS_BUILD_NUMBER=""
JENKINS_BASE_URL=""
JENKINS_USER=""
JENKINS_TOKEN=""
JENKINS_USER_EMAIL=""

# Function to display help menu
display_help() {
    echo "Usage: $0 [option...]" >&2
    echo
    echo "   -u, --user                         Set JENKINS_USER"
    echo "   -t, --token                        Set Jenkins JENKINS_TOKEN"
    echo "   -j, --job-url                      Set Jenkins JENKINS_JOB_URL - the full job url, including the job name, usually ends with /build."
    echo "   -p, --product                      Set PRODUCT - Available options are ODH and RHODS, default to ODH"
    echo "   -a, --args                         Set ODS_CI_RUN_SCRIPT_ARGS"
    echo "   -r, --release                      Set ODS_RELEASE_VERSION"
    echo "   -e, --environment                  Set TEST_ENVIRONMENT"
    echo "   -f, --fips                         Set ENABLE_FIPS_IN_CLUSTER"
    echo "   -c, --cluster-action               Set CLUSTER_ACTION_POST_EXECUTION"
    echo "   -ct, --cluster-type                Set CLUSTER_TYPE"
    echo "   -tb, --testbed                     Set TESTBED_TO_USE"
    echo "   -n, --cluster                      Set TEST_CLUSTER - is the cluster name, must be unique. Check first if there is a cluster already created."
    echo "   -d, --details                      Set TEST_CLUSTER_DETAILS"
    echo "   -pa, --params                      Set PSI_PARAMS"
    echo "   -o, --operator                     Set DEPLOY_RHODS_OPERATOR"
    echo "   -rdp, --rhods-deployment-type      Set RHODS_DEPLOYMENT_TYPE - Default to Cli"
    echo "   -ot, --operator-type               Set OPERATOR_TYPE - RHODS Operator V2"
    echo "   -em, --email                       Set JENKINS_USER_EMAIL - set if you want to receive an email when the job is finished."
    echo "   -b, --build                        Set ODS_BUILD_URL - To get an Errata release enter 'X.yy-latest' (e.g. 1.31-latest), or use 'brew.registry.redhat.io/rh-osbs/iib:RHODS_BUILD_NUMBER'. An empty value will fetch latest Errata release, The build number can be obtanined in the brew."
    echo "   -h, --help                         Display help menu"
    echo
    exit 1
}

# Parse command line arguments
while (( "$#" )); do
  case "$1" in
    -u|--user)
      JENKINS_USER="$2"
      if [ -z "$JENKINS_USER" ]; then
        echo "Jenkins user must be set."
        exit 1
      fi
      shift 2
      ;;
    -t|--token)
      JENKINS_TOKEN="$2"
      if [ -z "$JENKINS_TOKEN" ]; then
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
    -p|--product)
      PRODUCT="$2"
      shift 2
      ;;
    -a|--args)
      ODS_CI_RUN_SCRIPT_ARGS="$2"
      shift 2
      ;;
    -r|--release)
      ODS_RELEASE_VERSION="$2"
      shift 2
      ;;
    -e|--environment)
      TEST_ENVIRONMENT="$2"
      shift 2
      ;;
    -f|--fips)
      ENABLE_FIPS_IN_CLUSTER="$2"
      shift 2
      ;;
    -ct|--cluster-action)
      CLUSTER_ACTION_POST_EXECUTION="$2"
      shift 2
      ;;
    -ct|--cluster-type)
      CLUSTER_TYPE="$2"
      shift 2
      ;;
    -tb|--testbed)
      TESTBED_TO_USE="$2"
      shift 2
      ;;
    -n|--cluster)
      TEST_CLUSTER="$2"
      shift 2
      ;;
    -d|--details)
      TEST_CLUSTER_DETAILS="$2"
      shift 2
      ;;
    -pa|--params)
      PSI_PARAMS="$2"
      shift 2
      ;;
    -o|--operator)
      DEPLOY_RHODS_OPERATOR="$2"
      shift 2
      ;;
    -rdp|--rhods-deployment-type)
      RHODS_DEPLOYMENT_TYPE="$2"
      shift 2
      ;;
    -ot|--operator-type)
      OPERATOR_TYPE="$2"
      shift 2
      ;;
    -em|--email)
      JENKINS_USER_EMAIL="$2"
      shift 2
      ;;
    -b|--build)
      ODS_BUILD_URL="$2"
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
if [ -z "$JENKINS_USER" ] || [ -z "$JENKINS_TOKEN" ] || [ -z "$JENKINS_JOB_URL" ]; then
    echo "All Jenkins parameters must be set."
    exit 1
fi

# Add all parameters here, in order to pass them to the Jenkins job encoded
declare -a parameters_array=(
    "ODS_CI_RUN_SCRIPT_ARGS=$ODS_CI_RUN_SCRIPT_ARGS"
    "ODS_RELEASE_VERSION=$ODS_RELEASE_VERSION"
    "TEST_ENVIRONMENT=$TEST_ENVIRONMENT"
    "ENABLE_FIPS_IN_CLUSTER=$ENABLE_FIPS_IN_CLUSTER"
    "CLUSTER_ACTION_POST_EXECUTION=$CLUSTER_ACTION_POST_EXECUTION"
    "CLUSTER_TYPE=$CLUSTER_TYPE"
    "TESTBED_TO_USE=$TESTBED_TO_USE"
    "TEST_CLUSTER=$TEST_CLUSTER"
    "TEST_CLUSTER_DETAILS=$TEST_CLUSTER_DETAILS"
    "PSI_PARAMS=$PSI_PARAMS"
    "DEPLOY_RHODS_OPERATOR=$DEPLOY_RHODS_OPERATOR"
    "RHODS_DEPLOYMENT_TYPE=$RHODS_DEPLOYMENT_TYPE"
    "OPERATOR_TYPE=$OPERATOR_TYPE"
    "ODS_BUILD_URL=$ODS_BUILD_URL"
    "JENKINS_USER_EMAIL=$JENKINS_USER_EMAIL"
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
CRUMB=$(curl -s -k "$JENKINS_BASE_URL/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)" -u $JENKINS_USER:$JENKINS_TOKEN)
if [ -z "$CRUMB" ]; then
    echo "Failed to get Jenkins crumb."
    exit 1
fi

# Trigger the Jenkins build job, the url should end with "build"
response=$(curl -k -s -i -vv -X POST "${JENKINS_JOB_URL}WithParameters?${PARAMETERS}" -H "$CRUMB" -u "$JENKINS_USER:$JENKINS_TOKEN")

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
    queue_data=$(curl -k -s "${queue_location}api/json" -u "$JENKINS_USER:$JENKINS_TOKEN")

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
BUILD_URL="${JENKINS_BASE_URL}/job/rhods/job/rhods-smoke"
# Get the initial console output
build_logs=$(curl -k -s "${BUILD_URL}/${job_id}/consoleText" -u "$JENKINS_USER:$JENKINS_TOKEN")

# Print the initial console output
echo "$build_logs"

# Poll the console output until the job is finished
while true; do
    # Get the job status
    job_status=$(curl -k -s "${BUILD_URL}/${job_id}/api/json" -u "$JENKINS_USER:$JENKINS_TOKEN" | jq -r .result)

    # Break the loop if the job is finished
    if [ "$job_status" == "SUCCESS" ]; then
        # Download the file to a specific directory
        curl -k -s -O "/tmp/test-variables.yaml" "${BUILD_URL}/${job_id}/artifact/test-variables.yml" -u "$JENKINS_USER:$JENKINS_TOKEN"
        break
    elif [ "$job_status" != "null" ]; then
        echo "Job failed"
        exit 1
    fi

    # Get the new console output
    new_build_logs=$(curl -k -s "${BUILD_URL}/${job_id}/consoleText" -u "$JENKINS_USER:$JENKINS_TOKEN")

    # Check if new logs are different from the previous logs
    if [[ "$new_build_logs" != "$build_logs" ]]; then
      # Print the new lines
      echo "${new_build_logs:$((${#build_logs}+1))}"
    fi
    # Update the build logs
    build_logs="$new_build_logs"
    echo ${build_logs} >> ${REPORT_FILE}
    # Wait before polling the logs again
    sleep 2
done
