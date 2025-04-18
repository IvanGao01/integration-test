import json
from typing import  Union, Dict, Any, Optional, List, Mapping, ByteString
import requests
from urllib.parse import urljoin
from utils.logger import log
import allure

class HttpRequestHelper:

    @staticmethod
    def send_http_request(
            method: str,
            base_url: str,
            endpoint: str,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Union[Dict[str, str], bytes, List[tuple]]] = None,
            data: Optional[Union[str, bytes, ByteString, Mapping[str, Any], List[tuple]]] = None,  # 修正类型注解
            json_data: Optional[Union[Dict[str, Any], List[Any]]] = None,
            form_data: Optional[Dict[str, str]] = None,
            files: Optional[Dict[str, Union[str, bytes, ByteString]]] = None,
            auth: Optional[tuple] = None,
            timeout: int = 10,
            expected_status: Optional[int] = None,
            ssl_verify: bool = True
    ) -> requests.Response:
        """
        发送HTTP请求的通用方法

        Args:
            method: HTTP方法 (GET/POST/PUT/DELETE等)
            base_url: 基础URL (e.g. "https://api.example.com")
            endpoint: 接口端点 (e.g. "/v1/users")
            headers: 请求头
            params: URL查询参数
            data:  # 新增data参数
            json_data: JSON格式的请求体
            form_data: Form表单数据
            files: 文件上传 {"file": open('test.txt', 'rb')}
            auth: 基本认证 (username, password)
            timeout: 请求超时时间(秒)
            expected_status: 预期的HTTP状态码
            ssl_verify: 是否验证SSL证书

        Returns:
            requests.Response: 响应对象

        Raises:
            AssertionError: 当expected_status不匹配时
            requests.RequestException: 请求失败时
        """
        url = urljoin(base_url, endpoint)
        request_description = f"{method.upper()} {url}"

        # 准备请求数据
        request_data = {
            "method": method,
            "url": url,
            "headers": headers or {},
            "params": params,
            "timeout": timeout,
            "verify": ssl_verify
        }

        # 请求体处理优先级: data > json > form > files
        if data is not None:
            request_data["data"] = data
        if json_data:
            request_data["json"] = json_data
        if form_data:
            request_data["data"] = form_data
        if files:
            request_data["files"] = files
        if auth:
            request_data["auth"] = auth

        # 记录到Allure
        with allure.step(f"HTTP请求: {request_description}"):
            try:
                # 记录请求详情
                allure.attach(
                    json.dumps({
                        "url": url,
                        "method": method,
                        "headers": request_data["headers"],
                        "params": params,
                        "body": json_data or form_data,
                        "timeout": timeout
                    }, indent=2, ensure_ascii=False),
                    name="Request Details",
                    attachment_type=allure.attachment_type.JSON
                )

                log.info(f"发送请求: {request_description}")
                response = requests.request(**request_data)

                # 记录响应详情
                try:
                    response_body = response.json()
                    content_type = "JSON"
                except ValueError:
                    response_body = response.text
                    content_type = "Text"

                allure.attach(
                    json.dumps({
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response_body,
                        "elapsed": f"{response.elapsed.total_seconds()}s"
                    }, indent=2, ensure_ascii=False),
                    name=f"Response ({content_type})",
                    attachment_type=allure.attachment_type.JSON
                )

                log.info(
                    f"收到响应: {response.status_code} "
                    f"(耗时: {response.elapsed.total_seconds()}s)"
                )

                # 状态码断言
                if expected_status is not None:
                    assert response.status_code == expected_status, (
                        f"预期状态码 {expected_status}, 实际得到 {response.status_code}\n"
                        f"响应内容: {response_body}"
                    )
                    log.success(f"状态码验证通过: {expected_status}")

                return response

            except requests.RequestException as e:
                log.error(f"请求失败: {str(e)}")
                allure.attach(
                    str(e),
                    name="Request Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
            except AssertionError as e:
                log.error(f"断言失败: {str(e)}")
                allure.attach(
                    response.text if 'response' in locals() else "No response",
                    name="Assertion Failure",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
            except Exception as e:
                log.critical(f"未知错误: {str(e)}")
                allure.attach(
                    str(e),
                    name="Unexpected Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise