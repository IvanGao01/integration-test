import os
import platform
import pytest
from pathlib import Path

from utils.helper.KubenetesHellper import KubernetesHelper

kubernetes_helper = KubernetesHelper(default_namespace=f"{os.environ['KUBERNETES_NAMESPACE']}")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """在所有测试开始前执行"""
    env_vars = {
        "Python.Version": platform.python_version(),
        "OS": platform.platform(),
        "Pytest.Version": pytest.__version__,
        "CI": os.getenv("CI", "false"),
        "Workers": os.getenv("PYTEST_XDIST_WORKER_COUNT", "1")
    }

    # 确保目录存在
    results_dir = Path("allure-results")
    results_dir.mkdir(exist_ok=True)

    # 写入环境文件（使用绝对路径）
    env_file = results_dir / "environment.properties"
    with env_file.open("w", encoding="utf-8") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

    print(f"✅ 环境文件已生成: {env_file.absolute()}")


