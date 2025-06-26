#!/usr/bin/env bash

# Verification functions
verify_image_exists() {
  local image_url=$1
  info "Verifying if image exists: $image_url"
  
  if ${CONTAINER_CLI} manifest inspect $image_url >/dev/null 2>&1; then
    success "Image exists in registry: $image_url"
    return 0
  else
    error "Image does not exist in registry: $image_url" 
    return 1
  fi
}

verify_image_sha_match() {
  local target_image_full_url=$1
  info "Verifying image SHA match between local and remote"

  # Get remote image SHA using skopeo
  remote_sha=$(skopeo inspect docker://$target_image_full_url | jq -r '.Digest' 2>/dev/null)
  if [[ -z "$remote_sha" || "$remote_sha" == "null" ]]; then
    error "Failed to get remote image SHA"
    return 1
  fi

  # Get local image SHA
  local_sha=$(${CONTAINER_CLI} inspect $target_image_full_url | jq -r '.[0].Id' 2>/dev/null)
  if [[ -z "$local_sha" || "$local_sha" == "null" ]]; then
    error "Failed to get local image SHA"
    return 1
  fi

  if [[ "$remote_sha" == "$local_sha" ]]; then
    success "Image SHA matches between local and remote"
    return 0
  else
    error "Image SHA mismatch - Local: $local_sha, Remote: $remote_sha"
    return 1
  fi
}

verify_branch_pushed() {
  local branch_name="${TEST_MANIFEST_BRANCH}"
  local repo_dir=$1
  local user_name=$2
  local repo_name=$3
  
  cd $repo_dir
  
  if git remote show ${user_name} >/dev/null 2>&1; then 
    info "Username remote found: ${user_name}"
  else
    info "Username remote not found, using origin"
    user_name="origin"
  fi
  
  info "Verifying if branch is pushed to remote: $branch_name"
  
  # Check if branch exists on remote
  if git ls-remote --heads ${user_name} $branch_name | grep -q $branch_name; then
    success "Branch $branch_name exists on remote repository"
    git fetch --all
    # Check if local and remote commits match
    local_commit=$(git rev-parse HEAD)
    remote_commit=$(git rev-parse ${user_name}/$branch_name)
    
    if [[ "$local_commit" == "$remote_commit" ]]; then
      success "Local and remote commits match for branch $branch_name"
      return 0
    else
      error "Local and remote commits don't match for branch $branch_name"
      return 1
    fi
  else
    error "Branch $branch_name not found on remote repository"
    return 1
  fi
}

verify_image_url_updated() {
  local target_image_full_url=$1
  local component_name=$2
  local config_file="config/overlays/odh/params.env"
  local param_field_name="kserve-controller"
  if [[ ${component_name} != "kserve" ]]; then       
    config_file="config/base/params.env"
    param_field_name="odh-model-controller"
  fi    
  
  local expected_line="${param_field_name}=${target_image_full_url}"
  if [[ -n "${CUSTOM_IMAGE}" ]]; then
     expected_line="${param_field_name}=${CUSTOM_IMAGE}"
  fi

  info "Verifying if image URL is correctly updated in $config_file"
  
  if [[ -f "$config_file" ]]; then
    if grep -q "$expected_line" "$config_file"; then
      success "Image URL correctly updated in $config_file"
      info "  Expected: $expected_line"
      return 0
    else
      error "Image URL not found or incorrect in $config_file"
      error "  Expected: $expected_line"
      error "  Current content:"
      grep "${param_field_name}=" "$config_file" || error "  No controller line found"
      return 1
    fi
  else
    error "Configuration file not found: $config_file"
    return 1
  fi
}

# Function to run all verifications
run_all_verifications() {
  local target_image_full_url=$1
  local repo_dir=$2
  local component_name=$3
  local result=0
  
  info "Starting verification process..."
  
  # 1. Verify image exists in registry
  if ! verify_image_exists "$target_image_full_url"; then
    result=1
  fi
  
  # 2. Verify branch is pushed
  if ! verify_branch_pushed "$repo_dir" "$USER_NAME" "$component_name"; then
    result=1
    exit 1
  fi
  
  # 3. Verify image URL is updated in config
  if ! verify_image_url_updated "$target_image_full_url" "$component_name"; then
    result=1
  fi
  
  # Final verification result
  if [[ $result -eq 0 ]]; then
    success "All verifications passed successfully!"
  else
    error "One or more verifications failed!"
  fi
  
  return $result
} 