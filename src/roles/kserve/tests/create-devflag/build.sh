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
else
  echo "Error: Unable to find .github folder."
fi
source $root_directory/src/commons/scripts/utils.sh
## INIT END ##

# Function to check if branch exists
check_and_create_branch() {
  local branch_name=$1
  if git show-ref --verify --quiet refs/heads/$branch_name; then
    echo "Branch $branch_name already exists, skipping branch creation"
    return 0
  else
    git checkout -b $branch_name
    return $?
  fi
}

# Function to build and push image
build_and_push_image() {
  local make_target=$1
  local original_image_full_url=$2
  local target_image_full_url=$3  
 
  info "Building and pushing ${target_image_full_url} image..."
  
  CONTAINER_TOOL=${CONTAINER_CLI} ENGINE=${CONTAINER_CLI} make ${make_target}
  
  ${CONTAINER_CLI} tag ${original_image_full_url} ${target_image_full_url}
  ${CONTAINER_CLI} push ${target_image_full_url}
}

# Function to setup git repository and branch
setup_git_repo() {
  local use_case=$1
  local target_parent_directory=$2

  if [[ "${use_case}" != "LOCAL_SOURCE" ]]; then
    cd $target_parent_directory

    # Clone repository
    if [[ -d ${COMPONENT_NAME} ]]; then
      info "Repository ${COMPONENT_NAME} already exists, skipping clone"
    else
      info "Cloning ${COMPONENT_NAME} repository(git clone git@github.com:${USER_NAME}/${COMPONENT_NAME}.git)..."
      git clone git@github.com:${USER_NAME}/${COMPONENT_NAME}.git
      if [[ $? != 0 ]]; then
        error "Failed to clone ${COMPONENT_NAME}."
        return 1
      fi
    fi
    cd ${COMPONENT_NAME}
  else
    if [[ $(basename "$ORIGINAL_DIR") != ${COMPONENT_NAME} ]]; then
      error "This is not the ${COMPONENT_NAME} repository"
      return 1
    fi
  fi
  

  if [[ ${COMPONENT_NAME} == "kserve" ]]; then
    if [[ ! -d /tmp/kserve/config/overlays/odh ]]; then
      error "This is upstream kserve that does not support devflag"
      return 1
    fi
  fi
  # Set environment variables
  export REPO_URL=https://github.com/${USER_NAME}/${COMPONENT_NAME}.git
  export KO_DOCKER_REPO=${REGISTRY_URL}
    
  # Handle different source types
  case $use_case in
    "PR_SOURCE")
      info "Setting up PR source from: ${PR_URL}"
      export PR_REPO_URL=https://github.com/${PR_USER_NAME}/${COMPONENT_NAME}.git
      
      # Setup git remotes and fetch
      if ! git remote | grep -q "^${PR_USER_NAME}$"; then
        git remote add ${PR_USER_NAME} ${PR_REPO_URL}
        git fetch --all
      fi
      
      # Checkout PR branch for build
      git checkout -b ${PR_BRANCH_NAME}-for-devflag ${PR_USER_NAME}/${PR_BRANCH_NAME} 2>/dev/null || git checkout ${PR_BRANCH_NAME}-for-devflag
      ;;
      
    "REMOTE_SOURCE")
      info "Setting up remote source from: ${TARGET_USER_NAME}/${TARGET_BRANCH_NAME}"
      export TARGET_REPO_URL=https://github.com/${TARGET_USER_NAME}/${COMPONENT_NAME}.git
      
      # Setup git remotes and fetch
      git remote add ${TARGET_USER_NAME} ${TARGET_REPO_URL}
      git fetch --all
      
      # Checkout target branch for build
      git checkout -b ${TARGET_BRANCH_NAME}-for-devflag ${TARGET_USER_NAME}/${TARGET_BRANCH_NAME} 2>/dev/null || git checkout ${TARGET_BRANCH_NAME}-for-devflag
      ;;
      
    "LOCAL_SOURCE")
      info "Use local source for build"
      ;;
      
    "CUSTOM_IMAGE")
      info "Use custom image without build: ${CUSTOM_IMAGE}"    
      ;;
  esac
}

# Function to update manifest files
update_manifests() {
  local target_image_full_url=$1
  local component_name=$2

  kserve_params_file="config/overlays/odh/params.env"
  odh_model_controller_params_file="config/base/params.env"

  # Checkout a new branch "${TEST_MANIFEST_BRANCH}" for updating manifests
  # git checkout -b ${TEST_MANIFEST_BRANCH}  2>/dev/null || git checkout ${TEST_MANIFEST_BRANCH}
  check_and_create_branch ${TEST_MANIFEST_BRANCH}
  # Check and update controller image in params.env
  if [[ ${component_name} == "kserve" ]]; then
    if grep -q "$target_image_full_url" ${kserve_params_file}; then
      info "Controller image is already updated in params.env, skipping update"
    else
      # Update the controller image in params.env
      sed -i "s|^${component_name}-controller=.*|kserve-controller=${target_image_full_url}|g" ${kserve_params_file}
      info "Updated ${component_name}-controller image in params.env"
    fi
  else
      if grep -q "$target_image_full_url" ${odh_model_controller_params_file}; then
      info "Controller image is already updated in params.env, skipping update"
    else
      # Update the controller image in params.env
      sed -i "s|^${component_name}=.*|odh-model-controller=${target_image_full_url}|g" ${odh_model_controller_params_file}
      info "Updated ${component_name} image in params.env"
    fi
  fi
  
  # Commit and push changes
  git add .
  git commit -m "Update ${target_image_full_url} in params.env"
  git push -u origin ${TEST_MANIFEST_BRANCH} -f
}

# Function to handle image building and pushing
handle_image_build() {
  local component_name=$1
  local target_parent_directory=$2
  local original_image_full_url=$3
  local target_image_full_url=$4
   
  local make_target="docker-build"
 
  if [[ $component_name != "kserve" ]]; then        
    make_target="container-build"
  fi

  cd $target_parent_directory/${component_name}
  build_and_push_image "$make_target" "$original_image_full_url" "$target_image_full_url"
} 
