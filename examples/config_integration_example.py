"""配置系统与基础架构模块集成示例"""

import os
from typing import Dict, Any
from src.infrastructure import DependencyContainer
from infrastructure.config.config_loader import YamlConfigLoader
from src.infrastructure.config import ConfigSystem, ConfigMerger, ConfigValidator, ConfigValidatorTool


def setup_dependency_container(config_path: str = "configs") -> DependencyContainer:
    """设置依赖注入容器
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置好的依赖注入容器
    """
    # 创建容器
    container = DependencyContainer()
    
    # 注册配置加载器
    container.register(YamlConfigLoader, YamlConfigLoader, "default")
    
    # 注册配置系统组件
    container.register(ConfigMerger, ConfigMerger, "default")
    container.register(ConfigValidator, ConfigValidator, "default")
    container.register(ConfigSystem, ConfigSystem, "default")
    
    # 注册配置验证工具
    container.register(ConfigValidatorTool, ConfigValidatorTool, "default")
    
    return container


def main() -> None:
    """主函数"""
    print("配置系统与基础架构模块集成示例")
    print("=" * 50)
    
    # 设置环境变量
    os.environ["AGENT_OPENAI_KEY"] = "your_openai_api_key_here"
    os.environ["AGENT_GEMINI_KEY"] = "your_gemini_api_key_here"
    
    try:
        # 设置依赖注入容器
        container = setup_dependency_container()
        
        # 获取配置加载器
        config_loader = container.get(YamlConfigLoader)
        print(f"✅ 获取配置加载器: {type(config_loader).__name__}")
        
        # 获取配置系统组件
        config_merger = container.get(ConfigMerger)
        config_validator = container.get(ConfigValidator)
        print(f"✅ 获取配置合并器: {type(config_merger).__name__}")
        print(f"✅ 获取配置验证器: {type(config_validator).__name__}")
        
        # 创建配置系统
        config_system = ConfigSystem(
            config_loader=config_loader,
            config_merger=config_merger,
            config_validator=config_validator
        )
        print(f"✅ 创建配置系统: {type(config_system).__name__}")
        
        # 加载全局配置
        global_config = config_system.load_global_config()
        print(f"✅ 加载全局配置:")
        print(f"   - 环境: {global_config.env}")
        print(f"   - 日志级别: {global_config.log_level}")
        print(f"   - 调试模式: {global_config.debug}")
        print(f"   - 热重载: {global_config.hot_reload}")
        
        # 列出可用配置
        llm_configs = config_system.list_configs("llms")
        agent_configs = config_system.list_configs("agents")
        tool_configs = config_system.list_configs("tool-sets")
        
        print(f"✅ 可用LLM配置: {llm_configs}")
        print(f"✅ 可用Agent配置: {agent_configs}")
        print(f"✅ 可用工具配置: {tool_configs}")
        
        # 加载LLM配置
        if "gpt4" in llm_configs:
            gpt4_config = config_system.load_llm_config("gpt4")
            print(f"✅ 加载GPT-4配置:")
            print(f"   - 模型类型: {gpt4_config.model_type}")
            print(f"   - 模型名称: {gpt4_config.model_name}")
            print(f"   - 基础URL: {gpt4_config.base_url}")
            print(f"   - 温度: {gpt4_config.parameters.get('temperature')}")
        
        # 加载Agent配置
        if "code_agent" in agent_configs:
            code_agent_config = config_system.load_agent_config("code_agent")
            print(f"✅ 加载代码Agent配置:")
            print(f"   - 名称: {code_agent_config.name}")
            print(f"   - LLM: {code_agent_config.llm}")
            print(f"   - 工具集: {code_agent_config.tool_sets}")
            print(f"   - 工具: {code_agent_config.tools}")
            print(f"   - 最大迭代次数: {code_agent_config.max_iterations}")
        
        # 使用配置验证工具
        validator_tool = ConfigValidatorTool()
        print(f"✅ 创建配置验证工具: {type(validator_tool).__name__}")
        
        # 验证所有配置
        print("\n验证所有配置...")
        all_valid = validator_tool.validate_all()
        
        if all_valid:
            print("✅ 所有配置验证通过")
        else:
            print("❌ 部分配置验证失败")
        
        # 监听配置变化
        print("\n设置配置变化监听...")
        
        def config_change_callback(path: str, config: Dict[str, Any]) -> None:
            print(f"🔄 配置文件变化: {path}")
        
        config_system.watch_for_changes(config_change_callback)
        print("✅ 配置变化监听已设置")
        
        # 获取环境变量解析器
        env_resolver = config_system.get_env_resolver()
        print(f"✅ 获取环境变量解析器: {type(env_resolver).__name__}")
        print(f"   - 环境变量前缀: {env_resolver.prefix}")
        
        # 检查环境变量
        if env_resolver.has_env_var("OPENAI_KEY"):
            openai_key = env_resolver.get_env_var("OPENAI_KEY")
            print(f"   - OPENAI_KEY: {openai_key[:10]}...")
        
        print("\n集成示例完成!")
        
        # 清理
        config_system.stop_watching()
        print("✅ 已停止配置监听")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理环境变量
        if "AGENT_OPENAI_KEY" in os.environ:
            del os.environ["AGENT_OPENAI_KEY"]
        if "AGENT_GEMINI_KEY" in os.environ:
            del os.environ["AGENT_GEMINI_KEY"]


if __name__ == "__main__":
    main()