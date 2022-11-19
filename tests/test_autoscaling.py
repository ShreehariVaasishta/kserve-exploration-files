from kserve import (
    V1beta1InferenceService,
    constants,
    V1beta1InferenceServiceSpec,
    V1beta1PredictorSpec,
    V1beta1TFServingSpec,
    V1beta1CustomPredictor,
    V1beta1SKLearnSpec,
    V1beta1TorchServeSpec,
    KServeClient,
)
from kubernetes import client, config
import datetime
from dateutil.tz import tzutc
from pprint import pprint
from kubernetes.client.models.v1_namespace_list import V1NamespaceList
import os

k8s_namespace = "afw-kserve-local"
service_name = "custom-model"

TARGET = "autoscaling.knative.dev/target"
METRIC = "autoscaling.knative.dev/metric"
MODEL = "gs://kfserving-examples/models/sklearn/1.0/model"
INPUT = "./data/iris_input.json"

# ------------------------ Create a namespace on K8s ------------------------ #
def create_namespace():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    namespaces: V1NamespaceList = v1.list_namespace()
    namespaces_exists = False
    # pprint(namespaces.to_dict())

    for items in namespaces.to_dict().get("items"):
        if items["metadata"]["name"] == k8s_namespace:
            namespaces_exists = True
            break
    if not namespaces_exists:
        print(f"Namespace {k8s_namespace} does not exist. Creating it.")
        v1.create_namespace(
            body={
                "metadata": {
                    "name": k8s_namespace,
                }
            },
        )
        namespaces = v1.list_namespace()
        for items in namespaces.to_dict().get("items"):
            if items["metadata"]["name"] == k8s_namespace:
                print("- Namespace", items["metadata"]["name"], "created")
    else:
        print(f"Namespace {k8s_namespace} exists.")


# create_namespace()

# ------------------------ Create a inference service using kserve ------------------------ #
def create_inference_service():
    INPUT = "./input.json"
    # PreRequiscites - kserve, ingress etc should be installed
    # Custom model
    print("------ Trying to create inf*service ------")
    predictor = V1beta1PredictorSpec(
        min_replicas=1,
        scale_metric="concurrency",
        scale_target=2,
        containers=[
            client.V1Container(
                name="kserve-container",
                image="shreeharivl/custom-model:v1.2",
                resources=client.V1ResourceRequirements(
                    requests={"cpu": "50m", "memory": "128Mi"}, limits={"cpu": "100m", "memory": "1Gi"}
                ),
                env=[
                    client.V1EnvVar(
                        name="STORAGE_URI",
                        value=MODEL,
                    )
                ],
            )
        ],
    )
    isvc = V1beta1InferenceService(
        api_version=constants.KSERVE_V1BETA1,
        kind=constants.KSERVE_KIND,
        metadata=client.V1ObjectMeta(name=service_name, namespace=k8s_namespace),
        spec=V1beta1InferenceServiceSpec(predictor=predictor),
    )

    kserve_client = KServeClient()
    kserve_client.create(isvc)
    kserve_client.wait_isvc_ready(service_name, namespace=k8s_namespace)
    pods = kserve_client.core_api.list_namespaced_pod(
        k8s_namespace, label_selector="serving.kserve.io/inferenceservice={}".format(service_name)
    )
    print(pods)
    # kserve_client = KServeClient()
    # x = kserve_client.create(isvc, namespace=k8s_namespace, watch=True)
    # pprint(x)


create_inference_service()
