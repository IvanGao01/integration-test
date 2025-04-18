"""
3+3集群（k8s deploy）
建库，replica为 1 ：CREATE DATABASE db4 WITH replica 1;
找出有更大存储空间的节点
向tskv-0节点写入一条line protocol文本数据
测试点
  检查写入的vnode在存储空间更大的节点
"""
from time import sleep
from typing import Dict, List

import allure

from utils.helper.CnosDBHelper import CnosDBHelper
from utils.helper.KubenetesHellper import KubernetesHelper
from utils.logger import log


kubernetes_helper = KubernetesHelper()
pods = List[Dict]

def test_vnode_allocation_to_node_with_large_free_storage():
    query_tskv_pods = kubernetes_helper.list_pods(label_selector="cnosdb.com/role=query_tskv")
    # 选择 n-1 个 Pod 写入文件（保留一个不写入）
    pods_to_write = query_tskv_pods[:-1]
    excluded_pod = query_tskv_pods[-1]


    log.info(f"当前 namespace={kubernetes_helper.default_namespace}")
    with allure.step("清理环境：如果数据库db4存在，则删除"):
        resp = CnosDBHelper.query_from_cnosdb(
            f"http://{pods_to_write[0]['ip']}:8902",
            "",
            "drop database IF EXISTS db4")
        assert resp.status_code == 200

    with allure.step("创建数据库：db4"):
        resp = CnosDBHelper.query_from_cnosdb(
            f"http://{pods_to_write[0]['ip']}:8902",
            "",
            "create database if not EXISTS  db4 with replica 1")
        assert resp.status_code == 200

    with allure.step("等待 3 秒 ..."):
        sleep(3)
        assert 0 == 0
    with allure.step("向所有节点创建一个 1G 的文件，保留一个不写"):
        for pod in pods_to_write:
            success, message = write_large_file_to_pod(kubernetes_helper, pod['name'])
            assert success is True, log.error(message)
    with allure.step("写入一条数据"):

        resp = CnosDBHelper.write_to_cnosdb(
            f"http://{pods_to_write[0]['ip']}:8902",
            db_name="db4",
            data="ma,ta=a fa=1",
        )
        assert resp.status_code == 200

    with allure.step("查看数据是否落入磁盘空间空余更大的节点"):
        sleep(10)
        log.info("休眠 10 秒等待数据完全写入")
        success, message = check_dir_in_pod(kubernetes_helper, excluded_pod['name'],  "/var/lib/cnosdb/data/data/cnosdb.db4/")

        assert success is True, log.error(message)




def write_large_file_to_pod(kubernetes_helper, name, size_mb=1024):
    """
    向指定 Pod 写入一个大文件

    参数:
        kubernetes_helper: KubernetesHelper 实例
        name: Pod Name
        size_mb: 文件大小，单位 MB (默认 1024MB = 1GB)

    返回:
        (bool, str): (是否成功, 执行结果或错误信息)
    """
    try:
        # 使用 dd 命令创建文件
        command = [
            "dd", "if=/dev/zero",
            f"of=/var/lib/cnosdb/1G",
            "bs=1M",
            f"count={size_mb}"
        ]

        result = kubernetes_helper.exec_command(
            pod_name=name,
            command=command
        )

        if "records in" in result and "records out" in result:
            return True, f"成功在 {name} 中创建 {size_mb}MB 文件"
        return False, f"在 {name} 中创建文件失败: {result}"

    except Exception as e:
        return False, f"在 {name} 中执行命令异常: {str(e)}"


def check_dir_in_pod(kubernetes_helper, name, dir_path):
    """
    检查 Pod 中是否存在指定目录

    参数:
        kubernetes_helper: KubernetesHelper 实例
        name: Pod Name
        dir_path: 要检查的目录路径

    返回:
        (bool, str): (目录是否存在, 执行结果或错误信息)
    """

    try:
        # 使用 test -d 命令检查目录是否存在
        command = ["/bin/bash", "-c", f"ls {dir_path} && echo $?" ]
        result = kubernetes_helper.exec_command(
            pod_name=name,
            command=command
        ).strip()

        log.info(result)

        if "0" in result:
            return True, f"目录 {dir_path} 存在"
        return False, f"目录 {dir_path} 不存在"

    except Exception as e:
        return False, f"检查 Pod {name} 异常: {str(e)}"

# kubectl port-forward pod/my-pod 8902:8902 -n your-namespace


# def main():
#     print("Start")
#
#     kubernetes_helper.default_namespace = "cnosdb-enterprise-latest-3meta-2querytskv"
#
#     success, message = check_dir_in_pod(kubernetes_helper, "my-cnosdb-querytskv-0",
#                                         "/var/lib/cnosdb")
#
#     assert success is True, log.error(message)
#
#     return 0
#
#
#
#
#
# if __name__ == "__main__":
#     sys.exit(main())