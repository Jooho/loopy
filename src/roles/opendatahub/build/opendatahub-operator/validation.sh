#!/bin/bash

# Validation functions for opendatahub-operator build process
source $root_directory/src/commons/scripts/utils.sh
# Function to validate GitHub branch exists
validate_github_branch() {
  local repo_url=$1
  local username=$2
  local branch_name=$3
  
  # Extract repository name from URL (assuming format: https://github.com/username/repo)
  local repo_name=$(echo $repo_url | cut -d'/' -f5)
  
  # Check if branch exists using GitHub API
  if curl -s -f "https://api.github.com/repos/${username}/${repo_name}/branches/${branch_name}" > /dev/null 2>&1; then
    info "Branch '${branch_name}' exists in repository ${username}/${repo_name}"
    return 0
  else
    error "Branch '${branch_name}' does not exist in repository ${username}/${repo_name}"
    return 1
  fi
}



# Function to validate Quay.io images exist and were pushed within specified time (default: 2 minute)
validate_quay_images_recent() {
  local quay_name=$1
  local version=$2
  local max_age_minutes=${3:-2}  # Default to 2 minute if not specified
  
  # Define image to tag mapping
  declare -A image_tag_map=(
    ["opendatahub-operator"]="${version}"
    ["opendatahub-operator-bundle"]="v${version}"
    ["opendatahub-operator-index"]="${version}"
  )
  
  local current_time=$(date +%s)
  local max_age_seconds=$((max_age_minutes * 60))
  local missing_images=()
  local old_images=()
  
  # Iterate over image names and their corresponding tags
  for image_name in "${!image_tag_map[@]}"; do
    local tag="${image_tag_map[$image_name]}"
    
    # Use the tags parameter to get specific tag information without authentication
    local api_response=$(curl -s "https://quay.io/api/v1/repository/${quay_name}/${image_name}?tags=${tag}")
    
    if [[ $? -eq 0 && -n "$api_response" ]]; then
      # Check if we got an error response
      if echo "$api_response" | grep -q "error"; then
        warn "Cannot access repository ${quay_name}/${image_name}:${tag}"
        missing_images+=("${image_name}:${tag}")
        continue
      fi
      
      # Check if the specific tag exists in the response
      local tag_exists=$(echo "$api_response" | jq -r ".tags.\"${tag}\" // empty" 2>/dev/null)
      
      if [[ -n "$tag_exists" && "$tag_exists" != "null" ]]; then
        info "Image ${quay_name}/${image_name}:${tag} exists in Quay.io"
        
        # Extract last_modified timestamp from the tag info
        local last_modified=$(echo "$api_response" | jq -r ".tags.\"${tag}\".last_modified // empty" 2>/dev/null)
        
        if [[ -n "$last_modified" && "$last_modified" != "null" ]]; then
          # Convert last_modified string to timestamp (format: "Thu, 14 Aug 2025 02:11:35 -0000")
          local timestamp=$(date -d "$last_modified" +%s 2>/dev/null)
          
          if [[ -n "$timestamp" && "$timestamp" -gt 0 ]]; then
            local image_age=$((current_time - timestamp))
            
            if [[ $image_age -le $max_age_seconds ]]; then
              info "Image ${quay_name}/${image_name}:${tag} was pushed ${image_age} seconds ago (within ${max_age_minutes} minute(s))"
            else
              local age_minutes=$((image_age / 60))
              warn "Image ${quay_name}/${image_name}:${tag} was pushed ${age_minutes} minute(s) ago (older than ${max_age_minutes} minute(s))"
              old_images+=("${image_name}:${tag}")
            fi
          else
            warn "Could not parse timestamp for ${quay_name}/${image_name}:${tag}"
          fi
        else
          warn "Could not determine last_modified time for ${quay_name}/${image_name}:${tag}"
        fi
      else
        warn "Image ${quay_name}/${image_name}:${tag} does not exist in Quay.io"
        missing_images+=("${image_name}:${tag}")
      fi
    else
      warn "Could not fetch API information for ${quay_name}/${image_name}:${tag}"
      missing_images+=("${image_name}:${tag}")
    fi
  done
  
  # Report results
  if [[ ${#missing_images[@]} -gt 0 ]]; then
    error "Missing images: ${missing_images[*]}"
    return 1
  fi
  
  if [[ ${#old_images[@]} -gt 0 ]]; then
    warn "Images that may be too old: ${old_images[*]}"
    return 1
  fi
  
  info "All images exist and are recent"
  return 0
}
