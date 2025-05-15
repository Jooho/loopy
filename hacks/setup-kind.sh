#!/bin/bash
cd /tmp

if [ "${TEST_ENV}" == "local" ]; then
    kind create cluster
fi

# For ingress
kubectl label node/kind-control-plane ingress-ready=true 
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/kind/deploy.yaml

# For OLM
kubectl create -f https://raw.githubusercontent.com/operator-framework/operator-lifecycle-manager/refs/heads/master/deploy/upstream/quickstart/crds.yaml
kubectl create -f https://raw.githubusercontent.com/operator-framework/operator-lifecycle-manager/refs/heads/master/deploy/upstream/quickstart/olm.yaml

# Wait for minio packagemanifest to appear
echo "Waiting for olm to be available..."
timeout=120  # seconds
interval=5
elapsed=0
while true; do
  count=$(kubectl get packagemanifests 2>/dev/null | grep -c minio || true)
  if [ "$count" -eq 1 ]; then
    echo "minio packagemanifest is available."
    break
  fi
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "Timed out waiting for minio packagemanifest."
    exit 1
  fi
  sleep $interval
  elapsed=$((elapsed + interval))
done
