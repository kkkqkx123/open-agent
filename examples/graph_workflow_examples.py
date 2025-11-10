#!/usr/bin/env python3
"""
GraphWorkflow 快速示例

展示如何使用 GraphWorkflow 基类创建和运行基于图的工作流。
"""

import asyncio
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入 GraphWorkflow
from src.application.workflow.graph_workflow import GraphWorkflow, SimpleGraphWorkflow


def example_1_basic_usage():
    """示例1: 基本用法 - 从配置文件创建工作流"""
    print("=== 示例1: 基本用法 ===")
    
    # 从配置文件创建工作流
    config_path = Path("configs/workflows/examples/simple_data_processing.yaml")
    
    try:
        workflow = GraphWorkflow(config_path)
        print(f"✅ 工作流创建成功: {workflow.name}")
        print(f"   描述: {workflow.description}")
        print(f"   版本: {workflow.version}")
        
        # 验证配置
        errors = workflow.validate()
        if errors:
            print(f"❌ 配置错误: {errors}")
        else:
            print("✅ 配置验证通过")
            
        # 获取工作流信息
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()
        print(f"📊 节点数量: {len(nodes)}")
        print(f"🔗 边数量: {len(edges)}")
        
    except Exception as e:
        print(f"❌ 创建工作流失败: {e}")


def example_2_dict_config():
    """示例2: 使用字典配置创建工作流"""
    print("\n=== 示例2: 字典配置 ===")
    
    # 定义简单的配置
    config = {
        "name": "quick_workflow",
        "description": "快速创建工作流示例",
        "version": "1.0",
        "entry_point": "start",
        "nodes": {
            "start": {
                "name": "start",
                "function_name": "process_start",
                "description": "开始节点"
            },
            "end": {
                "name": "end",
                "function_name": "process_end",
                "description": "结束节点"
            }
        },
        "edges": [
            {
                "from": "start",
                "to": "end",
                "type": "simple"
            }
        ],
        "state_schema": {
            "name": "QuickState",
            "fields": {
                "messages": {
                    "type": "List[dict]",
                    "default": []
                },
                "result": {
                    "type": "str",
                    "default": ""
                }
            }
        }
    }
    
    try:
        workflow = GraphWorkflow(config)
        print(f"✅ 工作流创建成功: {workflow.name}")
        
        # 导出配置
        exported_config = workflow.export_config()
        print(f"📋 导出配置包含 {len(exported_config)} 个顶级字段")
        
    except Exception as e:
        print(f"❌ 创建工作流失败: {e}")


def example_3_simple_graph_workflow():
    """示例3: 使用 SimpleGraphWorkflow 快速创建"""
    print("\n=== 示例3: SimpleGraphWorkflow ===")
    
    # 定义节点
    nodes = [
        {
            "name": "input_processor",
            "function_name": "process_input",
            "description": "处理输入数据"
        },
        {
            "name": "output_generator",
            "function_name": "generate_output",
            "description": "生成输出"
        }
    ]
    
    # 定义边
    edges = [
        {
            "from": "input_processor",
            "to": "output_generator",
            "type": "simple"
        }
    ]
    
    try:
        workflow = SimpleGraphWorkflow(
            name="simple_example",
            nodes=nodes,
            edges=edges,
            description="简单示例工作流"
        )
        print(f"✅ 简单工作流创建成功: {workflow.name}")
        
        # 获取状态模式
        schema = workflow.get_state_schema()
        print(f"🔧 状态模式: {schema['name']}")
        
    except Exception as e:
        print(f"❌ 创建工作流失败: {e}")


async def example_4_async_execution():
    """示例4: 异步执行"""
    print("\n=== 示例4: 异步执行 ===")
    
    # 创建简单工作流
    config = {
        "name": "async_workflow",
        "description": "异步执行示例",
        "version": "1.0",
        "entry_point": "process",
        "nodes": {
            "process": {
                "name": "process",
                "function_name": "async_process",
                "description": "异步处理节点"
            }
        },
        "edges": [],
        "state_schema": {
            "name": "AsyncState",
            "fields": {
                "data": {"type": "str", "default": ""},
                "processed": {"type": "bool", "default": false}
            }
        }
    }
    
    try:
        workflow = GraphWorkflow(config)
        print(f"✅ 异步工作流创建成功: {workflow.name}")
        
        # 模拟异步执行
        initial_data = {"data": "test data"}
        print(f"🚀 开始异步执行...")
        
        # 注意：这里需要实际的异步函数注册
        # result = await workflow.run_async(initial_data)
        # print(f"✅ 异步执行完成: {result}")
        
        print("✅ 异步执行框架准备就绪（需要注册实际的异步函数）")
        
    except Exception as e:
        print(f"❌ 异步执行失败: {e}")


