from unittest.mock import Mock
from src.infrastructure.graph.edges.conditions import ConditionEvaluator

# 创建测试状态
mock_result = Mock()
mock_result.get = Mock(return_value=False)
state = {'tool_results': [mock_result]}

# 创建评估器并测试
evaluator = ConditionEvaluator()
result = evaluator._has_errors(state, {}, {})
print('_has_errors result:', result)

# 检查mock_result的属性
print('hasattr(mock_result, "get"):', hasattr(mock_result, 'get'))
print('callable(mock_result.get):', callable(mock_result.get))
print('mock_result.get("success", True):', mock_result.get('success', True))