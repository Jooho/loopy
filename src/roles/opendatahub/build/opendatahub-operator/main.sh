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

index_role_name=$(basename $ROLE_DIR)
role_name=$(yq e '.role.name' ${current_dir}/config.yaml)

###################
result=0

# Validate pre-requisites
export CONTAINER_CLI=podman
if [[ ! $(command -v ${CONTAINER_CLI}) ]]; then
  error "${CONTAINER_CLI} is not installed."
  exit 1 # TODO: replace STOP_ON_ERROR with result=1
  result=1
fi

if [[ -n "${KSERVE_MANIFESTS_BRANCH_URL}" ]]; then
  export KSERVE_USER_NAME=$(echo $KSERVE_MANIFESTS_BRANCH_URL | cut -d'/' -f4)  
  export KSERVE_BRANCH_NAME=$(echo $KSERVE_MANIFESTS_BRANCH_URL | cut -d'/' -f7)
  
  # Validate that the branch actually exists
  if ! validate_github_branch "$KSERVE_MANIFESTS_BRANCH_URL" "$KSERVE_USER_NAME" "$KSERVE_BRANCH_NAME"; then
    error "Invalid KSERVE_MANIFESTS_BRANCH_URL: Branch does not exist"
    exit 1 # TODO: replace STOP_ON_ERROR with result=1
    result=1
  fi
  export KSERVE_NEW_MANIFESTS="\"$KSERVE_USER_NAME:kserve:${KSERVE_BRANCH_NAME}:config\""     
else
  export KSERVE_NEW_MANIFESTS="\"opendatahub-io:kserve:release-v0.15:config\""     
fi

if [[ -n "${ODH_MODEL_CONTROLLER_MANIFESTS_BRANCH_URL}" ]]; then
  export ODH_MODEL_CONTROLLER_USER_NAME=$(echo $ODH_MODEL_CONTROLLER_MANIFESTS_BRANCH_URL | cut -d'/' -f4)
  export ODH_MODEL_CONTROLLER_BRANCH_NAME=$(echo $ODH_MODEL_CONTROLLER_MANIFESTS_BRANCH_URL | cut -d'/' -f7)
  
  # Validate that the branch actually exists
  if ! validate_github_branch "$ODH_MODEL_CONTROLLER_MANIFESTS_BRANCH_URL" "$ODH_MODEL_CONTROLLER_USER_NAME" "$ODH_MODEL_CONTROLLER_BRANCH_NAME"; then
    error "Invalid ODH_MODEL_CONTROLLER_MANIFESTS_BRANCH_URL: Branch does not exist"
    exit 1 # TODO: replace STOP_ON_ERROR with result=1
    result=1
  fi  
  export ODH_MODEL_CONTROLLER_NEW_MANIFESTS="\"$ODH_MODEL_CONTROLLER_USER_NAME:odh-model-controller:${ODH_MODEL_CONTROLLER_BRANCH_NAME}:config\""     
else
  export ODH_MODEL_CONTROLLER_NEW_MANIFESTS="\"opendatahub-io:odh-model-controller:main:config\""     
fi

if [[ -z "${VERSION}" ]]; then
  export VERSION=$(grep '^VERSION' Makefile | cut -d'=' -f2 | tr -d ' ')
fi

export IMAGE_TAG_BASE=quay.io/$QUAY_NAME/opendatahub-operator
export IMG=$IMAGE_TAG_BASE:$VERSION
export BUNDLE_IMG=$IMAGE_TAG_BASE-bundle:v$VERSION
export CATALOG_IMG=$IMAGE_TAG_BASE-index:$VERSION  


# Setup git repository
info "Cloning opendatahub-operator repository"
cd $ROLE_DIR
git clone --branch $ODH_OPERATOR_BRANCH https://github.com/opendatahub-io/opendatahub-operator.git 
cd opendatahub-operator

#update version
$ROLE_DIR/opendatahub-operator/.github/scripts/update-versions.sh $VERSION
sed -i "s|.*\[\"kserve\"\]=.*|    [\"kserve\"]=$KSERVE_NEW_MANIFESTS|"   $ROLE_DIR/opendatahub-operator/get_all_manifests.sh 
sed -i "s|.*\[\"odh-model-controller\"\]=.*|    [\"odh-model-controller\"]=$ODH_MODEL_CONTROLLER_NEW_MANIFESTS|"   $ROLE_DIR/opendatahub-operator/get_all_manifests.sh 
  

# 1. Operator Image build
make image

# 2. Bundle build and push
make bundle
make bundle-build bundle-push

# 3. Index(Catalog) Image build and push
make catalog-build catalog-push -e VERSION=v$VERSION -e CATALOG_IMG=$CATALOG_IMG   BUNDLE_IMGS=$BUNDLE_IMG

############# VERIFY #############
# Verify that all images exist in Quay.io and were pushed recently
info "Verifying images in Quay.io..."
if ! validate_quay_images_recent "$QUAY_NAME" "$VERSION" 2; then
  warn "Some images may be missing or older than expected. Time validation may be skipped due to authentication requirements."
  # Don't fail here, just warn - the images may exist but may not be fresh
  result=1
else
  info "All images were successfully pushed to Quay.io recently"
fi

############# OUTPUT #############
# Generate output based on component type
ODH_OPERATOR_CATALOG_IMG=$CATALOG_IMG
echo "ODH_OPERATOR_CATALOG_IMG=${CATALOG_IMG}" >${OUTPUT_ENV_FILE}

############# REPORT #############
echo "${index_role_name}::${result}" >>${REPORT_FILE}
