# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/seaweedfs-deploy
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/seaweedfs-deploy.sh
###########################
export ACCESS_KEY_ID=admin
export SECRET_ACCESS_KEY=password
export SEAWEEDFS_NAMESPACE=seaweedfs
export SEAWEEDFS_IMAGE=quay.io/jooholee/model-seaweedfs:latest
export IMAGE_PULL_POLICY=Always
###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
