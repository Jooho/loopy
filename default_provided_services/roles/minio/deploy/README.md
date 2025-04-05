
Test
```
curl --location 'http://minio.minio.svc:9000/api/v1/login' --header 'Content-Type: application/json'  --data '{"accessKey":"THEACCESSKEY","secretKey":"THEPASSWORD"}'


curl --location 'http://minio.minio.svc:9000'  --data '{"accessKey":"THEACCESSKEY","secretKey":"THEPASSWORD"}'
```


Test ssl minio
~~~
oc run minio-test --image=registry.access.redhat.com/rhel7/rhel-tools -- tail -f /dev/null
oc cp /tmp/minio_certs/root.crt minio-test:/home
oc rsh minio-test

curl --cacert /home/root.crt https://minio.minio.svc:9000
~~~
