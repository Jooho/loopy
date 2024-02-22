# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_ENV_DIR=output
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/cert
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/${OUTPUT_REPORT_FILE}
export OUTPUT_ENV_FILE=env

###########################

export SAN_LIST=minio.minio.svc.cluster.local,minio-minio.test

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
