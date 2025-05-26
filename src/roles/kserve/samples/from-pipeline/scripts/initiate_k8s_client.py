from kubernetes import client, config


def initiate_client(endpoint, token):

    # Create a Configuration object
    configuration = client.Configuration()

    # Set the OpenShift API server endpoint
    configuration.host = endpoint

    # Set the Bearer token for authentication
    configuration.api_key = {"authorization": "Bearer " + token}

    # ignore ssl
    configuration.verify_ssl = False

    # return the client using the custom configuration
    return client.ApiClient(configuration)
