#!/usr/bin/env bash
if [[ $DEBUG == "0" ]]
then
  set -x
fi

root_directory=$1
current_dir=$2
role_name=$3
source $root_directory/src/commons/scripts/utils.sh


# Pre-requisites: opendatahub operator
oc get ns redhat-ods-operator
if [[ $? != 0 ]]
then
cat <<EOF| oc create -f -
apiVersion: v1
kind: Namespace
metadata:
  name: redhat-ods-operator
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: redhat-ods-operator
  namespace: redhat-ods-operator
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  labels:
    operators.coreos.com/rhods-operator.redhat-ods-operator: ""
  name: rhods-operator
  namespace: redhat-ods-operator
spec:
  channel: stable
  installPlanApproval: Automatic
  name: rhods-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

wait_for_csv_installed rhods-operator redhat-ods-operator
echo "Creating default dsci"
oc apply -f $root_directory/commons/manifests/opendatahub/dsci_3.yaml
fi
