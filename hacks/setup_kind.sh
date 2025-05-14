#!/bin/bash
cd /tmp
kind create cluster

# For ingress
oc label node/kind-control-plane ingress-ready=true 
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/kind/deploy.yaml

# For OLM
oc create -f https://raw.githubusercontent.com/operator-framework/operator-lifecycle-manager/refs/heads/master/deploy/upstream/quickstart/crds.yaml
oc create -f https://raw.githubusercontent.com/operator-framework/operator-lifecycle-manager/refs/heads/master/deploy/upstream/quickstart/olm.yaml
