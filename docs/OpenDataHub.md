# OpenDataHub Roles & Playbooks

This document provides a concise overview of useful roles and playbooks for working with OpenDataHub (ODH), designed to improve development efficiency and simplify common tasks.

---

## Role: `build-odh-operator`

**Description:**  
The `build-odh-operator` role allows you to easily build the OpenDataHub Operator image directly from an incubating branch. This simplifies the build process and helps developers save time while ensuring consistency.

**Pre-requisites**  
- `podman` installed on your local machine  
- Logged in to the registry `quay.io` before running this role  


**Detail Information**
Show role descriptoin (parameters)

```shell
loopy roles show build-odh-operator
```

**Usage**  
To run this role with Loopy, use the following command:
```bash
loopy roles run build-odh-operator \
  -p QUAY_NAME=jooholee \
  -p KSERVE_MANIFESTS_BRANCH_URL=https://github.com/jooho/kserve/tree/loopy-test-devflag \
  -p VERSION=2.34.9
```

---

## Role: `create-devflag`

**Description:**  
This role helps to create devflag branch and update kserve-controller/odh-model-controller image.
It supports 4 different use cases with different environment variable requirements.

**Pre-requisites**  
  - docker or podman on local
  - You have to setup SSH key to github before running this role.
  - You have to login to registry like dockerhub or quay.io before running this role.
  - curl and jq are required for PR source mode

**Detail Information**
Show role descriptoin (parameters)

```shell
loopy roles show create-devflag
```

**Usage**  
To run this role with Loopy, use the following command:
```bash
./loopy roles run create-devflag \
  -p USER_NAME=jooho \
  -p TARGET_USER_NAME=test \
  -p COMPONENT_NAME=kserve \
  -p TARGET_BRANCH_NAME=pr_branch \
  -p REGISTRY_URL=quay.io/jooholee
```

---

## Role: `kserve-odh-e2e-test`

**Description:**  
 This role help to run kserve e2e test. The default execution run modelserving test cases.


**Pre-requisites**  
- openshift cluster

**Detail Information**
Show role descriptoin (parameters)

```shell
loopy roles show kserve-odh-e2e-test
```

**Usage**  
To run this role with Loopy, use the following command:
```bash
./loopy roles run kserve-odh-e2e-test  \
-p CLUSTER_TYPE=OCP \
-p CLUSTER_API_URL=https://api.cluster-name.example.com:6443 \
-p CLUSTER_ADMIN_ID=admin \
-p CLUSTER_ADMIN_PW=password \
-p PYTEST_JIRA_TOKEN=pytest-jira-token \
-p MINIO_S3_SVC_URL=https://minio.minio.svc.cluster.local:9000 \
-p MINIO_ACCESS_KEY_ID=admin \
-p MINIO_SECRET_ACCESS_KEY=password \
-p PYTEST_PATH=tests/model_serving   
```
---

## Role: `minio-deploy`

**Description:**  
 MinIO is an open-source, high-performance object storage server built for cloud-native and containerized environments. It is compatible with Amazon S3 APIs, making it easy to integrate with existing S3-compatible applications and tools. MinIO is designed to be lightweight, scalable, and highly available, making it suitable for storing unstructured data such as images, videos, log files, backups, and more. It is often used as a standalone object storage solution or as part of a larger data infrastructure stack.


**Pre-requisites**  
- N/A

**Detail Information**
Show role descriptoin (parameters)

```shell
loopy roles show minio-deploy
```

**Usage**  
To run this role with Loopy, use the following command:
```bash
./loopy roles run minio -i /path/to/cluster.sh
  
```

 
