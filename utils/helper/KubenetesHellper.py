from kubernetes import client, config
from kubernetes.client import ApiClient
from kubernetes.stream import stream
import yaml
from typing import Dict, List, Optional, Union


class KubernetesHelper:
    _instance = None

    def __new__(cls, config_file: str = None, in_cluster: bool = False, default_namespace: str = "default"):
        if cls._instance is None:
            cls._instance = super(KubernetesHelper, cls).__new__(cls)
            cls._instance._initialized = False
            # 只在第一次初始化时设置默认命名空间
            cls._instance._default_namespace = default_namespace
        return cls._instance

    def __init__(self, config_file: str = None, in_cluster: bool = False, default_namespace: str = None):
        if self._initialized:
            return

        """
        初始化 Kubernetes 客户端

        参数:
            config_file: kubeconfig 文件路径，如果为 None 则使用默认路径 (~/.kube/config)
            in_cluster: 是否在集群内部运行，如果在 Pod 中运行设置为 True
            default_namespace: 默认命名空间，只在第一次初始化时生效
        """
        if in_cluster:
            config.load_incluster_config()
        else:
            if config_file:
                config.load_kube_config(config_file=config_file)
            else:
                config.load_kube_config()

        self.api_client = ApiClient()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.custom_objects_api = client.CustomObjectsApi()
        self._initialized = True

    @property
    def default_namespace(self) -> str:
        """获取当前默认命名空间"""
        return self._default_namespace

    @default_namespace.setter
    def default_namespace(self, namespace: str):
        """设置新的默认命名空间"""
        self._default_namespace = namespace

    # ------------------------- Pod 操作 -------------------------
    def list_pods(self, label_selector: str = None) -> List[Dict]:
        """列出命名空间中的 Pod"""
        pods = self.core_v1.list_namespaced_pod(self.default_namespace, label_selector=label_selector)
        return [self._format_pod_info(self, pod) for pod in pods.items]

    def get_pod(self, name: str) -> Optional[Dict]:
        """获取 Pod 详细信息"""
        try:
            pod = self.core_v1.read_namespaced_pod(name, self.default_namespace)
            return self._format_pod_info(self, pod)
        except client.ApiException as e:
            print(f"获取 Pod 信息失败: {e}")
            return None

    def delete_pod(self, name: str) -> bool:
        """删除 Pod"""
        try:
            self.core_v1.delete_namespaced_pod(name, self.default_namespace)
            return True
        except client.ApiException as e:
            print(f"删除 Pod 失败: {e}")
            return False

    def exec_command(self, pod_name: str, command: List[str], container: str = None) -> str:
        """在 Pod 中执行命令"""
        try:
            resp = stream(
                self.core_v1.connect_get_namespaced_pod_exec,
                pod_name,
                self.default_namespace,
                command=command,
                container=container,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            return resp
        except client.ApiException as e:
            print(f"执行命令失败: {e}")
            return ""

    def get_pod_logs(self, pod_name: str, container: str = None,
                     tail_lines: int = 100) -> str:
        """获取 Pod 日志"""
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                pod_name,
                self.default_namespace,
                container=container,
                tail_lines=tail_lines
            )
            return logs
        except client.ApiException as e:
            print(f"获取日志失败: {e}")
            return ""

    # ------------------------- Deployment 操作 -------------------------
    def list_deployments(self) -> List[Dict]:
        """列出命名空间中的 Deployment"""
        deployments = self.apps_v1.list_namespaced_deployment(self.default_namespace)
        return [self._format_deployment_info(self, deploy) for deploy in deployments.items]

    def create_deployment(self, deployment_manifest: Union[Dict, str]) -> bool:
        """创建 Deployment"""
        try:
            if isinstance(deployment_manifest, str):
                deployment_manifest = yaml.safe_load(deployment_manifest)

            self.apps_v1.create_namespaced_deployment(
                namespace=self.default_namespace,
                body=deployment_manifest
            )
            return True
        except client.ApiException as e:
            print(f"创建 Deployment 失败: {e}")
            return False

    def update_deployment(self, name: str,deployment_manifest: Union[Dict, str]) -> bool:
        """更新 Deployment"""
        try:
            if isinstance(deployment_manifest, str):
                deployment_manifest = yaml.safe_load(deployment_manifest)

            self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=self.default_namespace,
                body=deployment_manifest
            )
            return True
        except client.ApiException as e:
            print(f"更新 Deployment 失败: {e}")
            return False

    def scale_deployment(self, name: str, replicas: int) -> bool:
        """扩缩容 Deployment"""
        try:
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment_scale(
                name=name,
                namespace=self.default_namespace,
                body=body
            )
            return True
        except client.ApiException as e:
            print(f"扩缩容 Deployment 失败: {e}")
            return False

    # ------------------------- Service 操作 -------------------------
    def list_services(self) -> List[Dict]:
        """列出命名空间中的 Service"""
        services = self.core_v1.list_namespaced_service(self.default_namespace)
        return [self._format_service_info(self, svc) for svc in services.items]

    def create_service(self, service_manifest: Union[Dict, str]) -> bool:
        """创建 Service"""
        try:
            if isinstance(service_manifest, str):
                service_manifest = yaml.safe_load(service_manifest)

            self.core_v1.create_namespaced_service(
                namespace=self.default_namespace,
                body=service_manifest
            )
            return True
        except client.ApiException as e:
            print(f"创建 Service 失败: {e}")
            return False

    # ------------------------- ConfigMap 和 Secret 操作 -------------------------
    def create_configmap(self, name: str , data: Dict) -> bool:
        """创建 ConfigMap"""
        try:
            body = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name=name),
                data=data
            )
            self.core_v1.create_namespaced_config_map(self.default_namespace, body)
            return True
        except client.ApiException as e:
            print(f"创建 ConfigMap 失败: {e}")
            return False

    def create_secret(self, name: str, data: Dict, secret_type: str = "Opaque") -> bool:
        """创建 Secret"""
        try:
            body = client.V1Secret(
                metadata=client.V1ObjectMeta(name=name),
                data=data,
                type=secret_type
            )
            self.core_v1.create_namespaced_secret(self.default_namespace, body)
            return True
        except client.ApiException as e:
            print(f"创建 Secret 失败: {e}")
            return False

    # ------------------------- 辅助方法 -------------------------
    @staticmethod
    def _format_pod_info(self, pod) -> Dict:
        """格式化 Pod 信息"""
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ip": pod.status.pod_ip,
            "node": pod.spec.node_name,
            "creation_time": pod.metadata.creation_timestamp,
            "labels": pod.metadata.labels,
            "containers": [c.name for c in pod.spec.containers]
        }

    @staticmethod
    def _format_deployment_info(self, deploy) -> Dict:
        """格式化 Deployment 信息"""
        return {
            "name": deploy.metadata.name,
            "namespace": deploy.metadata.namespace,
            "replicas": deploy.spec.replicas,
            "available_replicas": deploy.status.available_replicas,
            "labels": deploy.metadata.labels,
            "creation_time": deploy.metadata.creation_timestamp
        }

    @staticmethod
    def _format_service_info(self, svc) -> Dict:
        """格式化 Service 信息"""
        return {
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "ports": [{"port": p.port, "target_port": p.target_port} for p in svc.spec.ports],
            "creation_time": svc.metadata.creation_timestamp
        }

    def apply_yaml(self, yaml_content: str) -> bool:
        """应用 YAML 配置"""
        try:
            yaml_docs = yaml.safe_load_all(yaml_content)
            for doc in yaml_docs:
                if not doc:
                    continue

                kind = doc.get("kind")
                if kind == "Deployment":
                    self.apps_v1.create_namespaced_deployment(self.default_namespace, doc)
                elif kind == "Service":
                    self.core_v1.create_namespaced_service(self.default_namespace, doc)
                elif kind == "ConfigMap":
                    self.core_v1.create_namespaced_config_map(self.default_namespace, doc)
                elif kind == "Secret":
                    self.core_v1.create_namespaced_secret(self.default_namespace, doc)
                elif kind == "Namespace":
                    self.core_v1.create_namespace(doc)
                # 可以添加更多资源类型的处理

            return True
        except client.ApiException as e:
            print(f"应用 YAML 配置失败: {e}")
            return False

    def get_custom_resource(self, group: str, version: str, plural: str, name: str) -> Optional[
        Dict]:
        """获取自定义资源"""
        try:
            if self.default_namespace:
                resource = self.custom_objects_api.get_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=self.default_namespace,
                    plural=plural,
                    name=name
                )
            else:
                resource = self.custom_objects_api.get_cluster_custom_object(
                    group=group,
                    version=version,
                    plural=plural,
                    name=name
                )
            return resource
        except client.ApiException as e:
            print(f"获取自定义资源失败: {e}")
            return None


