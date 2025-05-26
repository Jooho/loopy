# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_ENV_DIR=output
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/opendatahub
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/${OUTPUT_REPORT_FILE}
export OUTPUT_ENV_FILE=env

###########################

export SUBSCRIPTION_NAME=opendatahub-operator
export CHANNEL=stable
export OPERATOR_NAMESPACE=openshift-operators
export INSTALL_APPROVAL=Automatic
export OPERATOR_NAME=opendatahub-operator
export CATALOGSOURCE_NAME=community-operators
export CATALOGSOURCE_NAMESPACE=openshift-marketplace

###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
