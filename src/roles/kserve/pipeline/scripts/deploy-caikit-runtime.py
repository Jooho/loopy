import argparse
import initiate_k8s_client as k8s_client
from kubernetes import client


def deploy_runtime(protocol, endpoint, token, namespace="pipeline-test"):
    # Specify the YAML definition for the custom object
    enable_http = True
    enable_grpc = False
    name = "caikit-tgis-runtime"
    container_port = [
        {"containerPort": 8080, "protocol": "TCP"}
    ]
    if protocol == "grpc":
        container_port = [
            {"containerPort": 8085, "protocol": "TCP", "name": "h2c"},
        ]
        enable_http = False
        enable_grpc = True
        name = name + "-grpc"

    custom_object = {
        "apiVersion": "serving.kserve.io/v1alpha1",
        "kind": "ServingRuntime",
        "metadata": {
            "name": name,
            "labels": {
                "pipeline": "caikit-pipeline-test",
            }
        },
        "spec": {
            "multiModel": False,
            "supportedModelFormats": [
                {
                    "autoSelect": True,
                    "name": "caikit",
                }
            ],
            "containers": [
                {
                    "name": "kserve-container",
                    "image": "quay.io/opendatahub/text-generation-inference:stable",
                    "command": ["text-generation-launcher"],
                    "args": ["--model-name=/mnt/models/artifacts/"],
                    "env": [
                        {"name": "TRANSFORMERS_CACHE", "value": "/tmp/transformers_cache"}
                    ],
                },
                {
                    "name": "transformer-container",
                    "image": "quay.io/opendatahub/caikit-tgis-serving:stable",
                    "env": [
                        {"name": "RUNTIME_LOCAL_MODELS_DIR", "value": "/mnt/models"},
                        {"name": "TRANSFORMERS_CACHE", "value": "/tmp/transformers_cache"},
                        {"name": "RUNTIME_GRPC_ENABLED", "value": "true" if enable_grpc else "false"},
                        {"name": "RUNTIME_HTTP_ENABLED", "value": "true" if enable_http else "false"},
                    ],
                    "ports": container_port,
                    "readinessProbe": {
                        "exec": {
                            "command": [
                                "python",
                                "-m",
                                "caikit_health_probe",
                                "readiness",
                            ]
                        }
                    },
                    "livenessProbe": {
                        "exec": {
                            "command": [
                                "python",
                                "-m",
                                "caikit_health_probe",
                                "liveness",
                            ]
                        }
                    },
                },
            ],
        },
    }

    openshift_api_client = k8s_client.initiate_client(endpoint, token)
    api_instance = client.CustomObjectsApi(openshift_api_client)
    group = 'serving.kserve.io'
    version = 'v1alpha1'
    plural = 'servingruntimes'

    return api_instance.create_namespaced_custom_object(
        group, version, namespace, plural, custom_object)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='CaKit Runtime Deployed - Note, this requires the RHOSAI deployed.')
    parser.add_argument('-p', '--protocol', default='http', type=str,
                        help='Infer the model using the selected protocol (http or grpc), default is http')
    parser.add_argument('-e', '--endpoint', type=str, help='OpenShift Endpoint API.')
    parser.add_argument('-t', '--token', type=str, help='OpenShift Endpoint API access token.')
    parser.add_argument('-n', '--namespace', type=str, default='', help='OpenShift namespace.')

    args = parser.parse_args()
    if args.endpoint is None:
        raise ValueError("OpenShift API endpoint is required.")
    if args.token is None:
        raise ValueError("OpenShift API token is required.")
    print(deploy_runtime(args.protocol, args.endpoint, args.token, args.namespace))

