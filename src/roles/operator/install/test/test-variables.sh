# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/operator-install
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/operator-install.sh
###########################

export SUBSCRIPTION_NAME=opendatahub-operator
export CHANNEL=stable
export OPERATOR_NAMESPACE=openshift-operators
export INSTALL_APPROVAL=Automatic
export OPERATOR_NAME=opendatahub-operator
export CATALOGSOURCE_NAME=community-operators
export CATALOGSOURCE_NAMESPACE=openshift-marketplace
# export OPERATOR_VERSION="2.5.0"
export OPERATOR_VERSION="latest"
export OPERATOR_LABEL="name=error"
export OPERATOR_POD_PREFIX="opendatahub"

###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
