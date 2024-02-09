#!/bin/bash
set -o pipefail
set -o nounset
set -o errtrace
# set -x   #Uncomment this to debug script.

source "$(dirname "$(realpath "$0")")/../../../env.sh"

# Deploy Minio
ACCESS_KEY_ID=THEACCESSKEY

if [[ ! -d ${KSERVE_BASE_DIR} ]]
then
  mkdir ${KSERVE_BASE_DIR}
fi

if [[ ! -d ${KSERVE_BASE_CERT_DIR} ]]
then
  mkdir ${KSERVE_BASE_CERT_DIR}
fi

## Check if ${KSERVE_MINIO_NS} exist
oc get ns ${KSERVE_MINIO_NS}
if [[ $? ==  1 ]]
then
  oc new-project ${KSERVE_MINIO_NS}
  SECRET_ACCESS_KEY=$(openssl rand -hex 32)
  sed "s/<accesskey>/$ACCESS_KEY_ID/g"  ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/minio.yaml | sed "s+<secretkey>+$SECRET_ACCESS_KEY+g" | tee ${KSERVE_BASE_DIR}/minio-current.yaml | oc -n ${KSERVE_MINIO_NS} apply -f -
  sed "s/<minio_ns>/$KSERVE_MINIO_NS/g" ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/minio-secret-json.yaml  | tee ${KSERVE_BASE_DIR}/minio-secret-json-current.yaml | oc -n ${KSERVE_MINIO_NS} apply -f - 
  sed "s/<accesskey>/$ACCESS_KEY_ID/g" ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/minio-secret-annotation.yaml | sed "s+<secretkey>+$SECRET_ACCESS_KEY+g" |sed "s/<minio_ns>/$KSERVE_MINIO_NS/g" | tee ${KSERVE_BASE_DIR}/minio-secret-annotation-current.yaml | oc -n ${KSERVE_MINIO_NS} apply -f - 
else
  SECRET_ACCESS_KEY=$(oc get pod minio  -n minio -ojsonpath='{.spec.containers[0].env[1].value}')
  sed "s/<accesskey>/$ACCESS_KEY_ID/g"  ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/minio.yaml | sed "s+<secretkey>+$SECRET_ACCESS_KEY+g" | tee ${KSERVE_BASE_DIR}/minio-current.yaml 
  sed "s/<accesskey>/$ACCESS_KEY_ID/g" ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/minio-secret-annotation.yaml | sed "s+<secretkey>+$SECRET_ACCESS_KEY+g" |sed "s/<minio_ns>/$KSERVE_MINIO_NS/g" | tee ${KSERVE_BASE_DIR}/minio-secret-annotation-current.yaml 
  sed "s/<minio_ns>/$KSERVE_MINIO_NS/g" ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/minio-secret-json.yaml | tee ${KSERVE_BASE_DIR}/minio-secret-json-current.yaml 
fi
sed "s/<minio_ns>/$KSERVE_MINIO_NS/g" ${KSERVE_CUSTOM_MANIFESTS_DIR}/minio/serviceaccount-minio.yaml | tee ${KSERVE_BASE_DIR}/serviceaccount-minio-current.yaml 
