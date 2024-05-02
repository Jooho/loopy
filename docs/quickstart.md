# Quick Start

## Setup
- Download loopy and download required cli binary
~~~
git clone   git@github.com:Jooho/loopy.git
cd loopy
make init
~~~

- Loopy health check
~~~
./loopy roles run shell-execute -p COMMANDS="echo 'LOOPY is Ready'"


*****************************************************************************************************************************
*                                                      ╦  ╔═╗╔═╗╔═╗╦ ╦                                                      *
*                                                      ║  ║ ║║ ║╠═╝╚╦╝                                                      *
*                                                      ╩═╝╚═╝╚═╝╩   ╩                                                       *
*                                                   ╔═╗┬ ┬┌┬┐┌┬┐┌─┐┬─┐┬ ┬                                                   *
*                                                   ╚═╗│ │││││││├─┤├┬┘└┬┘                                                   *
*                                                   ╚═╝└─┘┴ ┴┴ ┴┴ ┴┴└─ ┴                                                    *
*                                                 Run: Role(shell-execute)                                                  *
*                                        Loopy result dir: /tmp/ms_cli/20240405_1214                                        *
*                                       Report file: /tmp/ms_cli/20240405_1214/report                                       *
*                                                 Execution time: 0m 0.001s                                                 *
*****************************************************************************************************************************
+-------+---------------+---------+-----------+-----------------------------------------------------+
| Index |   Role Name   |  Result |    Time   |                        Folder                       |
+-------+---------------+---------+-----------+-----------------------------------------------------+
|   0   | shell-execute | Success | 0m 0.001s | /tmp/ms_cli/20240405_1214/artifacts/0-shell-execute |
+-------+---------------+---------+-----------+-----------------------------------------------------+
~~~

- Check result folder
  ~~~
  ls /tmp/ms_cli/20240405_1214 
  artifacts  output  report
  ~~~

- Check commands
  ~~~
  cat /tmp/ms_cli/20240405_1214/artifacts/shell-execute/commands.txt 
  ######## 0 command #######
  COMMAND: echo 'LOOPY is Ready'
  STDOUT: LOOPY is Ready
  ~~~

## Loopy with your cluster

- Create your cluster information
  ~~~
  cat cluster_info.sh
  CLUSTER_CONSOLE_URL=https://console-openshift-console.XXXX
  CLUSTER_API_URL=https://api.XXX:443
  CLUSTER_ADMIN_ID=admin
  CLUSTER_ADMIN_PW=password
  CLUSTER_TOKEN=sha256~XXX
  CLUSTER_TYPE=ROSA
  ~~~

- Quick test
~~~
./loopy roles run shell-execute -i ./cluster_info.sh -p COMMANDS="oc get pod" 
~~~


## Examples

### Operator

- Install serverless stable operator using *unit*
  ~~~
  ./loopy units run install-serverless-stable-operator  -i ./cluster_info.sh 
  ~~~

- Uninstall serverless using *role*
  ~~~
  ./loopy roles run operator-delete -i ./cluster_info.sh -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=openshift-serverless -p OPERATOR_NAME=serverless-operator
  ~~~


### Minio
- Install Minio
  ~~~
  ./loopy roles run minio-deploy -i ./cluster_info.sh 
  ~~~

- Install SSL Minio
  ~~~
  ./loopy roles run minio-deploy -p ENABLE_SSL="true" -i ./cluster_info.sh 
  ~~~

  
### Caikit
- Test caikit-tgis rest test
  ~~~
  ./loopy units run test-kserve-caikit-tgis-rest -i ./cluster_info.sh 
  ~~~


### KServe Sanity Test
- Install ossm,serverless,rhoai operators. Deploy kserve then test caikit-tgis runtime.
  ~~~
  ./loopy playbooks run odh-stable-kserve-serverless-simple-sanity-test-on-existing-cluster -i ./cluster_info.sh 
  ~~~ 

### KServe Sanity Test on fips cluster
- Install ossm,serverless,rhoai operators. Deploy kserve then test caikit-tgis runtime.
  ~~~
  cat fips.sh
  JENKINS_USER=user
  JENKINS_TOKEN=XXXX
  JENKINS_URL=https://X.X.example.com

  ./loopy playbooks run kserve-full-sanity-test-on-new-fips-cluster -i ./fips.sh
  ~~~ 


### Deploy KServe/Modelmesh with the latest odh/rhoai operator
- Deploy KServe Serverless 
  ~~~
  # ODH
  ./loopy playbooks run odh-stable-install-kserve-serverless-on-existing-cluster  -i ./cluster_info.sh 

  # RHOAI
  ./loopy playbooks run rhoai-stable-install-kserve-serverless-on-existing-cluster  -i ./cluster_info.sh 
  ~~~ 

- Deploy KServe RawDeployment
  ~~~
  # ODH 
  ./loopy playbooks run odh-stable-install-kserve-raw-on-existing-cluster  -i ./cluster_info.sh 

  # RHOAI
  ./loopy playbooks run rhoai-stable-install-kserve-raw-on-existing-cluster  -i ./cluster_info.sh   
  ~~~ 

- Deploy Modelmesh and KServe Raw  
  ~~~
  ./loopy playbooks run odh-stable-install-kserve-raw-on-existing-cluster -p ENABLE_MODELMESH=Managed -i ~/temp/TEST_CLUSTER/integrate_test_j.sh 
  ~~~

### Deploy KServe/Modelmesh with custom manifests
example(unit - example-deploy-rhoai-kserve-with-custom-manifests)
You can combine multiple components together.

- Custom KServe Manifests
~~~
# ODH
  ./loopy playbooks run odh-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_KSERVE_MANIFESTS=https://github.com/jooho/kserve/tarball/master -i ./cluster_info.sh 

  # RHOAI
  ./loopy playbooks run rhoai-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_KSERVE_MANIFESTS=https://github.com/jooho/kserve/tarball/master -i ./cluster_info.sh 
~~~

- Custom ODH MODEL CONTROLLER Manifests
~~~
# ODH
  ./loopy playbooks run odh-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS=https://github.com/jooho/odh-model-controller/tarball/main -i ./cluster_info.sh 

  # RHOAI
  ./loopy playbooks run rhoai-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_ODH_MODEL_CONTROLLER_MANIFESTS=https://github.com/jooho/odh-model-controller/tarball/main -i ./cluster_info.sh 
~~~

- Custom MODELMESH Manifests
~~~
# ODH
  ./loopy playbooks run odh-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_MODELMESH_MANIFESTS=https://github.com/jooho/modelmesh-serving/tarball/main -i ./cluster_info.sh 

  # RHOAI
  ./loopy playbooks run rhoai-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_MODELMESH_MANIFESTS=https://github.com/jooho/modelmesh-serving/tarball/main -i ./cluster_info.sh 
~~~

- Custom DASHBOARD Manifests
~~~
# ODH
  ./loopy playbooks run odh-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_MODELMESH_MANIFESTS=https://github.com/opendatahub-io/odh-dashboard/tarball/f/pipelines-v2 -i ./cluster_info.sh 

  # RHOAI
  ./loopy playbooks run rhoai-stable-install-kserve-serverless-on-existing-cluster -p CUSTOM_MODELMESH_MANIFESTS=https://github.com/opendatahub-io/odh-dashboard/tarball/f/pipelines-v2 -i ./cluster_info.sh 
~~~
