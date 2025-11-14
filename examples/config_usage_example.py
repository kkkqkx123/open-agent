"""配置系统使用示例"""

from src.infrastructure.config import ConfigFactory
from src.infrastructure.config.interfaces import IConfigSystem


def basic_usage_example():
    """基本使用示例"""
    # 创建配置系统
    config_system = ConfigFactory.create_config_system()
    
    # 加载全局配置
    global_config = config_system.load_global_config()
    print(f"日志级别: {global_config.log_level}")
    print(f"运行环境: {global_config.env}")
    
    # 加载LLM配置
    try:
        llm_config = config_system.load_llm_config("gpt-4")
        print(f"模型名称: {llm_config.model_name}")
        print(f"提供商: {llm_config.provider}")
    except Exception as e:
        print(f"LLM配置加载失败: {e}")


def validation_example():
    """验证示例"""
    config_system = ConfigFactory.create_config_system()
    
    try:
        # 加载全局配置并验证
        global_config = config_system.load_global_config()
        print(f"配置验证成功: {global_config is not None}")
    except Exception as e:
        print(f"配置验证失败: {e}")


if __name__ == "__main__":
    basic_usage_example()
    validation_example()