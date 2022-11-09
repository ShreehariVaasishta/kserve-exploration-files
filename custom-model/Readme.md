## Instructions

1. Go to custom-model directory
```bash
cd custom-model
```
2. Build the image with custom predictor
```bash
pack build --builder=heroku/buildpacks:20 ${DOCKER_USER}/custom-model:<tag>

docker push ${DOCKER_USER}/custom-model:v1
```
3. Update the image in `custom-model.yaml`
```yaml
apiVersion: "serving.kserve.io/v1beta1"
kind: "InferenceService"
metadata:
  name: "custom-model"
  annotations:
    autoscaling.knative.dev/target: "1"
spec:
  predictor:
    logger:
      mode: all
      url: http://message-dumper.default/  
    containers:
      - name: "kserve-container"
        image: ${DOCKER_USER}/custom-model:<tag>
```
4. Apply the yaml
```bash
kubectl apply -f custom.yaml -n kserve-test
```
5. Make request to the endpoint
```bash
curl -v -H "Host: ${SERVICE_HOSTNAME}" http://${INGRESS_HOST}:${INGRESS_PORT}/v1/models/${MODEL_NAME}:predict -d $INPUT_PATH
```
#### Note:
1. input_path: *test-input.json*
```json
{  
    "instances":[  
       {  
          "image":{  
             "b64":"<base64>"
          },
          "key":"   1"
       }
    ]
 }
```
2. ingress should be running
