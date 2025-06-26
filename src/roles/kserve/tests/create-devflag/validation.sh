#!/usr/bin/env bash


# Function to validate environment variables for different use cases
validate_env_vars() {
  root_directory=$1
  source $root_directory/src/commons/scripts/utils.sh
  local use_case=""
  local missing_vars=()
  local conflicting_vars=()
  
  # First, validate that only one use case is specified (mutually exclusive)
  local use_case_count=0
  
  # Check PR_SOURCE indicators
  if [[ -n "${PR_URL}" ]]; then
    use_case_count=$((use_case_count + 1))
    conflicting_vars+=("PR_URL")
  fi
  
  # Check CUSTOM_IMAGE indicators  
  if [[ -n "${CUSTOM_IMAGE}" ]]; then
    use_case_count=$((use_case_count + 1))
    conflicting_vars+=("CUSTOM_IMAGE")
  fi
  
  # Check REMOTE_SOURCE indicators
  if [[ -n "${TARGET_USER_NAME}" && -n "${TARGET_BRANCH_NAME}" ]]; then
    use_case_count=$((use_case_count + 1))
    conflicting_vars+=("TARGET_USER_NAME + TARGET_BRANCH_NAME")
  fi
  
  # Validate mutual exclusivity
  if [[ $use_case_count -gt 1 ]]; then
    error "Multiple use cases detected. Only one use case can be specified at a time."
    error "Conflicting variables found: ${conflicting_vars[*]}"
    echo ""
    echo "Use case definitions:"
    echo "- PR_SOURCE: PR_URL is set"
    echo "- CUSTOM_IMAGE: CUSTOM_IMAGE is set"
    echo "- REMOTE_SOURCE: Both TARGET_USER_NAME and TARGET_BRANCH_NAME are set"
    echo "- LOCAL_SOURCE: None of the above are set"
    echo ""
    return 1
  fi
  
  # Determine use case based on provided variables
  if [[ -n "${PR_URL}" ]]; then
    use_case="PR_SOURCE"
  elif [[ -n "${CUSTOM_IMAGE}" ]]; then
    use_case="CUSTOM_IMAGE"
  elif [[ -n "${TARGET_USER_NAME}" && -n "${TARGET_BRANCH_NAME}" ]]; then
    use_case="REMOTE_SOURCE"
  else
    use_case="LOCAL_SOURCE"
  fi
  
  info "Detected use case: $use_case"
  
  case $use_case in
    "REMOTE_SOURCE")
      # Case 1: Remote source
      local required_vars=("USER_NAME" "TARGET_USER_NAME" "COMPONENT_NAME" "TARGET_BRANCH_NAME" "REGISTRY_URL")
      ;;
    "PR_SOURCE")
      # Case 2: PR source 
      local required_vars=("USER_NAME" "PR_URL" "REGISTRY_URL")
      ;;
    "LOCAL_SOURCE")
      # Case 3: Local source 
      local required_vars=("USER_NAME" "REGISTRY_URL")
      ;;
    "CUSTOM_IMAGE")
      # Case 4: Custom image
      local required_vars=("USER_NAME" "COMPONENT_NAME" "CUSTOM_IMAGE" "REGISTRY_URL")
      ;;
  esac
  
  # Check if all required variables are set
  for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
      missing_vars+=("$var")
    fi
  done
  
  if [[ ${#missing_vars[@]} -gt 0 ]]; then
    error "Missing required environment variables for use case '$use_case':"
    for var in "${missing_vars[@]}"; do
      error "  - $var"
    done
    
    # Print usage examples
    echo ""
    echo "Usage examples:"
    echo ""
    echo "1. Remote source:"
    echo "   ./loopy roles run create-devflag \\"
    echo "     -p USER_NAME=jooho \\"
    echo "     -p TARGET_USER_NAME=test \\"
    echo "     -p COMPONENT_NAME=kserve \\"
    echo "     -p TARGET_BRANCH_NAME=pr_branch \\"
    echo "     -p REGISTRY_URL=quay.io/jooholee"
    echo ""
    echo "2. PR source:"
    echo "   ./loopy roles run create-devflag \\"
    echo "     -p USER_NAME=jooho \\"
    echo "     -p PR_URL=https://github.com/opendatahub-io/kserve/pulls/684 \\"
    echo "     -p REGISTRY_URL=quay.io/jooholee"
    echo ""
    echo "3. Local source:"
    echo "   ./loopy roles run create-devflag \\"
    echo "     -p USER_NAME=jooho \\"
    echo "     -p REGISTRY_URL=quay.io/jooholee"
    echo ""
    echo "4. Custom image:"
    echo "   ./loopy roles run create-devflag \\"
    echo "     -p USER_NAME=jooho \\"
    echo "     -p COMPONENT_NAME=kserve \\"
    echo "     -p CUSTOM_IMAGE=quay.io/jooholee/kserve-controller:loopy \\"
    echo "     -p REGISTRY_URL=quay.io/jooholee"
    echo ""
    
    error "Exiting due to missing required environment variables."
    return 1
  fi
  
  success "All required environment variables are set for use case '$use_case'"
  
  # Set derived variables based on use case
  case $use_case in
    "PR_SOURCE")
      # Extract component name and PR details from PR_URL
      if [[ $PR_URL =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
        PR_OWNER="${BASH_REMATCH[1]}"
        COMPONENT_NAME="${BASH_REMATCH[2]}"
        PR_NUMBER="${BASH_REMATCH[3]}"
        info "Extracted from PR_URL: PR_OWNER=$PR_OWNER, COMPONENT_NAME=$COMPONENT_NAME, PR_NUMBER=$PR_NUMBER"
        
        # Get PR details using GitHub API
        if command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
          PR_INFO=$(curl -s "https://api.github.com/repos/${PR_OWNER}/${COMPONENT_NAME}/pulls/${PR_NUMBER}")
          PR_USER_NAME=$(echo "$PR_INFO" | jq -r '.head.repo.owner.login')
          PR_BRANCH_NAME=$(echo "$PR_INFO" | jq -r '.head.ref')
          info "PR details: PR_USER_NAME=$PR_USER_NAME, PR_BRANCH_NAME=$PR_BRANCH_NAME"
        else
          error "curl and jq are required for PR source mode"
          return 1
        fi
      else
        error "Invalid PR_URL format. Expected format: https://github.com/user/repo/pull/number"
        return 1
      fi
      ;;
    "LOCAL_SOURCE")
      base_dir=$(basename ${ORIGINAL_DIR})    
      export COMPONENT_NAME="${base_dir}"
    
      info "Using COMPONENT_NAME=$COMPONENT_NAME for local source"
      ;;
    "REMOTE_SOURCE")
      info "Using remote source: TARGET_USER_NAME=$TARGET_USER_NAME, TARGET_BRANCH_NAME=$TARGET_BRANCH_NAME"
      ;;
  esac
  
  # Set common derived variables
  export TAG=${CTRL_IMG_TAG}
  export CONTAINER_CLI=${CONTAINER_CLI:-podman}
  
  return 0
} 