# # 初始化客户端
# k8s_tool = KubernetesTool()  # 使用默认 kubeconfig
# # 或者在集群内部使用:
# # k8s_tool = KubernetesTool(in_cluster=True)
#
# # 列出所有命名空间
# namespaces = k8s_tool.list_namespaces()
# print("Namespaces:", namespaces)
#
# # 列出 default 命名空间中的 Pod
# pods = k8s_tool.list_pods("default")
# for pod in pods:
#     print(f"Pod: {pod['name']}, Status: {pod['status']}, IP: {pod['ip']}")
#
# # 获取特定 Pod 的日志
# logs = k8s_tool.get_pod_logs("my-pod", "default", tail_lines=50)
# print("Pod logs:", logs)
#
# # 在 Pod 中执行命令
# output = k8s_tool.exec_command("my-pod", "default", ["ls", "-l", "/"])
# print("Command output:", output)
#
# # 创建 Deployment
# deployment_yaml = """
# apiVersion: apps/v1
# kind: Deployment
# metadata:
#   name: nginx-deployment
# spec:
#   replicas: 2
#   selector:
#     matchLabels:
#       app: nginx
#   template:
#     metadata:
#       labels:
#         app: nginx
#     spec:
#       containers:
#       - name: nginx
#         image: nginx:1.14.2
#         ports:
#         - containerPort: 80
# """
# success = k8s_tool.apply_yaml(deployment_yaml)
# print("Deployment created:", success)
#
# # 扩缩容 Deployment
# success = k8s_tool.scale_deployment("nginx-deployment", "default", 3)
# print("Deployment scaled:", success)
#
# # 创建 ConfigMap
# config_data = {
#     "app.properties": "key1=value1\nkey2=value2",
#     "log4j.properties": "log.level=INFO"
# }
# success = k8s_tool.create_configmap("app-config", "default", config_data)
# print("ConfigMap created:", success)
