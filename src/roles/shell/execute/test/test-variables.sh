# REQUIRED VARIABLES
export OUTPUT_ROOT_DIR=/tmp
export OUTPUT_REPORT_FILE=report
export OUTPUT_ENV_DIR=output
export ROLE_DIR=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/shell
export REPORT_FILE=${OUTPUT_ROOT_DIR}/${OUTPUT_ENV_DIR}/${OUTPUT_REPORT_FILE}
export OUTPUT_ENV_FILE=env

###########################

export COMMANDS="uname%%uname -n"


###############################
# Export these values to environmental variable.
# CLUSTER_API_URL
# CLUSTER_ADMIN_ID
# CLUSTER_ADMIN_PW
# or
# CLUSTER_API_URL
# CLUSTER_TOKEN
