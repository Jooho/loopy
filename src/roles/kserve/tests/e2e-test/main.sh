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

cd $ROLE_DIR
# Clone opendatahub-tests
  if [[ ! -d "opendatahub-tests" ]]; then
    git clone git@github.com:opendatahub-io/opendatahub-tests.git
  fi
  cd opendatahub-tests
#cd /tmp/opendatahub-tests

result=1 # 0 is "succeed", 1 is "fail"
if [[ ${CLUSTER_TYPE} != "KIND" ]]; then
  oc login --username=${CLUSTER_ADMIN_ID} --password=${CLUSTER_ADMIN_PW} --server=${CLUSTER_API_URL}
  check_oc_status
fi

export DOMAIN=$(oc get ingresses.config.openshift.io cluster -o jsonpath='{.spec.domain}')


if [[ $(which oc) >/dev/null ]]; then
  oc_path=$(which oc)
else
  oc_path=$root_directory/bin/oc
fi

# Set environment variables
export OC_BINARY_PATH=$oc_path
export CI_S3_BUCKET_NAME=ods-ci-s3
export CI_S3_BUCKET_ENDPOINT=${MINIO_ODS_CI_S3_SVC_URL}.${DOMAIN}
export CI_S3_BUCKET_REGION=us-east-1
export MODELS_S3_BUCKET_NAME=ods-ci-wisdom
export MODELS_S3_BUCKET_ENDPOINT=${MINIO_ODS_CI_WISDOM_SVC_URL}.${DOMAIN}
export MODELS_S3_BUCKET_REGION=us-east-2
export AWS_ACCESS_KEY_ID=${MINIO_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${MINIO_SECRET_ACCESS_KEY}
export PYTEST_JIRA_TOKEN=${PYTEST_JIRA_TOKEN}
export PYTEST_JIRA_URL=https://issues.redhat.com

# Create ldap secret
oc get ns openldap >/dev/null 2>&1 || oc create ns openldap

# Check if openldap secret exists and update or create accordingly
if oc get secret openldap -n openldap >/dev/null 2>&1; then
  # Secret exists, get existing values
  existing_users=$(oc get secret openldap -n openldap -o jsonpath='{.data.users}' | base64 -d)
  existing_passwords=$(oc get secret openldap -n openldap -o jsonpath='{.data.passwords}' | base64 -d)
  
  # Check if the user already exists
  IFS=',' read -ra users_array <<< "${existing_users}"
  user_exists=false
  for user in "${users_array[@]}"; do
    if [[ "${user}" == "${CLUSTER_ADMIN_ID}" ]]; then
      user_exists=true
      break
    fi
  done
  
  if [[ "${user_exists}" == "false" ]]; then
    # Add new user and password to existing lists
    if [[ -n "${existing_users}" ]]; then
      new_users="${existing_users},${CLUSTER_ADMIN_ID}"
      new_passwords="${existing_passwords},${CLUSTER_ADMIN_PW}"
    else
      new_users="${CLUSTER_ADMIN_ID}"
      new_passwords="${CLUSTER_ADMIN_PW}"
    fi
    
    # Update the secret with new values
    oc patch secret openldap -n openldap --type='json' \
      -p="[{\"op\": \"replace\", \"path\": \"/data/users\", \"value\":\"$(echo -n ${new_users} | base64 -w 0)\"}, \
          {\"op\": \"replace\", \"path\": \"/data/passwords\", \"value\":\"$(echo -n ${new_passwords} | base64 -w 0)\"}]"
    
    info "Added user ${CLUSTER_ADMIN_ID} to existing openldap secret"
  else
    info "User ${CLUSTER_ADMIN_ID} already exists in openldap secret"
  fi
else
  # Secret doesn't exist, create new one
  oc create secret generic openldap -n openldap --from-literal=users=${CLUSTER_ADMIN_ID} --from-literal=passwords=${CLUSTER_ADMIN_PW}
  info "Created new openldap secret with user ${CLUSTER_ADMIN_ID}"
fi


if [[ ${CLUSTER_ADMIN_ID} != "user" ]]; then
  line_number=$(grep -n "first_user_index" tests/conftest.py| head -1|cut -d':' -f1)

  sed -i "${line_number}s+\"user\"+\"${CLUSTER_ADMIN_ID}\"+g" tests/conftest.py
fi

# Run pytest
if [[ ${PYTEST_MARKER} != "" ]]; then
  echo "uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -m \"${PYTEST_MARKER}\" -s"
  uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -m "${PYTEST_MARKER}" -s
else
  echo "uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -s"
  uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -s --pdb
fi

#if [[ ${PYTEST_MARKER} != "" ]]; then
#  echo "uv run pytest --setup-show --tc=distribution:upstream /tmp/opendatahub-tests/${PYTEST_PATH} -m \"${PYTEST_MARKER}\" -s"
#  uv run pytest --setup-show --tc=distribution:upstream /tmp/opendatahub-tests/${PYTEST_PATH} -m "${PYTEST_MARKER}" -s
#else
#  echo "uv run pytest --setup-show --tc=distribution:upstream /tmp/opendatahub-tests/${PYTEST_PATH} -s"
#  uv run pytest --setup-show --tc=distribution:upstream /tmp/opendatahub-tests/${PYTEST_PATH} -s
#fi

############# VERIFY #############


############# OUTPUT #############


############# REPORT #############
echo "${index_role_name}::$?" >>${REPORT_FILE}
