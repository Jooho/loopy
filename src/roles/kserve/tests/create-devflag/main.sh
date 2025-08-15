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
# Source additional function files
source "${current_dir}/validation.sh"
source "${current_dir}/build.sh"
source "${current_dir}/verify.sh"

index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)

###################
result=0
# cd $ROLE_DIR

# Validate pre-requisites
export CONTAINER_CLI=${CONTAINER_CLI:-podman}
if [[ ! $(command -v ${CONTAINER_CLI}) ]]; then
  error "${CONTAINER_CLI} is not installed."
  exit 1 # TODO: replace STOP_ON_ERROR with result=1
  result=1
fi

# Validate environment variables first
info "Validating environment variables"
if ! validate_env_vars ${root_directory}; then
  error "Validation failed"
  exit 1 # TODO: replace STOP_ON_ERROR with result=1
  result=1
fi

# Determine use case
use_case=""
if [[ -n "${PR_URL}" ]]; then
  use_case="PR_SOURCE"
elif [[ -n "${CUSTOM_IMAGE}" ]]; then
  use_case="CUSTOM_IMAGE"
elif [[ -n "${TARGET_USER_NAME}" && -n "${TARGET_BRANCH_NAME}" ]]; then
  use_case="REMOTE_SOURCE"
else
  use_case="LOCAL_SOURCE"
fi

# Setup git repository
GIT_PARENT_REPO_DIR="${ROLE_DIR}"
if [[ "$use_case" == "LOCAL_SOURCE" ]]; then
  GIT_PARENT_REPO_DIR="$(dirname ${ORIGINAL_DIR})"
fi
debug "ORIGINAL_DIR: ${ORIGINAL_DIR}"
debug "ROLE_DIR: ${ROLE_DIR}"
debug "GIT_PARENT_REPO_DIR: ${GIT_PARENT_REPO_DIR}"
setup_git_repo "$use_case" "$GIT_PARENT_REPO_DIR"
if [[ $? -ne 0 ]]; then
  error "Failed to setup git repository"
  exit 1
  result=1
fi

# Define required variables based on component
if [[ $COMPONENT_NAME == "kserve" ]]; then
  IMAGE_NAME="kserve-controller"
  ORIGINAL_IMAGE_FULL_URL="docker.io/library/${IMAGE_NAME}:latest"
  TARGET_IMAGE_FULL_URL="${REGISTRY_URL}/${IMAGE_NAME}:${CTRL_IMG_TAG}"
else
  IMAGE_NAME="odh-model-controller"
  ORIGINAL_IMAGE_FULL_URL="quay.io/${USER}/${IMAGE_NAME}:latest"
  TARGET_IMAGE_FULL_URL="${REGISTRY_URL}/${IMAGE_NAME}:${CTRL_IMG_TAG}"
fi

# Execute based on use case
if [[ "$use_case" == "CUSTOM_IMAGE" ]]; then
  # Case 4: Custom image - only update manifests, no image building
  TARGET_IMAGE_FULL_URL="${CUSTOM_IMAGE}"
else
  # Cases 1, 2, 3: Need to build and push image
  # Handle container image building and pushing
  info "Building image: ${TARGET_IMAGE_FULL_URL}"
  handle_image_build "$COMPONENT_NAME" "$GIT_PARENT_REPO_DIR" "$ORIGINAL_IMAGE_FULL_URL" "$TARGET_IMAGE_FULL_URL"
  if [[ $? -ne 0 ]]; then
    error "Failed to build image"
    exit 1
  fi
fi

cd $GIT_PARENT_REPO_DIR/${COMPONENT_NAME}
# Check and update controller image in params.env
update_manifests "$TARGET_IMAGE_FULL_URL" "$COMPONENT_NAME"
############# VERIFY #############
run_all_verifications "$TARGET_IMAGE_FULL_URL" "$GIT_PARENT_REPO_DIR/${COMPONENT_NAME}" "$COMPONENT_NAME"
result=$?

############# OUTPUT #############
# Generate output based on component type
TARBALL_URL="https://github.com/${USER_NAME}/${COMPONENT_NAME}/tarball/${TEST_MANIFEST_BRANCH}"

if [[ ${COMPONENT_NAME} == "kserve" ]]; then
  echo "CUSTOM_KSERVE_MANIFESTS=${TARBALL_URL}" >${OUTPUT_ENV_FILE}
else
  echo "CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS=${TARBALL_URL}" >${OUTPUT_ENV_FILE}
fi

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}
