"""工作流验证示例

演示如何使用 WorkflowValidator 进行静态检测。
"""

from src.infrastructure.graph.workflow_validator import WorkflowValidator, validate_workflow_config


def validate_example_workflow():
    """验证示例工作流"""
    print("🔍 验证示例工作流配置...")
    print("=" * 50)
    
    # 验证正确的工作流配置
    print("\n1. 验证正确的工作流配置:")
    config_path = "configs/workflows/plan_execute_agent_workflow.yaml"
    issues = validate_workflow_config(config_path)
    
    if not issues:
        print("✅ 工作流配置验证通过")
    else:
        print(f"❌ 发现 {len(issues)} 个问题")
    
    print("\n" + "=" * 50)
    
    # 创建一个有问题的配置进行演示
    print("\n2. 验证有问题的配置（演示）:")
    
    problematic_config = {
        "name": "problematic_workflow",
        "description": "有问题的工作流示例",
        "nodes": {
            "node1": {
                "type": "llm_node"
            }
        },
        "edges": [
            {
                "from": "node1",
                "to": "node2",
                "type": "simple"
            },
            {
                "from": "node1",
                "to": "node3", 
                "type": "conditional",
                "condition": "some_condition"
            },
            {
                "from": "node1",
                "to": "node4",
                "type": "conditional",
                "condition": "another_condition"
            }
        ],
        "state_schema": {
            "fields": {
                "messages": {
                    "type": "List[dict]"
                },
                "iteration_count": {
                    "type": "int"
                }
            }
        }
    }
    
    validator = WorkflowValidator()
    validator._validate_config_data(problematic_config, "demo_config")
    validator.print_issues(validator.issues)


def demonstrate_validation_rules():
    """演示验证规则"""
    print("\n📋 工作流验证规则说明:")
    print("=" * 50)
    
    rules = [
        {
            "规则": "条件边配置",
            "说明": "每个节点只能有一个条件边，使用 path_map 定义路由",
            "错误示例": "多个独立的条件边指向同一节点",
            "正确示例": "单个条件边使用 path_map 映射多个目标"
        },
        {
            "规则": "状态字段命名",
            "说明": "避免使用 LangGraph 内置字段名",
            "错误示例": "messages, iteration_count, tool_calls",
            "正确示例": "workflow_messages, workflow_iteration_count"
        },
        {
            "规则": "节点引用",
            "说明": "所有边引用的节点必须存在",
            "错误示例": "边指向不存在的节点",
            "正确示例": "确保所有目标节点都已定义"
        },
        {
            "规则": "终止条件",
            "说明": "工作流必须有明确的终止路径",
            "错误示例": "无限循环没有出口",
            "正确示例": "包含指向 __end__ 的路径"
        }
    ]
    
    for i, rule in enumerate(rules, 1):
        print(f"\n{i}. {rule['规则']}")
        print(f"   说明: {rule['说明']}")
        print(f"   ❌ 错误: {rule['错误示例']}")
        print(f"   ✅ 正确: {rule['正确示例']}")


def show_validation_usage():
    """显示验证工具使用方法"""
    print("\n🛠️ 验证工具使用方法:")
    print("=" * 50)
    
    print("\n1. 在代码中使用:")
    print("""
from src.infrastructure.graph.workflow_validator import validate_workflow_config

# 验证配置文件
issues = validate_workflow_config("configs/workflows/my_workflow.yaml")

# 检查结果
if issues:
    for issue in issues:
        print(f"{issue.severity.value}: {issue.message}")
else:
    print("验证通过")
""")
    
    print("\n2. 命令行使用:")
    print("""
python -m src.infrastructure.graph.workflow_validator configs/workflows/my_workflow.yaml
""")
    
    print("\n3. 集成到 CI/CD:")
    print("""
# 在 CI 脚本中添加验证
python -m src.infrastructure.graph.workflow_validator configs/workflows/
if [ $? -ne 0 ]; then
    echo "工作流配置验证失败"
    exit 1
fi
""")


if __name__ == "__main__":
    validate_example_workflow()
    demonstrate_validation_rules()
    show_validation_usage()