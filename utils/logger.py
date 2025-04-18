# utils/logger.py
from pathlib import Path
from loguru import logger
import sys
import allure


class PytestLoguru:
    """专为pytest+allure优化的日志工具"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 初始化配置
        self._logs_dir = Path("logs")
        self._initialized = True

        # 清理现有handler
        logger.remove()

        # 基础配置
        self.configure()

    def configure(
            self,
            level: str = "INFO",
            rotation: str = "10 MB",
            retention: str = "7 days",
            enqueue: bool = True
    ):
        """配置日志参数

        Args:
            level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
            rotation: 日志轮转条件
            retention: 日志保留时间
            enqueue: 是否线程安全
        """
        # 确保日志目录存在
        self._logs_dir.mkdir(exist_ok=True)

        # 控制台输出配置
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{module}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            colorize=True,
            enqueue=enqueue
        )

        # 文件输出配置
        logger.add(
            self._logs_dir / "pytest_{time:YYYY-MM-DD}.log",
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=enqueue,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                   "{level: <8} | "
                   "{module}:{line} - {message}"
        )

        # 绑定Allure集成
        self._bind_allure()

    def _bind_allure(self):
        """绑定Allure报告集成"""

        def allure_log(level: str, message: str, **kwargs):
            # 原始日志记录
            logger.opt(depth=1).log(level, message, **kwargs)

            # 关键日志附加到Allure
            if level in ("ERROR", "CRITICAL"):
                with allure.step(f"[{level}] {message}"):
                    allure.attach(
                        message,
                        name=f"{level} Log",
                        attachment_type=allure.attachment_type.TEXT
                    )

        # 重定向关键日志方法
        logger.error = lambda msg, *a, **kw: allure_log("ERROR", msg, *a, **kw)
        logger.critical = lambda msg, *a, **kw: allure_log("CRITICAL", msg, *a, **kw)

    def __getattr__(self, name):
        """转发所有未定义的方法到loguru logger"""
        return getattr(logger, name)


# 全局单例实例
log = PytestLoguru()