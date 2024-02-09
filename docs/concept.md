# Loopy Concept
Loopy is TEST Framework that anybody can create a test script simply with your favorite language. Loopy is using environment variable to pass information between tests. The main concept is similar to ansible. Role is the smallest component and Unit will include Role with specific input data. The playbook can 



Loopy is using 3 components:
- role
- unit (role + input value)
- playbook (role + unit)

## Component
**role**
- This include real scripts to achieve the goal

**unit**
- This is combination of a configuration file and role. 
- Unit can be reusable in the playbook
- example
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

**playbook**
- This is combination of several roles.
- Each role will have input/output and it will be passed to the next role
- playbook can be resuable in the suite.
- example
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
