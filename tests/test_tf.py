from kserve import (
    V1beta1InferenceService,
    constants,
    V1beta1InferenceServiceSpec,
    V1beta1PredictorSpec,
    V1beta1TFServingSpec,
    KServeClient,
)
from kubernetes import client, config
import datetime
from dateutil.tz import tzutc
from pprint import pprint
from kubernetes.client.models.v1_namespace_list import V1NamespaceList
import os

k8s_namespace = "afw-kserve-local"

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


create_namespace()

# ------------------------ Create a inference service using kserve ------------------------ #
def create_inference_service():
    # PreRequiscites - kserve, ingress etc should be installed
    # Tensorflow isvc
    config.load_kube_config()
    print("------ Trying to create inf*service ------")
    isvc = V1beta1InferenceService(
        api_version=constants.KSERVE_V1BETA1,
        kind=constants.KSERVE_KIND,
        metadata=client.V1ObjectMeta(name="flower-sample2-2", namespace=k8s_namespace),
        spec=V1beta1InferenceServiceSpec(
            predictor=V1beta1PredictorSpec(
                tensorflow=V1beta1TFServingSpec(
                    storage_uri="gs://kfserving-examples/models/tensorflow/flowers",
                )
            )
        ),
    )

    kserve_client = KServeClient()
    x = kserve_client.create(isvc, namespace=k8s_namespace, watch=True)
    pprint(x)


# create_inference_service()


def get_inference_services(isvc_name: str, namespace=k8s_namespace, watch=True, timeout_seconds=120):
    print(f"------ Trying to get inf*service {isvc_name} ------")
    kserve_client = KServeClient()
    x = kserve_client.get(isvc_name, namespace=namespace, watch=watch, timeout_seconds=timeout_seconds)
    pprint(x)


get_inference_services("flower-sample2-2", watch=True)


def get_cluster_ip():
    config.load_kube_config()
    api_instance = client.CoreV1Api(client.ApiClient())
    service = api_instance.read_namespaced_service("istio-ingressgateway", "istio-system")
    if service.status.load_balancer.ingress is None:
        cluster_ip = service.spec.cluster_ip
    else:
        cluster_ip = service.status.load_balancer.ingress[0].hostname or service.status.load_balancer.ingress[0].ip

    return os.environ.get("KSERVE_INGRESS_HOST_PORT", cluster_ip)


# print(get_cluster_ip())
