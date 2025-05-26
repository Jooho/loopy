import argparse
import os
from jproperties import Properties
from caikit_nlp_client import GrpcClient
from caikit_nlp_client import HttpClient

# Model Query
QUERY = "Translate to German:  My name is Arthur"


def infer(endpoint, protocol, port=80):
    model_name = "flan-t5-small-caikit"

    print(
        f"Using {protocol} protocol to infer the model {model_name} at {endpoint}:{port}"
    )

    if protocol == "grpc":
        grpc_client = GrpcClient(endpoint, port, verify=False)
        text = grpc_client.generate_text(model_name, QUERY, max_new_tokens=200)

    elif "http" in protocol:
        http_client = HttpClient(f"{protocol}://{endpoint}:{port}", verify=False)
        text = http_client.generate_text(model_name, QUERY, max_new_tokens=200)

    else:
        raise ValueError("Invalid protocol, use http or grpc")

    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CaKit Inference caller")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8080",
        type=str,
        help="Model endpoint, provide the " "endpoint without protocol.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="Model endpoint port, required for grpc protocol",
    )
    parser.add_argument(
        "-p",
        "--protocol",
        default="https",
        type=str,
        help="Infer the model using the selected protocol (http or grpc), default is http",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="the directory to write the endpoint file to",
        required=True,
    )

    args = parser.parse_args()
    endpoint = args.endpoint
    protocol = args.protocol
    port = args.port

    file_path = os.path.join(args.directory, "output-envs.properties")

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            configs = Properties()
            configs.load(f)
            # gets only the endpoint without the protocol
            endpoint = configs.get("endpoint-" + protocol).data.split("//")[-1]
            if protocol != "grpc" and protocol.startswith("http"):
                # override the protocol if the endpoint is already defining it
                protocol = configs.get("endpoint-" + protocol).data.split(":")[0]

    else:
        if args.protocol == "grpc" and args.port is None:
            raise ValueError("Port is required for grpc protocol")

    print(infer(endpoint, protocol, port))
