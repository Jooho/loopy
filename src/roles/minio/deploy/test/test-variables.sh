# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/minio-deploy
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/minio-deploy.sh
###########################
export ACCESS_KEY_ID=admin
export SECRET_ACCESS_KEY=password
export MINIO_NAMESPACE=minio
export MINIO_IMAGE=quay.io/opendatahub/modelmesh-minio-examples:caikit-flan-t5  
export IMAGE_PULL_POLICY=Always
export ENABLE_SSL=false
###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
