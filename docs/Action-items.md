2/1
- Setup test role directory/files for test framework
  - config.yaml
  - operator install
  - test script
  
2/2
- Add util file 
  - to verify object 
  - move root-directory.sh to util file
- finish test script 
- role finish
  - install
  - delete
- add a new role 
  - openshift install  
- create a test unit(odh 2.5 operator install)

- create ms.py to test unit 
  - default command-sub command

  

2/5
  - gather/export input variables
    - create global map
      - default_env_vars
      - config
  - Create Role process



2/6
- create a playbook
- playbook logic
- playbook/unit/role input file
  - create files 
    - artifacts
      - manifests
      - logs
  - create directies 
    - output
    - unit-name

#  /tmp/ms_cli/20240206/report

#  /tmp/ms_cli/20240206/output
#  /tmp/ms_cli/20240206/output/1.${role-name}.sh
#  /tmp/ms_cli/20240206/output/2.${unit-name}.sh

#  /tmp/ms_cli/20240206_tiem/artifacts
#  /tmp/ms_cli/20240206/artifacts/1.$role-name        #(openshift-install)
#  /tmp/ms_cli/20240206/artifacts/1.$role-name/log
#  /tmp/ms_cli/20240206/artifacts/1.$role-name/input_env
#  /tmp/ms_cli/20240206/artifacts/1.$role-name/output_env
#  /tmp/ms_cli/20240206/artifacts/2.$unit-name        #(install-odh-2.5-opeator)  


2/7
- bash role 



default value in commons --> config.yaml ---> unit or playbook input.sh  --> -p test=a 






2/7



- create a test pipeline(openshift install -> operator -> operator)
- minio deploy








- Setup module directory/files for test framework
- update ms.py to test module

- Setup test suite direcotry/files for test framework
- update ms.py to test test-suite





Terms
- role
  - This include real scripts to achieve the goal
- unit
  - This is combination of a configuration file and role. 
  - Unit can be reusable in the playbook
  - target units
    - operator-install-ossm-stable
    - operator-install-serverless-stable
    - operator-install-pipeline-stable
    - operator-install-odh-stable
    - operator-install-rhods-stable
    - test-notebook-deploy-model
    - test-pipeline-deploy-model
    - test-kserve-deploy-model
    - test-modelmesh-deploy-model
- playbook
  - This is combination of several roles.
  - Each role will have input/output and it will be passed to the next role
  - playbook can be resuable in the suite.
  - target playbooks
    - operator-install-for-integration-test
      - operator-install-ossm-stable
      - operator-install-serverless-stable
      - operator-install-pipeline-stable
      - operator-install-rhods-stable
    - integration-tests
      - test-notebook-deploy-model
      - test-pipeline-deploy-model
      - test-kserve-deploy-model
      - test-modelmesh-deploy-model
- Suite
  - This is combination of several playbooks, units and bashshell.
  - It is the final script for each use case
    - integration tests
      - unit - openshift-create-rosa
      - playbook - operator-install-for-integration-test
      - bash - update smcp security
      - bash - verify all pods are ready
      - unit - opendatahub-create-DSC-for-integration-test
      - verify all pods are ready
      - - integration-tests


ms.py run role $role_name test
ms.py run unit $unit_name 



# unitest
# all unit tests
python -m unittest discover

# specific unit test
python -m unittest cli/test/test_a.py

# spcific method
python -m unittest cli/test/test_a.py.TestA.test_function_to_test

 python ./main.py roles run operator-install -p subscription_name=opendatahub-operator -p operator_namespace=openshift-operators -p operator_name=opendatahub-operator 
 
 python main.py units run install-odh-2.5-operator -p test=a

 python main.py playbooks run deploy-odh-2.5-on-new-gpu-cluster  -i 



Global Env
- OUTPUT_DIR (/tmp/ms_cli/20240206/output)
- ARTIFACTS_DIR (/tmp/ms_cli/20240206/artifacts)
- ROLE_DIR (/tmp/ms_cli/20240206/artifacts/1.$role-name)
- REPORT_FILE (/tmp/ms_cli/20240206/report)





python main.py playbooks run kserve-sanity-test-on-existing-cluster -i ~/temp/TEST_CLUSTER/integrate_test.sh


python main.py units run deploy-rhoai-kserve -i ~/temp/TEST_CLUSTER/integrate_test.sh


 python main.py units run install-serverless-stable-operator  -i ~/temp/TEST_CLUSTER/integrate_test.sh
python main.py roles run operator-delete -i ~/temp/TEST_CLUSTER/integrate_test.sh  -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=openshift-serverless -p OPERATOR_NAME=serverless-operator



python main.py roles run operator-delete -i ~/temp/TEST_CLUSTER/integrate_test.sh  -p SUBSCRIPTION_NAME=opendatahub-operator -p OPERATOR_NAMESPACE=opendatahub -p OPERATOR_NAME=opendatahub-operator 





create inference service
grpc call





Terms
- role
  - This include real scripts to achieve the goal
- unit
  - This is combination of a configuration file and role. 
  - Unit can be reusable in the playbook
  - target units
    - operator-install-ossm-stable
    - operator-install-serverless-stable
    - operator-install-pipeline-stable
    - operator-install-odh-stable
    - operator-install-rhods-stable
    - test-notebook-deploy-model
    - test-pipeline-deploy-model
    - test-kserve-deploy-model
    - test-modelmesh-deploy-model
- playbook
  - This is combination of several roles.
  - Each role will have input/output and it will be passed to the next role
  - playbook can be resuable in the suite.
  - target playbooks
    - operator-install-for-integration-test
      - operator-install-ossm-stable
      - operator-install-serverless-stable
      - operator-install-pipeline-stable
      - operator-install-rhods-stable
    - integration-tests
      - test-notebook-deploy-model
      - test-pipeline-deploy-model
      - test-kserve-deploy-model
      - test-modelmesh-deploy-model
  - 


Demo
./src/roles/minio/deploy/test/test.sh

./loopy roles run minio-deploy 
./loopy roles run minio-deploy  -i ~/temp/TEST_CLUSTER/integrate_test.sh

./loopy units run install-serverless-stable-operator  -i ~/temp/TEST_CLUSTER/integrate_test.sh
./loopy roles run operator-delete -i ~/temp/TEST_CLUSTER/integrate_test.sh  -p SUBSCRIPTION_NAME=serverless-operator -p OPERATOR_NAMESPACE=openshift-serverless -p OPERATOR_NAME=serverless-operator

./loopy playbooks run kserve-sanity-test-on-existing-cluster -i ~/temp/TEST_CLUSTER/integrate_test.sh



./loopy units run test-kserve-caikit-tgis-rest  -i ~/temp/TEST_CLUSTER/integrate_test.sh


TODO list
- in config.yaml, it would be a good idea to check if the input value is correct or not
  - CLUSTER_TYPE can be ROSA, PSI
  - User can put something else.
  - Need to check the value is one of the possible value 
  
