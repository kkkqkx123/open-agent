"""
提示词工作流使用示例

演示如何使用新的提示词工作流系统。
"""

from unittest.mock import Mock
from src.services.prompts import (
    PromptInjector,
    PromptLoader,
    PromptRegistry,
    PromptConfigManager,
    create_prompt_agent_workflow,
    create_simple_prompt_agent_workflow,
    get_global_config_manager
)
from src.core.workflow.templates import PromptAgentTemplate, SimplePromptAgentTemplate
from src.core.workflow.templates.registry import get_global_template_registry


def example_1_using_helper_functions():
    """示例1：使用辅助函数创建工作流"""
    print("=== 示例1：使用辅助函数创建工作流 ===")
    
    # 创建模拟的提示词注入器
    mock_registry = Mock(spec=PromptRegistry)
    mock_loader = Mock(spec=PromptLoader)
    mock_loader.load_prompt.return_value = "这是一个测试提示词"
    injector = PromptInjector(mock_loader)
    
    # 创建完整的提示词代理工作流
    workflow = create_prompt_agent_workflow(
        prompt_injector=injector,
        llm_client="gpt-4",
        system_prompt="assistant",
        rules=["safety", "format"],
        user_command="data_analysis",
        cache_enabled=True
    )
    
    print(f"创建工作流: {workflow.name}")
    print(f"工作流描述: {workflow.description}")
    print(f"入口点: {workflow.entry_point}")
    print()


def example_2_using_simple_helper():
    """示例2：使用简化辅助函数"""
    print("=== 示例2：使用简化辅助函数 ===")
    
    # 创建模拟的提示词注入器
    mock_registry = Mock(spec=PromptRegistry)
    mock_loader = Mock(spec=PromptLoader)
    mock_loader.load_prompt.return_value = "这是一个测试提示词"
    injector = PromptInjector(mock_loader)
    
    # 创建简化的提示词代理工作流
    workflow = create_simple_prompt_agent_workflow(
        prompt_injector=injector,
        system_prompt="assistant"
    )
    
    print(f"创建简化工作流: {workflow.name}")
    print(f"工作流描述: {workflow.description}")
    print()


def example_3_using_template_directly():
    """示例3：直接使用模板"""
    print("=== 示例3：直接使用模板 ===")
    
    # 创建模拟的提示词注入器
    mock_registry = Mock(spec=PromptRegistry)
    mock_loader = Mock(spec=PromptLoader)
    mock_loader.load_prompt.return_value = "这是一个测试提示词"
    injector = PromptInjector(mock_loader)
    
    # 直接使用模板
    template = PromptAgentTemplate(prompt_injector=injector)
    
    config = {
        "llm_client": "gpt-4",
        "system_prompt": "assistant",
        "rules": ["safety", "format"],
        "user_command=": "data_analysis"
    }
    
    workflow = template.create_workflow(
        name="direct_template_workflow",
        description="直接使用模板创建的工作流",
        config=config
    )
    
    print(f"直接创建工作流: {workflow.name}")
    print(f"工作流描述: {workflow.description}")
    print()


def example_4_using_registry():
    """示例4：使用模板注册表"""
    print("=== 示例4：使用模板注册表 ===")
    
    # 获取全局注册表
    registry = get_global_template_registry()
    
    # 列出可用模板
    templates = registry.list_templates()
    print(f"可用模板: {templates}")
    
    # 使用注册表创建工作流
    config = {
        "llm_client": "gpt-4",
        "system_prompt": "assistant",
        "rules": ["safety"]
    }
    
    workflow = registry.create_workflow_from_template(
        template_name="prompt_agent",
        name="registry_workflow",
        description="通过注册表创建的工作流",
        config=config
    )
    
    print(f"注册表创建工作流: {workflow.name}")
    print()


def example_5_config_management():
    """示例5：配置管理"""
    print("=== 示例5：配置管理 ===")
    
    # 使用配置管理器
    manager = PromptConfigManager()
    
    # 创建配置
    config = manager.create_config(
        system_prompt="assistant",
        rules=["safety", "format"],
        user_command="data_analysis",
        cache_enabled=True
    )
    
    print(f"创建配置: system_prompt={config.system_prompt}, rules={config.rules}")
    
    # 验证配置
    errors = manager.validate_config(config)
    if errors:
        print(f"配置错误: {errors}")
    else:
        print("配置验证通过")
    
    # 使用全局配置管理器
    global_manager = get_global_config_manager()
    default_config = global_manager.get_agent_config()
    print(f"默认配置: system_prompt={default_config.system_prompt}")
    print()


def example_6_simple_template():
    """示例6：简单模板"""
    print("=== 示例6：简单模板 ===")
    
    # 创建模拟的提示词注入器
    mock_registry = Mock(spec=PromptRegistry)
    mock_loader = Mock(spec=PromptLoader)
    mock_loader.load_prompt.return_value = "这是一个测试提示词"
    injector = PromptInjector(mock_loader)
    
    # 使用简单模板
    template = SimplePromptAgentTemplate(prompt_injector=injector)
    
    config = {
        "llm_client": "gpt-4",
        "system_prompt": "assistant"
    }
    
    workflow = template.create_workflow(
        name="simple_template_workflow",
        description="简单模板工作流",
        config=config
    )
    
    print(f"简单模板工作流: {workflow.name}")
    print(f"模板参数数量: {len(template.get_parameters())}")
    print()


if __name__ == "__main__":
    print("提示词工作流系统使用示例")
    print("=" * 50)
    
    try:
        example_1_using_helper_functions()
        example_2_using_simple_helper()
        example_3_using_template_directly()
        example_4_using_registry()
        example_5_config_management()
        example_6_simple_template()
        
        print("✅ 所有示例运行成功！")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()