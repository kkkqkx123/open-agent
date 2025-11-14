"""提示词管理模块演示"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config.config_loader import YamlConfigLoader
from src.domain.prompts.registry import PromptRegistry
from src.domain.prompts.loader import PromptLoader
from src.domain.prompts.injector import PromptInjector
from src.domain.prompts.models import PromptConfig
from src.application.workflow.state import AgentState  # type: ignore
from src.domain.prompts.langgraph_integration import create_simple_workflow


def main():
    """主函数"""
    print("=== 提示词管理模块演示 ===\n")
    
    # 1. 初始化配置加载器
    print("1. 初始化配置加载器...")
    config_loader = YamlConfigLoader("configs")
    
    # 2. 创建提示词注册表
    print("2. 创建提示词注册表...")
    registry = PromptRegistry(config_loader)
    
    # 3. 验证注册表
    print("3. 验证注册表完整性...")
    try:
        registry.validate_registry()
        print("   ✓ 注册表验证通过")
    except Exception as e:
        print(f"   ✗ 注册表验证失败: {e}")
        return
    
    # 4. 列出所有提示词
    print("\n4. 列出所有提示词...")
    for category in ["system", "rules", "user_commands"]:
        prompts = registry.list_prompts(category)
        print(f"   {category}:")
        for prompt in prompts:
            composite_mark = " (复合)" if prompt.is_composite else ""
            print(f"     - {prompt.name}{composite_mark}: {prompt.description}")
    
    # 5. 创建提示词加载器
    print("\n5. 创建提示词加载器...")
    loader = PromptLoader(registry)
    
    # 6. 加载简单提示词
    print("\n6. 加载简单提示词...")
    try:
        assistant_prompt = loader.load_prompt("system", "assistant")
        print(f"   助手提示词: {assistant_prompt[:50]}...")
    except Exception as e:
        print(f"   ✗ 加载失败: {e}")
    
    # 7. 加载复合提示词
    print("\n7. 加载复合提示词...")
    try:
        coder_prompt = loader.load_prompt("system", "coder")
        print(f"   代码专家提示词: {coder_prompt[:100]}...")
        print(f"   包含 'PEP8规范': {'PEP8规范' in coder_prompt}")
    except Exception as e:
        print(f"   ✗ 加载失败: {e}")
    
    # 8. 创建提示词注入器
    print("\n8. 创建提示词注入器...")
    injector = PromptInjector(loader)
    
    # 9. 配置并注入提示词
    print("\n9. 配置并注入提示词...")
    config = PromptConfig(
        system_prompt="assistant",
        rules=["safety", "format"],
        user_command="data_analysis"
    )
    
    state = {}  # type: ignore
    state = injector.inject_prompts(state, config)  # type: ignore

    print(f"   注入了 {len(state['messages'])} 条消息:")
    for i, message in enumerate(state['messages']):
        message_type = type(message).__name__
        content = getattr(message, 'content', str(message))
        content_preview = content[:50] + "..." if len(content) > 50 else content
        print(f"     {i+1}. [{message_type}] {content_preview}")
    
    # 10. 测试缓存机制
    print("\n10. 测试缓存机制...")
    print(f"    缓存大小: {len(loader._cache)}")
    
    # 再次加载相同提示词（应该从缓存获取）
    assistant_prompt_cached = loader.load_prompt("system", "assistant")
    print(f"    再次加载助手提示词: {assistant_prompt_cached[:50]}...")
    print(f"    缓存大小: {len(loader._cache)}")
    
    # 清空缓存
    loader.clear_cache()
    print(f"    清空缓存后大小: {len(loader._cache)}")
    
    # 11. 创建简单工作流
    print("\n11. 创建简单工作流...")
    workflow = create_simple_workflow(injector)
    print(f"    工作流描述: {workflow['description']}")
    
    # 运行工作流
    result_state = workflow["run"]()
    print(f"    工作流结果: {len(result_state.messages)} 条消息")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()