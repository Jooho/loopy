#!/usr/bin/env bash

if [[ $DEBUG == "0" ]]
then 
  set -x 
fi  

root_directory=$1
current_dir=$2
role_name=$3
source $current_dir/test-variables.sh
source $root_directory/src/commons/scripts/utils.sh


kubectl patch DataScienceCluster dsc-test -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch dsci default-dsci -p '{"metadata":{"finalizers":[]}}' --type=merge
oc delete dsci,dsc --all --force

kubectl patch knativeServing knative-serving -n knative-serving -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch smcp data-science-smcp -n istio-system -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch servicemeshmemberrolls default -n istio-system -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch servicemeshmembers.maistra.io default -n knative-serving -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch servicemeshmembers.maistra.io default -n rhoai-serverless -p '{"metadata":{"finalizers":[]}}' --type=merge

oc delete validatingwebhookconfiguration  openshift-operators.servicemesh-resources.maistra.io validating.knativeeventings.operator.serverless.openshift.vq9sp validating.knativekafkas.operator.serverless.openshift.io-bm6kq validating.knativeservings.operator.serverless.openshift.ipfb7l
oc delete mutatingwebhookconfiguration mutating.knativeeventings.operator.serverless.openshift.io6pgl9 mutating.knativeservings.operator.serverless.openshift.io-4nn6p  openshift-operators.servicemesh-resources.maistra.io 

oc delete smcp data-science-smcp -n istio-system
oc delete servicemeshmemberrolls.maistra.io --all --force --grace-period=0 -n istio-system
oc delete subs servicemeshoperator -n openshift-operators 

oc delete knativeServing knative-serving -n knative-serving
oc delete pod --all -n rhoai-serverless --force --grace-period=0
oc delete subs serverless-operator -n rhoai-serverless

oc delete subs rhods-operator -n redhat-ods-operator


kubectl patch crd routes.serving.knative.dev -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch crd ingresses.networking.internal.knative.dev -p '{"metadata":{"finalizers":[]}}' --type=merge

for crd in $(oc get crd|grep knative |cut -d" " -f1)
  do oc delete crd $crd
done
for crd in $(oc get crd|grep istio |cut -d" " -f1)
  do oc delete crd $crd
done

sm_csv_name=$(oc get csv -n openshift-operators | grep servicemeshoperator|awk '{print $1}')
oc delete csv $sm_csv_name -n openshift-operators

sl_csv_name=$(oc get csv -n openshift-operators | grep serverless-operator|awk '{print $1}')
oc delete csv $sl_csv_name -n rhoai-serverless

oc delete project istio-system  --force --grace-period=0
oc delete project knative-serving  --force --grace-period=0
oc delete project knative-eventing  --force --grace-period=0
oc delete project rhoai-serverless  --force --grace-period=0
  
oc delete ns opendatahub redhat-ods-monitoring rhoai-serverless istio-system  redhat-ods-operator --force --grace-period=0

success "Clean up $role_name test"
