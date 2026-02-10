# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/opendatahub-dsc_3
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/opendatahub-dsc_3.sh

###########################
export CLUSTER_TYPE=ROSA
export DATASCIENCECLUSTER_NAME=dsc-test
export ENABLE_DASHBOARD=Removed
export ENABLE_KSERVE=Managed
export ENABLE_RAY=Removed
export ENABLE_TRUSTYAI=Removed
export ENABLE_WORKBENCHES=Removed
export ENABLE_TRAININGOPERATOR=Removed
export ENABLE_KUEUE=Removed
export ENABLE_MODELREGISTRY=Removed
export OPENDATAHUB_TYPE=rhoai
# v2 new components
export ENABLE_KSERVE_NIM=Removed
export MODELREGISTRY_NAMESPACE=odh-model-registries
export ENABLE_FEASTOPERATOR=Removed
export ENABLE_AIPIPELINES=Removed
export ENABLE_MLFLOWOPERATOR=Removed
export ENABLE_LLAMASTACKOPERATOR=Removed
###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