def example_5_workflow_info():
    """示例5: 获取工作流信息"""
    print("\n=== 示例5: 工作流信息 ===")
    
    try:
        # 使用示例配置
        config = {
            "name": "info_demo",
            "description": "信息展示示例",
            "version": "1.0",
            "entry_point": "start",
            "nodes": {
                "start": {"name": "start", "function_name": "func_start"},
                "middle": {"name": "middle", "function_name": "func_middle"},
                "end": {"name": "end", "function_name": "func_end"}
            },
            "edges": [
                {"from": "start", "to": "middle", "type": "simple"},
                {"from": "middle", "to": "end", "type": "simple"}
            ],
            "state_schema": {
                "name": "DemoState",
                "fields": {
                    "counter": {"type": "int", "default": 0},
                    "messages": {"type": "List[str]", "default": []}
                }
            }
        }
        
        workflow = GraphWorkflow(config)
        
        # 基本信息
        print(f"📋 工作流信息:")
        print(f"   名称: {workflow.name}")
        print(f"   描述: {workflow.description}")
        print(f"   版本: {workflow.version}")
        
        # 详细信息
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()
        schema = workflow.get_state_schema()
        
        print(f"🔧 技术详情:")
        print(f"   节点数量: {len(nodes)}")
        print(f"   边数量: {len(edges)}")
        print(f"   状态模式: {schema['name']}")
        print(f"   状态字段: {list(schema['fields'].keys())}")
        
        # 可视化数据
        viz_data = workflow.get_visualization_data()
        print(f"📊 可视化数据包含 {len(viz_data)} 个字段")
        
    except Exception as e:
        print(f"❌ 获取信息失败: {e}")


def example_6_error_handling():
    """示例6: 错误处理"""
    print("\n=== 示例6: 错误处理 ===")
    
    from src.application.workflow.graph_workflow import (
        GraphWorkflowError,
        GraphWorkflowConfigError,
        GraphWorkflowExecutionError
    )
    
    # 测试配置错误
    try:
        workflow = GraphWorkflow({})  # 空配置
    except GraphWorkflowConfigError as e:
        print(f"✅ 捕获配置错误: {type(e).__name__}")
    except Exception as e:
        print(f"✅ 捕获其他错误: {type(e).__name__}: {e}")
    
    # 测试无效配置
    try:
        invalid_config = {
            "name": "invalid",
            "description": "测试无效配置",
            "nodes": {
                "node1": {"name": "node1"}  # 缺少 function_name
            },
            "edges": []
        }
        workflow = GraphWorkflow(invalid_config)
        errors = workflow.validate()
        if errors:
            print(f"✅ 验证发现错误: {len(errors)} 个")
    except Exception as e:
        print(f"✅ 捕获验证错误: {type(e).__name__}: {e}")


def main():
    """主函数 - 运行所有示例"""
    print("🚀 GraphWorkflow 快速示例")
    print("=" * 50)
    
    # 运行基本示例
    example_1_basic_usage()
    example_2_dict_config()
    example_3_simple_graph_workflow()
    
    # 运行异步示例
    asyncio.run(example_4_async_execution())
    
    # 运行信息和错误处理示例
    example_5_workflow_info()
    example_6_error_handling()
    
    print("\n" + "=" * 50)
    print("✅ 所有示例运行完成！")
    print("\n📚 更多信息请参考:")
    print("   - docs/workflow/graph_workflow_guide.md")
    print("   - configs/workflows/examples/")
    print("\n🔧 下一步:")
    print("   1. 注册实际的节点函数")
    print("   2. 运行真实的工作流")
    print("   3. 集成到您的应用中")


if __name__ == "__main__":
    main()