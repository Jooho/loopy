**Download CLI**
~~~
make init
~~~

**Operator**
- Install serverless stable operator using *unit*
  ~~~
  ./loopy units run install-serverless-stable-operator  -i ~/temp/TEST_CLUSTER/integrate_test.sh
  ~~~

- Uninstall serverless using *role*
  ~~~
  ./loopy roles run operator-delete -i ~/temp/TEST_CLUSTER/integrate_test.sh  -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=openshift-serverless -p OPERATOR_NAME=serverless-operator
  ~~~


**Minio**
- Install Minio
  ~~~
  ./loopy roles run minio-deploy 
  ~~~
  - adding input_variable file
    ~~~
    ./loopy roles run minio-deploy  -i ~/temp/TEST_CLUSTER/integrate_test.sh

    cat ~/temp/TEST_CLUSTER/integrate_test.sh
    CLUSTER_CONSOLE_URL=https://XXX
    CLUSTER_API_URL=https://XXX
    CLUSTER_ADMIN_ID=admin
    CLUSTER_ADMIN_PW=password
    CLUSTER_TOKEN=sha256~XXX
    CLUSTER_TYPE=ROSA
    ~~~
  
**Caikit**
- Test caikit-tgis rest test
  ~~~
  ./loopy units run test-kserve-caikit-tgis-rest  -i ~/temp/TEST_CLUSTER/integrate_test.sh
  ~~~


**KServe E2E test**
- Install ossm,serverless,rhoai operators. Deploy kserve then test caikit-tgis runtime.
  ~~~
  ./loopy playbooks run kserve-sanity-test-on-existing-cluster -i ~/temp/TEST_CLUSTER/integrate_test.sh
  ~~~ 
