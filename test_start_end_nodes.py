#!/usr/bin/env python3
"""START/END节点功能测试

测试新实现的START和END节点及其插件系统。
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_plugin_system():
    """测试插件系统"""
    logger.info("=== 测试插件系统 ===")
    
    try:
        from src.infrastructure.graph.plugins import PluginManager, PluginType
        
        # 创建插件管理器
        plugin_manager = PluginManager("configs/plugins/start_end_plugins.yaml")
        
        # 初始化插件管理器
        success = plugin_manager.initialize()
        logger.info(f"插件管理器初始化: {'成功' if success else '失败'}")
        
        # 获取统计信息
        stats = plugin_manager.get_manager_stats()
        logger.info(f"插件管理器统计: {stats}")
        
        # 获取启用的START插件
        start_plugins = plugin_manager.get_enabled_plugins(PluginType.START)
        logger.info(f"START插件数量: {len(start_plugins)}")
        for plugin in start_plugins:
            logger.info(f"  - {plugin.metadata.name} (v{plugin.metadata.version})")
        
        # 获取启用的END插件
        end_plugins = plugin_manager.get_enabled_plugins(PluginType.END)
        logger.info(f"END插件数量: {len(end_plugins)}")
        for plugin in end_plugins:
            logger.info(f"  - {plugin.metadata.name} (v{plugin.metadata.version})")
        
        # 清理
        plugin_manager.cleanup()
        logger.info("插件系统测试完成")
        
        return True
        
    except Exception as e:
        logger.error(f"插件系统测试失败: {e}")
        return False


def test_start_node():
    """测试START节点"""
    logger.info("=== 测试START节点 ===")
    
    try:
        from src.infrastructure.graph.nodes import StartNode
        from src.infrastructure.graph.states import create_workflow_state
        
        # 创建START节点
        start_node = StartNode("configs/plugins/start_end_plugins.yaml")
        
        # 创建测试状态
        state = create_workflow_state(
            workflow_id="test_workflow",
            input="测试输入",
            max_iterations=10
        )
        
        # 创建配置
        config = {
            "next_node": "test_end_node",
            "context_metadata": {
                "test_mode": True,
                "environment": "test"
            }
        }
        
        # 执行节点
        result = start_node.execute(state, config)
        
        logger.info(f"START节点执行成功")
        logger.info(f"下一个节点: {result.next_node}")
        logger.info(f"状态包含start_metadata: {'start_metadata' in result.state}")
        
        if 'start_metadata' in result.state:
            start_metadata = result.state['start_metadata']
            logger.info(f"执行时间: {start_metadata.get('execution_time', 'N/A')}s")
            logger.info(f"插件执行数量: {start_metadata.get('plugins_executed', 'N/A')}")
            logger.info(f"执行成功: {start_metadata.get('success', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"START节点测试失败: {e}")
        return False


def test_end_node():
    """测试END节点"""
    logger.info("=== 测试END节点 ===")
    
    try:
        from src.infrastructure.graph.nodes import EndNode
        from src.infrastructure.graph.states import create_workflow_state
        
        # 创建END节点
        end_node = EndNode("configs/plugins/start_end_plugins.yaml")
        
        # 创建测试状态（模拟已经执行完的工作流）
        state = create_workflow_state(
            workflow_id="test_workflow",
            input="测试输入",
            output="测试输出",
            max_iterations=10,
            iteration_count=5
        )
        
        # 添加一些测试数据
        state['start_metadata'] = {
            'timestamp': 1234567890.0,
            'execution_time': 2.5,
            'plugins_executed': 3,
            'success': True
        }
        
        state['messages'] = [
            {"role": "user", "content": "测试消息1"},
            {"role": "assistant", "content": "测试回复1"}
        ]
        
        # 创建配置
        config = {
            "context_metadata": {
                "test_mode": True,
                "environment": "test"
            },
            "output_directory": "./test_output"
        }
        
        # 执行节点
        result = end_node.execute(state, config)
        
        logger.info(f"END节点执行成功")
        logger.info(f"下一个节点: {result.next_node}")
        logger.info(f"工作流完成: {result.state.get('workflow_completed', False)}")
        
        if 'end_metadata' in result.state:
            end_metadata = result.state['end_metadata']
            logger.info(f"执行时间: {end_metadata.get('execution_time', 'N/A')}s")
            logger.info(f"插件执行数量: {end_metadata.get('plugins_executed', 'N/A')}")
            logger.info(f"执行成功: {end_metadata.get('success', 'N/A')}")
            
            if 'total_execution_time' in end_metadata:
                logger.info(f"总执行时间: {end_metadata['total_execution_time_formatted']}")
        
        return True
        
    except Exception as e:
        logger.error(f"END节点测试失败: {e}")
        return False


def test_workflow_integration():
    """测试工作流集成"""
    logger.info("=== 测试工作流集成 ===")
    
    try:
        from src.infrastructure.graph.nodes import StartNode, EndNode
        from src.infrastructure.graph.states import create_workflow_state
        
        # 创建节点
        start_node = StartNode("configs/plugins/start_end_plugins.yaml")
        end_node = EndNode("configs/plugins/start_end_plugins.yaml")
        
        # 创建初始状态
        state = create_workflow_state(
            workflow_id="integration_test",
            input="这是一个集成测试",
            max_iterations=5
        )
        
        logger.info(f"初始状态 - 工作流ID: {state.get('workflow_id')}")
        logger.info(f"初始状态 - 输入: {state.get('input')}")
        
        # 执行START节点
        start_config = {
            "next_node": "end_node",
            "context_metadata": {
                "test_mode": True,
                "integration_test": True
            }
        }
        
        start_result = start_node.execute(state, start_config)
        state = start_result.state
        
        logger.info("START节点执行完成")
        
        # 模拟一些中间处理
        state['output'] = "集成测试输出"
        state['iteration_count'] = 3
        state['messages'] = [
            {"role": "user", "content": "这是一个集成测试"},
            {"role": "assistant", "content": "测试处理中..."},
            {"role": "assistant", "content": "处理完成"}
        ]
        
        # 执行END节点
        end_config = {
            "context_metadata": {
                "test_mode": True,
                "integration_test": True
            },
            "output_directory": "./test_output"
        }
        
        end_result = end_node.execute(state, end_config)
        final_state = end_result.state
        
        logger.info("END节点执行完成")
        logger.info(f"最终状态 - 工作流完成: {final_state.get('workflow_completed', False)}")
        
        # 验证结果
        assert final_state.get('workflow_completed'), "工作流应该标记为已完成"
        assert 'start_metadata' in final_state, "应该包含开始元数据"
        assert 'end_metadata' in final_state, "应该包含结束元数据"
        
        logger.info("工作流集成测试成功")
        return True
        
    except Exception as e:
        logger.error(f"工作流集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("开始START/END节点功能测试")
    
    # 创建测试输出目录
    test_output_dir = Path("./test_output")
    test_output_dir.mkdir(exist_ok=True)
    
    # 运行测试
    tests = [
        ("插件系统", test_plugin_system),
        ("START节点", test_start_node),
        ("END节点", test_end_node),
        ("工作流集成", test_workflow_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            logger.info(f"测试结果: {'通过' if success else '失败'}")
        except Exception as e:
            logger.error(f"测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    logger.info(f"\n{'='*50}")
    logger.info("测试总结")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试都通过了！")
        return 0
    else:
        logger.error(f"❌ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)