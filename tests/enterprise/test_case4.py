"""
测试vnode分配策略：验证数据是否会分配到存储空间更大的节点
1. 创建3+3集群（k8s部署）
2. 创建replica为1的数据库：CREATE DATABASE db4 WITH replica 1;
3. 找出有更大存储空间的节点
4. 向tskv-0节点写入line protocol数据
5. 验证数据是否写入到存储空间更大的节点
"""
from time import sleep
from typing import Tuple
import allure
from utils.helper.CnosDBHelper import CnosDBHelper
from utils.helper.KubenetesHellper import KubernetesHelper
from utils.logger import log

class VNodeAllocationTester:
    def __init__(self):
        self.k8s = KubernetesHelper()
        self.db_helper = CnosDBHelper()
        self.query_tskv_pods = []
        self.excluded_pod = None
        self.pods_to_write = []

    def setup(self):
        """初始化并分组Pod"""
        self.query_tskv_pods = self.k8s.list_pods(label_selector="cnosdb.com/role=query_tskv")
        if not self.query_tskv_pods:
            raise ValueError("No query_tskv pods found")

        self.pods_to_write = self.query_tskv_pods[:-1]
        self.excluded_pod = self.query_tskv_pods[-1]
        log.info(f"Current namespace: {self.k8s.default_namespace}")

    def manage_database(self, action: str):
        """管理数据库创建/删除"""
        sql = {
            'create': 'CREATE DATABASE IF NOT EXISTS db4 WITH REPLICA 1',
            'drop': 'DROP DATABASE IF EXISTS db4'
        }[action]

        resp = self.db_helper.query_from_cnosdb(
            f"http://{self.pods_to_write[0]['ip']}:8902",
            "",
            sql
        )
        assert resp.status_code == 200, f"{action.capitalize()} database failed: {resp.text}"

    def prepare_storage_conditions(self):
        """准备存储条件：在部分节点上创建大文件"""
        for pod in self.pods_to_write:
            success, message = self._write_large_file(pod['name'])
            assert success, f"Failed to prepare storage on {pod['name']}: {message}"

    def write_test_data(self):
        """写入测试数据"""
        resp = self.db_helper.write_to_cnosdb(
            f"http://{self.pods_to_write[0]['ip']}:8902",
            db_name="db4",
            data="ma,ta=a fa=1",
        )
        assert resp.status_code == 200, f"Data write failed: {resp.text}"

    def verify_allocation(self):
        """验证数据分配结果"""
        sleep(10)  # 等待数据同步
        success, message = self._check_directory_exists(
            self.excluded_pod['name'],
            "/var/lib/cnosdb/data/data/cnosdb.db4/"
        )
        assert success, f"Allocation verification failed: {message}"

    def _write_large_file(self, pod_name: str, size_mb: int = 1024) -> Tuple[bool, str]:
        """在Pod上创建大文件"""
        try:
            cmd = f"dd if=/dev/zero of=/var/lib/cnosdb/1G bs=1M count={size_mb}"
            result = self.k8s.exec_command(pod_name=pod_name, command=cmd.split())
            return ("records in" in result and "records out" in result,
                    f"Created {size_mb}MB file in {pod_name}")
        except Exception as e:
            return (False, f"Command failed on {pod_name}: {str(e)}")

    def _check_directory_exists(self, pod_name: str, dir_path: str) -> Tuple[bool, str]:
        """检查Pod中目录是否存在"""
        try:
            cmd = f"test -d {dir_path} && echo exists || echo missing"
            result = self.k8s.exec_command(pod_name=pod_name, command=["/bin/bash", "-c", cmd])
            exists = "exists" in result
            return (exists, f"Directory {'exists' if exists else 'does not exist'}")
        except Exception as e:
            return (False, f"Check failed on {pod_name}: {str(e)}")

@allure.story("VNode Allocation Test")
def test_vnode_allocation_to_node_with_large_free_storage():
    tester = VNodeAllocationTester()

    with allure.step("Initialize test environment"):
        tester.setup()

    with allure.step("Clean up existing database"):
        tester.manage_database('drop')

    with allure.step("Create test database"):
        tester.manage_database('create')
        sleep(3)  # Wait for DB initialization

    with allure.step("Prepare storage conditions"):
        tester.prepare_storage_conditions()

    with allure.step("Write test data"):
        tester.write_test_data()

    with allure.step("Verify data allocation"):
        tester.verify_allocation()