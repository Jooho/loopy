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
