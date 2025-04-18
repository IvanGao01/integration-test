from typing import  Union
import requests

from utils.helper.HttpRequestHelper import HttpRequestHelper


class CnosDBHelper:
    @staticmethod
    def _make_request(
            base_url: str,
            endpoint: str,
            data: Union[str, bytes],
            username: str = "root",
            password: str = "",
            expected_status: int = 200,
            **kwargs
    ) -> requests.Response:
        """
        内部通用请求方法，封装了重复的HTTP请求逻辑
        """
        if not isinstance(data, (str, bytes)):
            raise TypeError("data must be str or bytes")

        return HttpRequestHelper.send_http_request(
            method="POST",
            base_url=base_url,
            endpoint=endpoint,
            auth=(username, password),
            headers={
                "Accept": "application/json",
                "Content-Type": "text/plain"
            },
            data=data if isinstance(data, bytes) else data.encode('utf-8'),
            expected_status=expected_status,
            **kwargs
        )

    @staticmethod
    def query_from_cnosdb(
            base_url: str,
            db_name: str,
            data: Union[str, bytes],
            username: str = "root",
            password: str = "",
            timeout: int = 300,
    ) -> requests.Response:
        """
        从CnosDB查询数据
        :param base_url: 基础URL
        :param db_name: 数据库名称
        :param data: 查询数据
        :param username: 用户名
        :param password: 密码
        :param timeout: 超时时间
        :return: 请求响应
        """
        endpoint = f"/api/v1/sql?db={db_name}"
        return CnosDBHelper._make_request(
            base_url=base_url,
            endpoint=endpoint,
            data=data,
            username=username,
            password=password,
            expected_status=200,
            timeout=timeout
        )

    @staticmethod
    def write_to_cnosdb(
            base_url: str,
            db_name: str,
            data: Union[str, bytes],
            username: str = "root",
            password: str = "",
            precision: str = "ns"
    ) -> requests.Response:
        """
        写入数据到CnosDB
        :param base_url: 基础URL
        :param db_name: 数据库名称
        :param data: 要写入的数据
        :param username: 用户名
        :param password: 密码
        :param precision: 时间精度
        :return: 请求响应
        """
        endpoint = f"/api/v1/write?db={db_name}&precision={precision}"
        return CnosDBHelper._make_request(
            base_url=base_url,
            endpoint=endpoint,
            data=data,
            username=username,
            password=password,
            expected_status=200
        )

    @staticmethod
    def create_database(
            db_name: str,
            ip: str = "127.0.0.1",
            port: int = 8902,
            username: str = "root",
            password: str = "",
            **options
    ) -> requests.Response:
        """
        创建CnosDB数据库
        :param db_name: 数据库名称
        :param ip
        :param port
        :param username: 用户名
        :param password: 密码
        :param options: 数据库配置选项，例如:
               - ttl: 数据保留时间(秒)
               - shard: 分片数量
               - vnode_duration: 虚拟节点持续时间
               - replica: 副本数
        :return: 请求响应
        示例
        response = CnosDBHelper.create_database(
            base_url="http://localhost:8902",
            db_name="test_db_with_options",
            ttl=604800,  # 7天
            shard=4,
            replica=2
        )
        """
        # 构建创建数据库的Line Protocol格式数据
        data = f"create database if not exists {db_name}"

        # 添加可选参数
        if options:
            options_str = " ".join(f"{k}={v}" for k, v in options.items())
            data = f"{data} {options_str}"

        base_url = f"http://{ip}:{port}"

        return CnosDBHelper.query_from_cnosdb(
            base_url=base_url,
            db_name="",
            data=data,
            username=username,
            password=password,
        )


