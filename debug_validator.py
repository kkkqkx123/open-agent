"""调试验证器问题"""

import yaml
from src.infrastructure.graph.workflow_validator import WorkflowValidator

# 加载配置文件
with open('configs/workflows/plan_execute_agent_workflow.yaml', 'r', encoding='utf-8') as f:
    config_data = yaml.safe_load(f)

print("配置加载成功")
print("节点:", list(config_data["nodes"].keys()))
print("边数量:", len(config_data["edges"]))

# 逐步测试验证器
validator = WorkflowValidator()

# 测试基本验证
print("\n1. 测试基本配置验证...")
try:
    validator._validate_config_data(config_data, "test")
    print("基本验证完成，问题数量:", len(validator.issues))
    for issue in validator.issues:
        print(f"  {issue.severity.value}: {issue.message}")
except Exception as e:
    print(f"基本验证出错: {e}")
    import traceback
    traceback.print_exc()

# 重置问题列表
validator.issues = []

# 测试连通性验证
print("\n2. 测试连通性验证...")
try:
    validator._validate_connectivity_from_dict(config_data, "test")
    print("连通性验证完成，问题数量:", len(validator.issues))
    for issue in validator.issues:
        print(f"  {issue.severity.value}: {issue.message}")
except Exception as e:
    print(f"连通性验证出错: {e}")
    import traceback
    traceback.print_exc()