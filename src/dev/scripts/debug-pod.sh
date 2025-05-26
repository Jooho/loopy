#!/bin/bash

# Source utility functions
source "$(dirname "$0")/../../commons/scripts/utils.sh"

# Define allowed parameters
# NAME: Pod name (default: debug-pod)
# WITH_ISTIO: Enable Istio sidecar injection (default: false)
ALLOWED_PARAMS=("NAME" "WITH_ISTIO")

# Default values
WITH_ISTIO=${WITH_ISTIO:-false}
NAME=${NAME:-debug-pod}

# Validate parameters
if ! validate_script_params  "${ALLOWED_PARAMS[@]}"; then
    die "Parameter validation failed"
fi

# Function to clean up resources
cleanup() {
    local pod_name=$1
    echo "Cleaning up pod ${pod_name}..."
    kubectl delete pod ${pod_name} --ignore-not-found=true
    # Wait for pod to be fully deleted
    while kubectl get pod ${pod_name} 2>/dev/null; do
        sleep 1
    done
}

# Function to execute the pod creation
execute() {
    local pod_name=$1
    local with_istio=$2
    # Build the base kubectl run command
    local base_cmd="kubectl run ${pod_name} --image=registry.access.redhat.com/rhel7/rhel-tools"
    local cmd="${base_cmd}"

    # Add istio sidecar if requested
    if [ "${with_istio}" = "true" ]; then
        cmd="${cmd} --annotations=sidecar.istio.io/inject=\"true\""
    fi

    # Add the command to keep container running
    cmd="${cmd} -- tail -f /dev/null"

    # Execute the command
    eval ${cmd}
}

# Main execution
if [ "${CLEAN}" = "true" ]; then
    cleanup "${NAME}"
    exit 0
fi

execute "${NAME}" "${WITH_ISTIO}" 