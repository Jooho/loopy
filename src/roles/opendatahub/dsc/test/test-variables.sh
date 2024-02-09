# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_ENV_DIR=output
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/opendatahub
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/${OUTPUT_REPORT_FILE}
export OUTPUT_ENV_FILE=env

###########################
export CLUSTER_TYPE=ROSA
export DATASCIENCECLUSTER_NAME=dsc-test
export ENABLE_CODEFLARE=Removed
export ENABLE_DASHBOARD=Removed
export ENABLE_DATASCIENCEPIPELINES=Removed
export ENABLE_KSERVE=Managed
export ENABLE_KSERVE_KNATIVE=Managed
export ENABLE_MODELMESH=Removed
export ENABLE_RAY=Removed
export ENABLE_TRUSTYAI=Removed
export ENABLE_WORKBENCHES=Removed
export OPENDATAHUB_TYPE=rhoai
###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
