# # #!/bin/bash

# # # 주어진 문자열
# # input="name=a::value=b,name=c"

# # # ':' 문자를 기준으로 문자열을 분할하여 배열에 저장
# # IFS=',' read -ra parts <<< "$input"

# # # 배열 요소들을 반복하여 처리
# # for part in "${parts[@]}"; do
# #     # ':' 문자를 기준으로 name과 value 분리
# #     IFS='=' read -r name value <<< "${part//::/=}"

# #     # value가 존재할 때
# #     if [ -n "$value" ]; then
# #         echo "- name: $name"
# #         echo "  value: $value"
# #     else
# #         echo "- name: $name"
# #     fi
# # done
# #!/bin/bash

# # 주어진 문자열
# input="name=a::value=b,name=c"

# # ',' 문자를 기준으로 문자열을 분할하여 배열에 저장
# IFS=',' read -ra items <<< "$input"

# # 배열 요소들을 반복하여 처리
# for item in "${items[@]}"; do
#     # echo $item
#     if [[ "$item" == *"::"* ]]; then
#       IFS='::' read -ra name value <<< "$item"
#       for subitem in "${subitems[@]}"; do
#           echo $subitem
#           result+=("$subitem")
#       done
#     fi
#     # echo $subitems
#     # echo $result

#     # # '=' 문자를 기준으로 name과 value 분리
#     # IFS='=' read -r name value <<< "$item"

#     # # value가 존재할 때
#     # if [ -n "$value" ]; then
#     #     echo "- name: $name"
#     #     echo "  value: $value"
#     # else
#     #     echo "- name: $name"
#     # fi
# done


# source ./a.sh
# echo ${a}


# env_value="name=DISABLE_DSC_CONFIG"
# IFS='=' read -r name value <<< "$env_value"

# yq -i ".spec.config.env += [{\"$name\": \"$value\"}]" a.yaml
# env_value="name=DISABLE_DSC_CONFIG"

# '='를 기준으로 문자열을 분할하여 name과 value 추출

# 결과 출력
# echo "name: $name"
# echo "value: $value"

# new_dns_entries_string="minio.minio.svc.cluster.local,minio-minio.test"


# IFS=',' read -ra new_dns_entries <<< "$new_dns_entries_string"

# # 기존 INI 파일 복사하여 임시 파일 생성
# cp input.config temp.ini

# # 추가할 DNS 항목을 임시 파일에 추가
# index=${#new_dns_entries[@]}
# for dns_entry in "${new_dns_entries[@]}"; do
#     echo $dns_entry
#     sed -i "/^\[alt_names\]/a DNS.$index = $dns_entry" temp.ini
#     ((index--))
# done
# ROOT_CA_FILE_PATH=test
# echo "${ROOT_CA_FILE_PATH}"
#   if [[ ! -n ${ROOT_CA_FILE_PATH} ]]
#   # if [[ -n ${ROOT_CA_FILE_PATH} || -n ${CERT_FILE_PATH} || -n ${KEY_FILE_PATH} ]]
#   then
#     echo "Required values(ROOT_CA_FILE_PATH,CERT_FILE_PATH,KEY_FILE_PATH) are NOT inputed."
#     exit 1
#   fi
  
# yq -i eval '.spec.containers[0].volumeMounts += [{"name": "minio-tls", "mountPath": "/home/modelmesh/.minio/certs"}] | .spec.volumes += [{"name": "minio-tls", "projected": {"defaultMode": 420, "sources": [{"secret": {"items": [{"key": "minio.crt", "path": "public.crt"}, {"key": "minio.key", "path": "private.key"}, {"key": "root.crt", "path": "CAs/root.crt"}], "name": "minio-tls"}}]}}]'  /tmp/ms_cli/20240221_1334/artifacts/1-minio-deploy/minio.yaml

#!/bin/bash

# # 'reports' 파일을 읽기
# while IFS= read -r line; do
#   # 구분자 '::'로 나누어 배열에 저장
#   IFS='::' read -ra ADDR <<< "$line"
#   # 배열의 마지막 원소 접근
#   last_element=${ADDR[-1]}
#   # 마지막 원소가 0인지 확인
#   if [ "$last_element" == "0" ]; then
#     echo "Last element is 0"
#   else
#     echo "Last element is not 0"
#   fi
# done < "reports"

crt_content=/tmp/minio/minio_certs/cabundle.crt
crt_content=$(awk '{printf "%s\\n", $0}' /tmp/minio/minio_certs/cabundle.crt)
# crt_content=$(cat /tmp/minio/minio_certs/cabundle.crt| tr -d '\n' |sed 's/-----BEGIN CERTIFICATE-----/-----BEGIN CERTIFICATE-----\\\\n/g' |sed 's/-----E/\\\\n-----E/g')
echo $crt_content
# kubectl patch dscinitialization default-dsci --type='json' -p='[{"op":"replace","path":"/spec/trustedCABundle/customCABundle","value":"'"$(awk '{printf "%s\\n", $0}' /tmp/minio/minio_certs/cabundle.crt)"'"}]'
:
# kubectl patch dscinitialization default-dsci --type='json' -p '{"spec":{"trustedCABundle":{"customCABundle":"|"'"${crt_content}"'"}}}'
