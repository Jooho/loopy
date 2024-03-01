# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/opendatahub-dsci
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/opendatahub-dsci.sh

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
