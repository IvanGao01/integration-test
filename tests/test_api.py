# from typing import Union
# import pytest
#
# from utils.helper import CnosDBHelper
#
#
# def test_create_database():
#     test_data: Union[str, bytes] = (
#         "CREATE DATABASE IF NOT EXISTS oceanic_station"
#     )
#     # 类型检查
#     if not isinstance(test_data, (str, bytes)):
#         pytest.fail("测试数据必须是字符串或字节")
#
#     response = CnosDBHelper.query_from_cnosdb(
#         base_url="http://127.0.0.1:8902",
#         db_name="",
#         data=test_data,
#         username="root",
#         password=""
#     )
#
#     assert response.status_code == 200
#
# data = """
# air,station=XiaoMaiDao visibility=50,temperature=63,pressure=52 1642176000000000000
# air,station=XiaoMaiDao visibility=50,temperature=63,pressure=52 1642176000000000001
# air,station=XiaoMaiDao visibility=50,temperature=63,pressure=52 1642176000000000002
# air,station=XiaoMaiDao visibility=50,temperature=63,pressure=52 1642176000000000003
# """
#
# def test_write_data_safely():
#     # 类型安全的测试用例
#     test_data: Union[str, bytes] = (
#         data
#     )
#
#     # 类型检查
#     if not isinstance(test_data, (str, bytes)):
#         pytest.fail("测试数据必须是字符串或字节")
#
#     response = CnosDBHelper.write_to_cnosdb(
#         base_url="http://127.0.0.1:8902",
#         db_name="oceanic_station",
#         data=test_data,
#         username="root",
#         password=""
#     )
#
#     assert response.status_code == 200