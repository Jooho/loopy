# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/modelmesh-onnx
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/modelmesh-onnx.sh

###########################

export TEST_NAMESPACE=kserve-demo
export MINIO_ACCESS_KEY_ID=admin
export MINIO_SECRET_ACCESS_KEY=password
export MINIO_S3_SVC_URL=http://minio.minio.svc.cluster.local:9000
export MINIO_DEFAULT_BUCKET_NAME=modelmesh-example-models
export MINIO_REGION=us-east-2

###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
