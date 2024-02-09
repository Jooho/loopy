
Test
```
curl --location 'http://minio.minio.svc:9000/api/v1/login' --header 'Content-Type: application/json'  --data '{"accessKey":"THEACCESSKEY","secretKey":"THEPASSWORD"}'


curl --location 'http://minio.minio.svc:9000'  --data '{"accessKey":"THEACCESSKEY","secretKey":"THEPASSWORD"}'
```
