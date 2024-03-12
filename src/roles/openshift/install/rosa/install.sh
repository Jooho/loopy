#!/usr/bin/env bash
# Parameters:
#   1 - cluster type - OSIA or ROSA default is OSIA
#   2 - env file path - default rhoai_env_vars

# fast fail
set -e
set -o pipefail

cluster_tye="${1:-"OSIA"}"
env_file="${2:-"rhoai_env_vars"}"

script_dir_path=$(cd `dirname "${BASH_SOURCE[0]}"`; pwd -P)

function set_env_vars {
    unamestr=$(uname)
    if [ "$unamestr" = 'Linux' ]; then
      export $(grep -v '^#' $1 | xargs -d '\n')
    elif [ "$unamestr" = 'FreeBSD' ] || [ "$unamestr" = 'Darwin' ]; then
      export $(grep -v '^#' $1 | xargs -0)
    fi
}

set_env_vars $env_file

echo "### Using the ${TMP_WD} tmp working dir ####"
if [ "$cluster_tye" = 'OSIA' ]; then

  echo "### Starting OSIA cluster creation  ####"
  cd $TMP_WD
  TMP_WD=$(mktemp -d)
  git clone git@gitlab.cee.redhat.com:AICoE/osia-configuration.git
  cd osia-configuration
  git crypt unlock "${OSIA_CONFIGURATION_KEY_PATH}"
  sh provision.sh -n $CLUSTER_NAME 2>&1 | tee -a $HOME/.osia-install.log

  echo "### Finished to create OSIA cluster  ####"

elif [ "$cluster_tye" = 'ROSA' ]; then
  echo "### Starting ROSA cluster creation  ####"
  git crypt unlock "${ROSA_CONFIGURATION_KEY_PATH}"
  set_env_vars openshift/common/rosa_env_vars
  rosa create cluster --sts --oidc-config-id $OIDC_CONFIG_ID --cluster-name=$CLUSTER_NAME --sts --mode=auto --hosted-cp --subnet-ids=$PRIVATE_SUBNET,$PUBLIC_SUBNET --compute-machine-type $MACHINE_POOL_TYPE --role-arn=$INSTALLER_ROLE --support-role-arn=$SUPPORT_ROLE --worker-iam-role=$WORKER_ROLE 2>&1 | tee -a $HOME/.rosa-install.log
  echo "### Finished to create ROSA cluster  ####"

fi
echo "### Returning into the initial directory ####"
cd $script_dir_path