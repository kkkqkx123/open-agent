"""
计算器工具实现

提供基本的数学计算功能。
"""

import ast
import operator
from typing import Union, Dict, Any


# 安全的数学操作符映射
SAFE_OPERATORS: Any = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# 安全的数学函数映射
SAFE_FUNCTIONS: Dict[str, Any] = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'len': len,
}


class SafeCalculator:
    """安全计算器
    
    提供安全的数学表达式计算功能，防止代码注入。
    """
    
    @staticmethod
    def evaluate(expression: str) -> Any:
        """安全地计算数学表达式
        
        Args:
            expression: 数学表达式字符串
            
        Returns:
            Union[int, float]: 计算结果
            
        Raises:
            ValueError: 表达式不安全或计算错误
        """
        try:
            # 解析表达式为AST
            node = ast.parse(expression, mode='eval')
            
            # 计算表达式
            result = SafeCalculator._eval_node(node.body)
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {str(e)}")
            
    @staticmethod
    def _eval_node(node: ast.AST) -> Any:
        """递归计算AST节点
        
        Args:
            node: AST节点
            
        Returns:
            Union[int, float]: 计算结果
            
        Raises:
            ValueError: 不安全的操作
        """
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left = SafeCalculator._eval_node(node.left)
            right = SafeCalculator._eval_node(node.right)
            op_type = type(node.op)  # type: ignore
            
            if op_type in SAFE_OPERATORS:
                # 直接调用操作符函数，避免类型检查问题
                try:
                    result = SAFE_OPERATORS[op_type](left, right)
                    # 确保返回类型符合函数签名
                    if isinstance(result, (int, float, complex)):
                        return result
                    else:
                        # 尝试转换为支持的类型
                        return float(result)
                except (ValueError, TypeError, Exception) as e:
                    # 如果调用失败，抛出异常
                    raise ValueError(f"Operator call failed: {e}")
            else:
                raise ValueError(f"Unsupported binary operation: {op_type}")
                
        elif isinstance(node, ast.UnaryOp):
            operand = SafeCalculator._eval_node(node.operand)
            op_type = type(node.op)  # type: ignore
            
            if op_type in SAFE_OPERATORS:
                # 直接调用操作符函数，避免类型检查问题
                try:
                    result = SAFE_OPERATORS[op_type](operand)
                    # 确保返回类型符合函数签名
                    if isinstance(result, (int, float, complex)):
                        return result
                    else:
                        # 尝试转换为支持的类型
                        return float(result)
                except (ValueError, TypeError, Exception) as e:
                    # 如果调用失败，抛出异常
                    raise ValueError(f"操作符调用失败: {e}")
            else:
                raise ValueError(f"Unsupported unary operation: {op_type}")
                
        elif isinstance(node, ast.Call):
            # 只允许安全的函数调用
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in SAFE_FUNCTIONS:
                    args = [SafeCalculator._eval_node(arg) for arg in node.args]
                    result = SAFE_FUNCTIONS[func_name](*args)
                    # 确保返回类型符合函数签名
                    if isinstance(result, (int, float, complex)):
                        return result
                    else:
                        # 尝试转换为支持的类型
                        try:
                            if isinstance(result, (int, float, complex)):
                                return result
                            # 尝试转换为 float
                            return float(result)
                        except (ValueError, TypeError):
                            # 如果转换失败，抛出异常
                            raise ValueError(f"无法将结果 {result} 转换为数字类型")
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Unsupported function call type")
                
        else:
            raise ValueError(f"Unsupported AST node type: {type(node)}")


def calculate(expression: str, precision: int = 2) -> Dict[str, Any]:
    """计算数学表达式
    
    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
        precision: 结果的小数位数，默认为2
        
    Returns:
        Dict[str, Any]: 计算结果
        
    Raises:
        ValueError: 表达式不安全或计算错误
    """
    # 计算表达式
    result = SafeCalculator.evaluate(expression)
    
    # 处理精度
    if isinstance(result, float) and precision >= 0:
        result = round(result, precision)
        
    return {
        "expression": expression,
        "result": result,
        "precision": precision,
        "type": type(result).__name__
    }


# 示例用法
if __name__ == "__main__":
    # 测试计算器
    test_expressions = [
        "2 + 3 * 4",
        "(10 + 5) / 3",
        "2 ** 8",
        "abs(-5)",
        "round(3.14159, 2)",
        "min(1, 2, 3)",
        "max(4, 5, 6)"
    ]
    
    for expr in test_expressions:
        try:
            result = calculate(expr)
            print(f"{expr} = {result['result']}")
        except ValueError as e:
            print(f"Error: {expr} - {e}")