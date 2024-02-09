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


env_value="name=DISABLE_DSC_CONFIG"
IFS='=' read -r name value <<< "$env_value"

yq -i ".spec.config.env += [{\"$name\": \"$value\"}]" a.yaml
# env_value="name=DISABLE_DSC_CONFIG"

# '='를 기준으로 문자열을 분할하여 name과 value 추출

# 결과 출력
# echo "name: $name"
# echo "value: $value"
