# Loopy Concept
Loopy is an automation framework in which anybody can create a test script simply with their favorite language. Loopy is using environment variables to pass information between tests. The main concept is similar to Ansible. Role is the smallest component and Unit will include Roles with specific input data. 
A Playbook can have combinations of roles and units. 

**Requirements:**
- python should be 3.10+
- The sudoers file must have your username listed as a root user

**Loopy is using 3 components:**
- role
- unit (role + input value)
- playbook (role + unit)

## Components
**Role**
- This includes real executable scripts to achieve the goal
- Role can be reusable in Unit and Playbook

**Unit**
- This is a combination of a role name and input environment values. 
- Unit can be reusable in Playbook.

**Playbook**
- This is a combination of several roles and units.
- Each Role/Unit can set input variables and output variables will be set for the next role.

## Commands
- list
  - This show you roles/units/playbooks that you can use
    ~~~
    ./loopy roles list
    ./loopy units list
    ./loopy playbooks list
    ~~~
- show
  - This show the detail information of the component. If you add `-v`, it will show you more detail information of the first component
    ~~~
    ./loopy roles show minio-deploy
    
    ./loopy units show deploy-ssl-minio
    ./loopy units show deploy-ssl-minio -v
    
    ./loopy playbooks show odh-stable-install-kserve-raw-on-existing-cluster
    ./loopy playbooks show odh-stable-install-kserve-raw-on-existing-cluster -v
    ~~~
- run
  - This trigger to execute script
    ~~~
    ./loopy roles run minio-deploy
    
    ./loopy units run deploy-ssl-minio
    
    ./loopy playbooks run odh-stable-install-kserve-raw-on-existing-cluster
    ~~~
