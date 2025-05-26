# Creating a New Role in Loopy

This guide explains how to create a new role in the Loopy framework.

## Basic Structure

A role in Loopy follows this structure:

```
src/roles/
└── <group_name>/
    └── <sub_command>/
        ├── main.sh
        ├── config.yaml
        ├── files/
        └── test/
```

## Steps to Create a New Role

1. Create a new directory under `src/roles/` with the following structure:

   ```
   src/roles/<group_name>/<sub_command>/
   ```

   For example: `src/roles/cert/generate/`

2. Create the following files and directories:

   - `main.sh`: The main script that will be executed
   - `config.yaml`: Configuration file for the role
   - `files/`: Directory for any additional files needed by the role
   - `test/`: Directory for test files

3. Configure `config.yaml` with the following structure:

   ```yaml
   role:
     created_date: "YYYYMMDD"
     name: "role-name" # Optional: If not specified, defaults to "<group_name>-<sub_command>"
     files:
       # List any files needed by the role
     description: |
       Detailed description of what the role does

       pre-requirements:
         List any prerequisites here

       Input Environment:
         Description of required environment variables

       To run it:
         Example command to run the role
         # This section is mandatory and should provide a copy-paste ready command
         # Users should be able to directly use this command without modifications
     input_env:
       - name: ENV_VAR_NAME
         description: Description of the environment variable
     output_env:
       - name: OUTPUT_VAR_NAME
         description: Description of the output variable
         required: true/false
   ```

   Note: The `name` field in config.yaml is optional. If not specified, the role name will automatically be set to `<group_name>-<sub_command>`. If specified, it will override the default naming convention.

## Best Practices

1. Use clear, descriptive names for your group and sub-command
2. Document all input and output environment variables
3. Include example commands in the description
4. List any prerequisites or requirements
5. Keep the main.sh script focused on a single responsibility
6. Include appropriate test cases in the test/ directory

## Testing Requirements

Every role must include pytest-based unit tests

1. **If it needs cluster**

   - If your role requires a cluster environment for testing:
     - Use `tests/e2e/roles/cluster-tests` for cluster-based tests
     - Reference the `minio-deploy` folder structure as a template
     - Ensure tests can run in a cluster environment

2. **If it does not need cluster**
   - If your role requires a cluster environment for testing:
     - Use `tests/e2e/roles/non-cluster-tests` for non-cluster-based tests
     - Reference the `cert_generate` folder structure as a template
     - Ensure tests can run in a cluster environment

## Example

Here's a reference example from the `cert/generate` role:

```yaml
role:
  created_date: "20240215"
  name: cert-generate
  files:
    openssl-san: ./files/openssl-san.config
  description: |
    This role help to generate self singed certificate. 
    The default execution create a SAN certificate for minio

    pre-requirements:
      N/A

    Input Environment:
      The parameters include:
      - SAN_DNS_LIST: Set SAN DNS hostname
      - SAN_IP_LIST: Set SAN IP address

    To run it:
      ./loopy roles run cert-generate \
        -p SAN_DNS_LIST=minio.minio.svc.cluster \
        -p SAN_IP_LIST=192.0.0.1
```

## Running the Role

Once created, you can run your role using:

```bash
./loopy roles run <group_name>-<sub_command> [parameters]
```
