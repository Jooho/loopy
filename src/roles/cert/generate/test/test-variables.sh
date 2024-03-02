# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_DATE=today
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/artifacts/cert-generate
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/${OUTPUT_REPORT_FILE}
export OUTPUT_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_DATE}/output
export OUTPUT_ENV_FILE=${OUTPUT_DIR}/cert-generate.sh
###########################

export SAN_DNS_LIST=minio.minio.svc.cluster.local,minio-minio.test,*.minio.svc
export SAN_IP_LIST=192.0.0.1

export ROOT_CA_CERT_NAME=root.crt
export ROOT_CA_KEY_NAME=root.key
export CERT_NAME=custom.crt
export KEY_NAME=custom.key
export CSR_NAME=custom.csr
export CN=custom
###############################
# Export these values to environmental variable.
# ROOT_CA_FILE_PATH
# CERT_FILE_PATH
# KEY_FILE_PATH
