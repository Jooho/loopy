# rhoai-model-pipeline

Important, before to start:
This pipeline assumes that **Red Hat OpenShift AI is already installed** as well the Minio that will
serve as the storage for the models.

This pipeline will execute the following steps in the same order as described:

- Clean the given namespace by deleting all the resources that might be created by a previous execution and left behind.
- Create the Storage Config secret with the Minio information.
- Pull the git repository that contains the needed files.
- Deploy the CaiKit Runtime:
  - http
  - grpc
- Check if the CaiKit Runtime is ready to be used.
- Deploy the Inference Service with the default model: `flan-t5-small-caikit`
- Infer the model with the 'Translate to German:  My name is Arthur' text.
  - Infer using the `caikit-nlp-client` with the `http` and `grpc` protocols
- Clean the current namespace


## Running it:

Deploy the pipeline and its tasks:

```bash
for yaml in `find pipelines -name "*.yaml"`; do 
    oc apply -f $yaml; 
done
```


Fill the required parameters in the command below file and then run the following command:

```bash
tkn pipeline start caikit-e2e-inference-pipeline  \
  --param CLUSTER_API_URL=https://ocp-endpoint.test.com:6443 \
  --param CLUSTER_TOKEN=sha256~mytoken \
  --param WORKING_NAMESPACE=pipeline-test \
  --param MINIO_ACCESS_KEY_ID=admin \
  --param MINIO_SECRET_ACCESS_KEY=password \
  --param MINIO_S3_SVC_URL=minio.pipeline-test.svc:9000 \
  -w name=shared-workspace,volumeClaimTemplateFile=pvc.yaml \
  --use-param-defaults --showlog
```

It will trigger the Pipeline.

Other option is to trigger the pipeline from OpenShift Web Console.



### TODOs

- [ ] Create a base python image with the required dependencies as part of the pipeline
- [ ] Parameterize the deploy-isvc step timeout, default is 360s.