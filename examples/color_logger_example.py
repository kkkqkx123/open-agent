"""彩色日志记录器示例"""

from src.services.logger import get_logger, Logger
from src.core.logger.handlers.console_handler import ConsoleHandler
from src.core.logger.formatters.color_formatter import ColorFormatter
from src.core.logger.log_level import LogLevel


def main():
    """主函数 - 演示彩色日志记录器的使用"""
    
    # 方法1: 通过配置使用彩色控制台处理器
    config = {
        "log_outputs": [
            {
                "type": "console",
                "use_color": True,
                "level": "DEBUG"
            }
        ],
        "log_level": "DEBUG"
    }
    
    logger = Logger("ColorExample", config)
    
    print("使用配置的彩色日志记录器:")
    logger.debug("这是一条调试信息 - 蓝色")
    logger.info("这是一条信息 - 绿色")
    logger.warning("这是一条警告 - 黄色")
    logger.error("这是一条错误 - 红色")
    logger.critical("这是一条严重错误 - 紫色")
    
    print("\n" + "="*50 + "\n")
    
    # 方法2: 手动创建使用彩色格式化器的处理器
    logger2 = Logger("ManualColorExample")
    
    # 创建控制台处理器并启用彩色格式
    console_handler = ConsoleHandler(LogLevel.DEBUG, {"use_color": True})
    
    # 或者直接设置彩色格式化器
    color_formatter = ColorFormatter()
    console_handler.set_formatter(color_formatter)
    
    logger2.add_handler(console_handler)
    
    print("手动设置的彩色日志记录器:")
    logger2.debug("这是一条调试信息 - 蓝色")
    logger2.info("这是一条信息 - 绿色")
    logger2.warning("这是一条警告 - 黄色")
    logger2.error("这是一条错误 - 红色")
    logger2.critical("这是一条严重错误 - 紫色")


if __name__ == "__main__":
    main()