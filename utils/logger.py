"""
调试日志管理

使用方法：
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("信息")
    logger.warning("警告")
    logger.error("错误")
    logger.debug("调试")

"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir="logs", log_file="medqa.log", level=logging.INFO):
    """
    log_dir: 日志文件目录
    log_file: 日志文件名
    level: 日志级别
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, log_file)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除已有的处理器
    root_logger.handlers.clear()
    
    # 文件处理器（带轮转，最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name):
    """
    获取指定名称的日志记录器
    name: 日志记录器名称（通常是 __name__）
    Returns:
        Logger实例
    """
    return logging.getLogger(name)


# 初始化日志
setup_logging()

