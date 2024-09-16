#!/bin/bash

# Set the color variable
red='\033[0;31m'
light_red='\033[0;91m'
cyan='\033[0;36m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
light_blue='\033[0;94m'
# Clear the color after that
clear='\033[0m'

# Set the color for log level
info=$cyan
warning=$yellow
error=$red
pending=$light_blue

die() {
  color_red='\e[31m'
  color_yellow='\e[33m'
  color_reset='\e[0m'
  printf "${color_red}FATAL:${color_yellow} $*${color_reset}\n"
  exit 1
}

light_info() {
  color_blue='\e[34m'
  color_reset='\e[0m'
  printf "${color_blue}$*${color_reset}\n"
}

info() {
  color_reset='\e[0m'
  printf "${cyan}$*${color_reset}\n"
}

error() {
  color_reset='\e[0m'
  printf "${error}$*${color_reset}\n"
}

success() {
  color_green='\e[32m'
  color_reset='\e[0m'
  printf "${color_green}$*${color_reset}\n"
}

pending() {
  printf "${pending}$*${color_reset}\n"
}

check_pod_status() {
  local -r JSONPATH="{range .items[*]}{'\n'}{@.metadata.name}:{@.status.phase}:{range @.status.conditions[*]}{@.type}={@.status};{end}{end}"
  local -r pod_selector="$1"
  local -r pod_namespace="$2"
  local pod_status
  local pod_entry

  pod_status=$(oc get pods -l $pod_selector -n $pod_namespace -o jsonpath="$JSONPATH")
  oc_exit_code=$? # capture the exit code instead of failing

  if [[ $oc_exit_code -ne 0 ]]; then
    # kubectl command failed. print the error then wait and retry
    echo "Error running kubectl command."
    echo $pod_status
    return 1
  elif [[ ${#pod_status} -eq 0 ]]; then
    echo -n "No pods found with selector $pod_selector in $pod_namespace. Pods may not be up yet."
    return 1
  else
    # split string by newline into array
    IFS=$'\n' read -r -d '' -a pod_status_array <<<"$pod_status"

    for pod_entry in "${pod_status_array[@]}"; do
      local pod=$(echo $pod_entry | cut -d ':' -f1)
      local phase=$(echo $pod_entry | cut -d ':' -f2)
      local conditions=$(echo $pod_entry | cut -d ':' -f3)
      if [ "$phase" != "Running" ] && [ "$phase" != "Succeeded" ]; then
        return 1
      fi
      if [[ $conditions != *"Ready=True"* ]]; then
        return 1
      fi
    done
  fi
  return 0
}

function wait_pod_containers_ready() {
  pod_label=$1
  namespace=$2
  checkcount=20
  tempcount=0
  while true; do
    pod_exist=$(oc get pod -l ${pod_label} -n ${namespace} --ignore-not-found)

    if [[ ${pod_exist} != '' ]]; then
      ready=$(oc get pod -l ${pod_label} -n ${namespace} --no-headers | head -1 | awk '{print $2}' | cut -d/ -f1)
      desired=$(oc get pod -l ${pod_label} -n ${namespace} --no-headers | head -1 | awk '{print $2}' | cut -d/ -f2)

      if [[ $ready == $desired ]]; then
        success "[SUCCESS] Pod(s) with label '${pod_label}' is(are) Ready!"
        break
      else
        pending "[PENDING] Pod(s) with label '${pod_label}' is(are) ${red}NOT${clear}${pending} Ready yet: $tempcount times"
        pending "[PENDING] Wait for 10 seconds"

        sleep 10
      fi
    else
      pending "[PENDING] Pod is NOT created yet"
      sleep 10
    fi

    tempcount=$((tempcount + 1))
    if [[ $checkcount == $tempcount ]]; then
      error "[ERROR] Pod(s) with label '${pod_label}' is(are) NOT Ready${clear}\n"
      exit 1
    fi
  done
}

wait_for_pods_ready() {
  local -r JSONPATH="{.items[*]}"
  local -r pod_selector="$1"
  local -r pod_namespace=$2
  local wait_counter=0
  local oc_exit_code=0
  local pod_status

  while true; do
    pod_status=$(oc get pods -l $pod_selector -n $pod_namespace -o jsonpath="$JSONPATH")
    oc_exit_code=$? # capture the exit code instead of failing

    if [[ $oc_exit_code -ne 0 ]]; then
      # kubectl command failed. print the error then wait and retry
      echo $pod_status
      echo -n "Error running kubectl command."
    elif [[ ${#pod_status} -eq 0 ]]; then
      echo -n "No pods found with selector '$pod_selector' -n '$pod_namespace'. Pods may not be up yet."
    elif check_pod_status "$pod_selector" "$pod_namespace"; then
      echo "All $pod_selector pods in '$pod_namespace' namespace are running and ready."
      return
    else
      echo -n "Pods found with selector '$pod_selector' in '$pod_namespace' namespace are not ready yet."
    fi

    if [[ $wait_counter -ge 30 ]]; then
      echo
      oc get pods -l $pod_selector -n $pod_namespace
      error "Timed out after $((30 * wait_counter / 60)) minutes waiting for pod with selector: $pod_selector"
      echo 1
      return
    fi

    wait_counter=$((wait_counter + 1))
    echo " Waiting 10 secs ..."
    sleep 10
  done
}

wait_for_pod_name_ready() {
  local pod_name="$1"
  local pod_namespace=$2

  oc status >>/dev/null
  if [[ $? != 0 ]]; then
    error "Cluster is not accessiable"
    echo 1
    return
  fi

  echo "Waiting for pod ${pod_name}"
  oc wait --for=condition=ready pod/${pod_name} -n $pod_namespace --timeout=300s
  if [[ $? == 0 ]]; then
    echo "The pod($pod_name) in '$pod_namespace' namespace are running and ready."
    return
  else
    error "Timed out after 300s waiting for pod($pod_name)"
    echo 1
    return
  fi
}

function wait_for_just_created_pod_ready() {
  local namespace=$1
  local wait_counter=0
  local created_pod_name=""

  while [[ ${created_pod_name} == '' ]]; do
    created_pod_name=$(oc get event -n $namespace | grep 'Started container manager' | grep -E '^[0-9]s' | grep -v -e '^[0-9]m' | awk '{print $4}' | cut -d'/' -f2)

    if [[ $wait_counter -ge 12 ]]; then
      echo
      oc get pods $pod_name -n $namespace
      exit 1
    fi
    echo "No pods created in $namespace. Pods may not be up yet."

    wait_counter=$((wait_counter + 1))
    echo "Waiting 5 secs ..."
    sleep 5

  done
  info "Catched 'Started container manager' event"

  wait_for_pod_name_ready $created_pod_name $namespace
}

function wait_for_csv_installed() {
  csv=$1
  namespace=$2
  ii=0
  echo
  echo "[START] Watching if CSV \"$csv\" is installed"
  csv_status=$(oc get csv -n $namespace 2>&1 | grep $csv | awk '{print $NF}')
  while [[ $csv_status != 'Succeeded' ]]; do
    echo -n "."
    ((ii = ii + 1))
    if [ $ii -eq 100 ]; then
      echo "CSV \"$csv\" is NOT installed and it exceeds maximum tries(300s)"
      echo "[FAILED] please check the CSV \"$csv\""
      exit 1
    fi
    sleep 3

    if [ $(expr $ii % 20) == "0" ]; then
      echo ""
      echo "CSV \"$csv\" is NOT installed yet"
    fi

    csv_status=$(oc get csv -n $namespace 2>&1 | grep $csv | awk '{print $NF}')
  done
  echo
  echo "[END] CSV \"$csv\" is successfully installed"
}

function oc::wait::object::availability() {
  local cmd=$1        # Command whose output we require
  local interval=$2   # How many seconds to sleep between tries
  local iterations=$3 # How many times we attempt to run the command

  ii=0
  echo "[START] Wait for \"${cmd}\" "
  while [ $ii -le $iterations ]; do

    token=$($cmd &>/dev/null) && returncode=$? || returncode=$?
    echo "$cmd " | sh

    if [ $returncode -eq 0 ]; then
      break
    fi

    ((ii = ii + 1))
    if [ $ii -eq 100 ]; then
      echo "${cmd} did not return a value$"
      exit 1
    fi
    sleep $interval
  done
  echo "[END] \"${cmd}\" is successfully done"
}

function oc::wait::return::true() {
  local cmd=$1        # Command whose output we require
  local interval=$2   # How many seconds to sleep between tries
  local iterations=$3 # How many times we attempt to run the command

  ii=0
  echo "[START] Wait for \"${cmd}\" "
  while [ $ii -le $iterations ]; do

    echo "$cmd " | sh

    if [ $? -eq 0 ]; then
      break
    fi

    ((ii = ii + 1))
    if [ $ii -eq 100 ]; then
      echo "${cmd} did not return a value$"
      exit 1
    fi
    sleep $interval
  done
  echo "[END] \"${cmd}\" return 'true' successfully"
}

function get_root_directory() {
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
    info "The root directory is: $root_directory"
    echo $root_directory
  else
    error "Error: Unable to find .github folder."
  fi
}

function is_positive() {
  input_val=$1

  if [[ $input_val == '0' || $input_val == "true" || $input_val == 'True' || $input_val == 'yes' || $input_val == 'Yes' || $input_val == 'y' || $input_val == 'Y' ]]; then
    echo 0
  elif [[ $input_val == '1' || $input_val == 'false' || $input_val == 'False' || $input_val == 'no' || $input_val == 'No' || $input_val == 'n' || $input_val == 'N' ]]; then
    echo 1
  else
    die "Input value(${input_val}) is not allowed text to check positive or not"
    echo 2
  fi
}

function check_if_result() {
  rc=$1
  if [[ $? != 0 ]]; then
    die "FAIL"
  else
    success "PASS"
  fi
}

function check_oc_status() {
  info "[INFO] Checking oc connection and user role"
  userName=$(oc whoami) && connected=$? || connected=$?

  if [[ ${connected} -eq '0' ]]; then
    groupNames=$(oc get group | grep ${userName} | awk '{print $1}')

    for groupName in $groupNames; do
      clusterAdmin=$(oc get clusterrolebindings -o json | jq '.items[] | select(.metadata.name| startswith("cluster-admin")) | .subjects[].name' | egrep "$userName|$groupName" | wc -l)
      if ((${clusterAdmin} >= 1)); then
        success "[PASS] You logged to the cluster as a cluster-admin"
        break
      else
        error "[FAIL] You logged to the cluster but you are not cluster-admin"
        light_info "        Please log in to your cluster as a cluster-admin"
        exit 1
      fi
    done
  else
    error "[FAIL] You are NOT logged to the cluster. Please log in to your cluster"
    exit 1
  fi
}

retry_if_http_code_is_not_200() {
  local retries=$1
  local interval=$2
  local result_var=$3
  shift 3
  local cmd=("$@")
  local result

  for ((i = 0; i < retries; i++)); do
    result=$("${cmd[@]}")
    if [[ $result == "200" ]]; then
      eval "$result_var=\"$result\""
      return 0
    else
      info "return code is not 200. retry"
      sleep $interval
    fi
  done
  eval "$result_var=\"$result\""
  return 1
}

function check_rosa_access() {
  info "[INFO] Checking ROSA access"
  # 1. does ~/.aws folder exist?
  if [ ! -d "$HOME/.aws" ]; then
    error "[FAIL] ~/.aws directory does not exist."
    exit 1
  fi

  # 2. does credentials file exist?
  if [ ! -f "$HOME/.aws/credentials" ]; then
    error "[FAIL]: credentials file does not exist in ~/.aws."
    exit 1
  fi

  # 3. does config file exist?
  if [ ! -f "$HOME/.aws/config" ]; then
    # if config does not exist, does AWS_REGION env parameter set?
    if [ -z "$AWS_REGION" ]; then
      error "[FAIL]: Neither config file exists in ~/.aws nor AWS_REGION environment variable is set."
      exit 1
    fi
  fi

  # 4. can rosa login?
  rosa login --token=$OCM_TOKEN

  if [[ $? != "0" ]]; then
    error "[FAIL] rosa login failed"
    exit 1
  fi

  # 5. can rosa list cluster?
  rosa list clusters > /dev/null

  if [[ $? != "0" ]]; then
    error "[FAIL] rosa can not list cluster. It would fail to create a new cluster"
    error "       please check region and permission"
    exit 1
  fi

  success "[SUCCESS] All checks passed!"
}
