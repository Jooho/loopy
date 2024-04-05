# Function Test

*Test commands*
~~~
./loopy roles list
./loopy units list
./loopy playbooks list

./loopy roles show deploy-minio
./loopy units show install-serverless-stable-operator
./loopy playbooks show deploy-ssl-minio

./loopy roles run minio-deploy 
./loopy roles run operator-delete -i ~/temp/TEST_CLUSTER/integrate_test.sh  -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=openshift-serverless -p OPERATOR_NAME=serverless-operator
./loopy roles run operator-install  -i ~/temp/TEST_CLUSTER/integrate_test_j.sh  -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=rhoai-serverless -p OPERATOR_NAME=serverless-operator -p CATALOGSOURCE_NAME=redhat-operators 
./loopy roles run install-operator  -i ~/temp/TEST_CLUSTER/integrate_test_j.sh  -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=rhoai-serverless -p OPERATOR_NAME=serverless-operator -p CATALOGSOURCE_NAME=redhat-operators -p OPERATOR_LABEL='name=knative-openshift'

./loopy units run install-serverless-stable-operator  -i ~/temp/TEST_CLUSTER/integrate_test_j.sh
./loopy playbooks run deploy-ssl-minio  -i ~/temp/TEST_CLUSTER/integrate_test_j.sh
~~~



**report test**
~~~
./loopy roles run shell-execute -p COMMANDS="ls%%hostname"
./loopy units run loopy-test-kubectl
./loopy playbooks run loopy-test-report-playbook
~~~

**related_component**
~~~
- playbook: loopy-test-report-playbook
  - unit: loopy-test-cert-generate 
  - role: shell-execute
  - unit: loopy-test-kubectl 
- unit: loopy-test-cert-generate 
  - role: generate-cert
  - role: shell-execute
- unit: loopy-test-kubectl
  - role: shell-execute
  - role shell-execute
~~~
