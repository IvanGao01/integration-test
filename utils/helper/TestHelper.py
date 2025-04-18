import json
import string
import requests
import allure

from random import random
from typing import Optional, Dict
from urllib.parse import urljoin

from utils.logger import log


class TestHelper:
    """测试辅助工具集"""

    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def make_api_request(
            method: str,
            base_url: str,
            endpoint: str,
            headers: Optional[Dict] = None,
            payload: Optional[Dict] = None,
            expected_status: int = 200
    ) -> Dict:
        """执行API请求并记录到Allure"""
        url = urljoin(base_url, endpoint)

        with allure.step(f"API请求: {method.upper()} {url}"):
            # 记录请求详情
            allure.attach(
                json.dumps({
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "body": payload
                }, indent=2),
                name="Request Details",
                attachment_type=allure.attachment_type.JSON
            )

            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload
                )

                # 记录响应详情
                allure.attach(
                    json.dumps({
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response.json() if response.content else None
                    }, indent=2),
                    name="Response Details",
                    attachment_type=allure.attachment_type.JSON
                )

                if response.status_code != expected_status:
                    log.error(f"API请求失败: {response.status_code} - {response.text}")
                    raise AssertionError(f"预期状态码 {expected_status}, 实际得到 {response.status_code}")

                log.success(f"API请求成功: {method} {url}")
                return response.json()

            except Exception as e:
                log.error(f"API请求异常: {str(e)}")
                allure.attach(
                    str(e),
                    name="API Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise

    @staticmethod
    def compare_dicts(actual: Dict, expected: Dict, path: str = "") -> bool:
        """深度比较字典并生成差异报告"""
        diff_messages = []

        for key in expected:
            current_path = f"{path}.{key}" if path else key

            if key not in actual:
                diff_messages.append(f"缺少字段: {current_path}")
                continue

            if isinstance(expected[key], dict):
                if not isinstance(actual[key], dict):
                    diff_messages.append(f"类型不匹配: {current_path} (期望dict, 实际{type(actual[key])})")
                else:
                    TestHelper.compare_dicts(actual[key], expected[key], current_path)
            elif actual[key] != expected[key]:
                diff_messages.append(
                    f"值不匹配: {current_path} (期望: {expected[key]}, 实际: {actual[key]})"
                )

        if diff_messages:
            diff_report = "\n".join(diff_messages)
            allure.attach(
                diff_report,
                name="Dictionary Comparison",
                attachment_type=allure.attachment_type.TEXT
            )
            log.error(f"字典比较失败:\n{diff_report}")
            return False

        return True

