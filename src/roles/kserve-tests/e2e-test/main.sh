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
export CI_S3_BUCKET_ENDPOINT="https://minio-minio.${DOMAIN}"
export CI_S3_BUCKET_REGION=us-east-1
export MODELS_S3_BUCKET_NAME=ods-ci-wisdom
export MODELS_S3_BUCKET_ENDPOINT="https://minio-minio.${DOMAIN}"
export MODELS_S3_BUCKET_REGION=us-east-2
export AWS_ACCESS_KEY_ID=${MINIO_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${MINIO_SECRET_ACCESS_KEY}
export PYTEST_JIRA_TOKEN=${PYTEST_JIRA_TOKEN}
export PYTEST_JIRA_URL=https://issues.redhat.com

# Create ldap secret
oc get ns openldap >/dev/null 2>&1 || oc create ns openldap
oc get secret openldap -n openldap >/dev/null 2>&1 || oc create secret generic openldap -n openldap --from-literal=users=${CLUSTER_ADMIN_ID} --from-literal=passwords=${CLUSTER_ADMIN_PW}

if [[ ${CLUSTER_ADMIN_ID} != "user" ]]; then
  line_number=$(grep -n "first_user_index" tests/conftest.py| head -1|cut -d':' -f1)

  sed -i "${line_number}s+\"user\"+\"${CLUSTER_ADMIN_ID}\"+g" tests/conftest.py
fi

# Run pytest
info "${PYTEST_MARKER}"
if [[ ${PYTEST_MARKER} != "" ]]; then
  echo "uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -m \"${PYTEST_MARKER}\" -s"
  uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -m "${PYTEST_MARKER}" -s
else
  echo "uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -s"
  uv run pytest --setup-show --tc=distribution:upstream $ROLE_DIR/opendatahub-tests/${PYTEST_PATH} -s
fi


############# VERIFY #############


############# OUTPUT #############


############# REPORT #############
echo "${index_role_name}::$?" >>${REPORT_FILE}
