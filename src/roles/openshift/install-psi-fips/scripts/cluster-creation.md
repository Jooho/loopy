# Cluster Creation

## Fips Enabled
To install the FIPS Enabled Cluster we do rely on  the QE Jenkins rhods-smoke pipeline.

To use this pipeline, you need to have a user in the given Jenkins Instance so you can have you token to use in the pipeline.

Here is a small example of how to use the pipeline:

```bash
./install.sh -u <JENKINS_USER> -t <JENKINS_TOKEN> -j <JENKINS_JOB_URL>
```

To see all options:
```bash
./install.sh -h
```
    
At the end of the execution you might have the output pointing out the cluster credentials to log in.

Keep in mind that, the pipeline will create a new cluster and keep it running.
So, before trigger it again make sure the cluster is not running, 

The default cluster name is `serving-ods-ci-fips-ms`
This should be possible to retrieve this information by querying the hive.

We can also build a specific build from brew, to do so, you can use the following command:

```bash
./install.sh -u <JENKINS_USER> -t <JENKINS_TOKEN> -j <JENKINS_JOB_URL> -b <ODS_BUILD_URL>
```


TODO: improvements:
- find a way to query if the cluster is already running.
