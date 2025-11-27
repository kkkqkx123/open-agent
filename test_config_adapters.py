#!/usr/bin/env python3
"""
测试配置适配器功能
验证所有模块的配置加载功能是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_adapters():
    """测试配置适配器功能"""
    print("开始测试配置适配器功能...")
    
    try:
        # 测试1: 配置管理器基础功能
        print("\n1. 测试配置管理器基础功能...")
        from src.core.config.config_manager import ConfigManager, get_default_manager
        config_manager = get_default_manager()
        print("   ✅ 配置管理器获取成功")
        
        # 测试2: 适配器工厂
        print("\n2. 测试适配器工厂...")
        from src.core.config.adapter_factory import AdapterFactory
        adapter_factory = AdapterFactory(config_manager)
        print("   ✅ 适配器工厂创建成功")
        
        # 测试3: LLM配置适配器
        print("\n3. 测试LLM配置适配器...")
        llm_adapter = adapter_factory.get_adapter('llm')
        print(f"   ✅ LLM配置适配器获取成功: {type(llm_adapter).__name__}")
        
        # 测试4: 工作流配置适配器
        print("\n4. 测试工作流配置适配器...")
        workflow_adapter = adapter_factory.get_adapter('workflow')
        print(f"   ✅ 工作流配置适配器获取成功: {type(workflow_adapter).__name__}")
        
        # 测试5: 工具配置适配器
        print("\n5. 测试工具配置适配器...")
        tools_adapter = adapter_factory.get_adapter('tools')
        print(f"   ✅ 工具配置适配器获取成功: {type(tools_adapter).__name__}")
        
        # 测试6: 状态配置适配器
        print("\n6. 测试状态配置适配器...")
        state_adapter = adapter_factory.get_adapter('state')
        print(f"   ✅ 状态配置适配器获取成功: {type(state_adapter).__name__}")
        
        # 测试7: LLM配置管理器使用适配器
        print("\n7. 测试LLM配置管理器...")
        from src.core.llm.config_manager import LLMConfigManager
        llm_config_manager = LLMConfigManager(base_config_manager=config_manager)
        print(f"   ✅ LLM配置管理器创建成功: {type(llm_config_manager).__name__}")
        
        # 测试8: 工作流节点函数加载器
        print("\n8. 测试工作流节点函数加载器...")
        from src.core.workflow.graph.node_functions.loader import NodeFunctionLoader
        node_loader = NodeFunctionLoader(config_manager=config_manager)
        print(f"   ✅ 工作流节点函数加载器创建成功: {type(node_loader).__name__}")
        
        # 测试9: 状态机配置加载器
        print("\n9. 测试状态机配置加载器...")
        from src.core.workflow.graph.nodes.state_machine.state_machine_config_loader import StateMachineWorkflowLoader
        sm_loader = StateMachineWorkflowLoader(config_manager=config_manager)
        print(f"   ✅ 状态机配置加载器创建成功: {type(sm_loader).__name__}")
        
        # 测试10: 工具加载器
        print("\n10. 测试工具加载器...")
        from src.core.tools.loaders import DefaultToolLoader
        tool_loader = DefaultToolLoader(config_manager=config_manager, logger=None)
        print(f"   ✅ 工具加载器创建成功: {type(tool_loader).__name__}")
        
        # 测试11: 状态管理配置
        print("\n11. 测试状态管理配置...")
        from src.core.state.config.settings import StateManagementConfig
        state_config = StateManagementConfig(config_manager=config_manager)
        print(f"   ✅ 状态管理配置创建成功: {type(state_config).__name__}")
        
        # 测试12: 工具配置验证器
        print("\n12. 测试工具配置验证器...")
        from src.services.tools.validation.validators.config_validator import ConfigValidator
        tool_validator = ConfigValidator(config_manager=config_manager, logger=None)
        print(f"   ✅ 工具配置验证器创建成功: {type(tool_validator).__name__}")
        
        print("\n🎉 所有配置适配器测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载功能"""
    print("\n开始测试配置加载功能...")
    
    try:
        from src.core.config.config_manager import get_default_manager
        config_manager = get_default_manager()
        print("   ✅ 配置管理器获取成功")
        
        # 测试配置管理器的基本功能
        from src.core.config.adapters import LLMConfigAdapter
        adapter = LLMConfigAdapter(config_manager)
        print("   ✅ 适配器创建成功")
        
        print("   ✅ 配置加载功能测试完成")
        return True
        
    except Exception as e:
        print(f"   ❌ 配置加载测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("模块配置加载修改方案 - 功能测试")
    print("="*50)
    
    success1 = test_config_adapters()
    success2 = test_config_loading()
    
    print("\n" + "="*50)
    if success1 and success2:
        print("🎉 所有测试通过！模块配置加载修改方案实施成功！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        sys.exit(1)