# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_ENV_DIR=output
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/opendatahub
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/${OUTPUT_REPORT_FILE}


###########################
export CLUSTER_TYPE=ROSA
export OPENDATAHUB_TYPE=rhoai
export DATASCIENCECLUSTER_NAME=dsc-test
export ENABLE_MONITORING=Removed
export ENABLE_SERVICEMESH=Removed
###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
