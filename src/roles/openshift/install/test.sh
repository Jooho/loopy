#!/usr/bin/env bash

# set -e 
# set -o pipefail
if [[ $DEBUG == "0" ]]
then 
  set -x 
fi  

## INIT START ##
# Get the directory where this script is located
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Traverse up the directory tree to find the .github folder
github_dir="$current_dir"
while [ ! -d "$github_dir/.github" ] && [ "$github_dir" != "/" ]; do
  github_dir="$(dirname "$github_dir")"
done

# If the .github folder is found, set root_directory
if [ -d "$github_dir/.github" ]; then
  root_directory="$github_dir"
  echo "The root directory is: $root_directory"
else
  echo "Error: Unable to find .github folder."
fi
## INIT END ##

#################################################################
source $root_directory/commons/scripts/utils.sh

# a=$(is_positive no)
# echo $a
output_file=$1
echo "TEST"

echo $output_file
echo "SUBSCRIPTION_NAME=$SUBSCRIPTION_NAME" > "$output_file"


cluster_console_url=https://console-openshift-console.apps.rosa.jooho.chbf.p3.openshiftapps.com
cluster_api_url=https://api.jooho.chbf.p3.openshiftapps.com:443
cluster_admin_id=joe
cluster_admin_pw=Redhat_0123456
cluster_token=sha256~2RD73aTiUJdDK-XgDyqbKLxuJmzAQ6xgxQwC_KNVB-s
############# OUTPUT #############
echo "CLUSTER_CONSOLE_URL=${cluster_console_url}" >> "$output_file"
echo "CLUSTER_API_URL=${cluster_api_url}" >> "$output_file"
echo "CLUSTER_ADMIN_ID=${cluster_admin_id}" >> "$output_file"
echo "CLUSTER_ADMIN_PW=${cluster_admin_pw}" >> "$output_file"
echo "CLUSTER_TOKEN=${cluster_token}" >> "$output_file"
