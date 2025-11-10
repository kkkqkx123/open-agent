#!/usr/bin/env python3
"""
工作流配置验证脚本

用于验证工作流配置的有效性，检测潜在问题如：
- 死循环
- 内存泄漏风险（如自调用）
- 执行不存在的节点或边
- 状态模式冲突
- 条件边冲突
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict, deque


class WorkflowConfigValidator:
    """工作流配置验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """验证工作流配置文件"""
        path = Path(file_path)
        if not path.exists():
            return {
                "valid": False,
                "errors": [f"文件不存在: {file_path}"],
                "warnings": []
            }
        
        # 加载配置
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    return {
                        "valid": False,
                        "errors": [f"不支持的文件格式: {path.suffix}"],
                        "warnings": []
                    }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"配置文件加载失败: {e}"],
                "warnings": []
            }
        
        return self.validate_config(config)
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证工作流配置"""
        self.errors = []
        self.warnings = []
        
        # 基本结构验证
        self._validate_basic_structure(config)
        
        if not self.errors:  # 只有基本结构正确才进行深度验证
            # 节点验证
            self._validate_nodes(config)
            
            # 边验证
            self._validate_edges(config)
            
            # 状态模式验证
            self._validate_state_schema(config)
            
            # 图结构验证
            self._validate_graph_structure(config)
            
            # 死循环检测
            self._detect_cycles(config)
            
            # 内存泄漏风险检测
            self._detect_memory_leaks(config)
        
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def _validate_basic_structure(self, config: Dict[str, Any]):
        """验证基本结构"""
        required_fields = ['name', 'nodes', 'edges', 'entry_point']
        
        for field in required_fields:
            if field not in config:
                self.errors.append(f"缺少必需字段: {field}")
        
        if 'nodes' in config and not isinstance(config['nodes'], dict):
            self.errors.append("'nodes' 必须是字典类型")
        
        if 'edges' in config and not isinstance(config['edges'], list):
            self.errors.append("'edges' 必须是列表类型")
    
    def _validate_nodes(self, config: Dict[str, Any]):
        """验证节点配置"""
        nodes = config.get('nodes', {})
        entry_point = config.get('entry_point')
        
        if entry_point and entry_point not in nodes:
            self.errors.append(f"入口点节点不存在: {entry_point}")
        
        # 检查节点配置
        for node_id, node_config in nodes.items():
            if not isinstance(node_config, dict):
                self.errors.append(f"节点 '{node_id}' 配置必须是字典类型")
                continue
            
            # 检查节点类型
            node_type = node_config.get('type', 'default')
            if node_type not in ['llm_node', 'tool_node', 'agent_node', 'wait_node', 'analysis_node', 'default']:
                self.warnings.append(f"节点 '{node_id}' 使用了未知的类型: {node_type}")
            
            # 检查函数名
            if 'function_name' in node_config:
                func_name = node_config['function_name']
                if not func_name or not isinstance(func_name, str):
                    self.errors.append(f"节点 '{node_id}' 的函数名无效: {func_name}")
    
    def _validate_edges(self, config: Dict[str, Any]):
        """验证边配置"""
        nodes = config.get('nodes', {})
        edges = config.get('edges', [])
        
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                self.errors.append(f"边 {i} 必须是字典类型")
                continue
            
            # 检查必需字段
            if 'from' not in edge:
                self.errors.append(f"边 {i} 缺少 'from' 字段")
            if 'to' not in edge:
                self.errors.append(f"边 {i} 缺少 'to' 字段")
            if 'type' not in edge:
                self.errors.append(f"边 {i} 缺少 'type' 字段")
            
            # 检查节点是否存在
            from_node = edge.get('from')
            to_node = edge.get('to')
            
            if from_node and from_node not in nodes:
                self.errors.append(f"边 {i} 的源节点不存在: {from_node}")
            
            if to_node and to_node not in nodes:
                self.errors.append(f"边 {i} 的目标节点不存在: {to_node}")
            
            # 检查边类型
            edge_type = edge.get('type')
            if edge_type not in ['simple', 'conditional', 'parallel', 'loop']:
                self.warnings.append(f"边 {i} 使用了未知的类型: {edge_type}")
            
            # 条件边需要条件表达式
            if edge_type == 'conditional' and 'condition' not in edge:
                self.errors.append(f"条件边 {i} 缺少条件表达式")
    
    def _validate_state_schema(self, config: Dict[str, Any]):
        """验证状态模式"""
        state_schema = config.get('state_schema')
        if not state_schema:
            return
        
        if not isinstance(state_schema, dict):
            self.errors.append("状态模式必须是字典类型")
            return
        
        # 检查LangGraph内置字段冲突
        reserved_fields = {'messages', 'checkpoint', 'config', 'metadata'}
        fields = state_schema.get('fields', {})
        
        if isinstance(fields, dict):
            for field_name in fields.keys():
                if field_name in reserved_fields:
                    self.warnings.append(f"状态字段 '{field_name}' 可能与LangGraph内置字段冲突")
        
        # 检查状态模式名称
        schema_name = state_schema.get('name')
        if not schema_name:
            self.warnings.append("状态模式缺少名称")
    
    def _validate_graph_structure(self, config: Dict[str, Any]):
        """验证图结构"""
        nodes = config.get('nodes', {})
        edges = config.get('edges', [])
        entry_point = config.get('entry_point')
        
        if not entry_point:
            return
        
        # 构建邻接表
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for edge in edges:
            from_node = edge.get('from')
            to_node = edge.get('to')
            if from_node and to_node:
                graph[from_node].append(to_node)
                in_degree[to_node] += 1
        
        # 检查孤立节点
        for node_id in nodes:
            if node_id not in graph and in_degree[node_id] == 0 and node_id != entry_point:
                self.warnings.append(f"孤立节点 (无入边也无出边): {node_id}")
        
        # 检查不可达节点
        reachable = self._find_reachable_nodes(graph, entry_point)
        unreachable = set(nodes.keys()) - reachable
        if unreachable:
            self.warnings.append(f"不可达节点: {', '.join(unreachable)}")
        
        # 检查条件边冲突
        self._check_conditional_edge_conflicts(edges)
    
    def _find_reachable_nodes(self, graph: Dict[str, List[str]], start: str) -> Set[str]:
        """查找从起始节点可达的所有节点"""
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        while queue:
            current = queue.popleft()
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return visited
    
    def _check_conditional_edge_conflicts(self, edges: List[Dict[str, Any]]):
        """检查条件边冲突"""
        conditional_edges = defaultdict(list)
        
        for i, edge in enumerate(edges):
            if edge.get('type') == 'conditional':
                from_node = edge.get('from')
                if from_node:
                    conditional_edges[from_node].append((i, edge))
        
        for from_node, edges_list in conditional_edges.items():
            if len(edges_list) > 1:
                # 检查是否有相同的条件
                conditions = [edge[1].get('condition') for edge in edges_list]
                if len(set(conditions)) != len(conditions):
                    self.warnings.append(f"节点 '{from_node}' 的条件边有重复的条件表达式")
                
                # 检查是否有默认路径（没有else条件）
                has_default = any('default' in edge[1] for edge in edges_list)
                if not has_default:
                    self.warnings.append(f"节点 '{from_node}' 的条件边缺少默认路径")
    
    def _detect_cycles(self, config: Dict[str, Any]):
        """检测图中的循环"""
        nodes = config.get('nodes', {})
        edges = config.get('edges', [])
        
        # 构建图
        graph = defaultdict(list)
        for edge in edges:
            from_node = edge.get('from')
            to_node = edge.get('to')
            if from_node and to_node:
                graph[from_node].append(to_node)
        
        # 使用DFS检测循环
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in nodes:
            if node not in visited:
                dfs(node, [])
        
        if cycles:
            for cycle in cycles:
                self.warnings.append(f"检测到循环: {' -> '.join(cycle)}")
    
    def _detect_memory_leaks(self, config: Dict[str, Any]):
        """检测内存泄漏风险"""
        nodes = config.get('nodes', {})
        edges = config.get('edges', [])
        
        # 检测自调用
        for edge in edges:
            from_node = edge.get('from')
            to_node = edge.get('to')
            if from_node == to_node:
                self.warnings.append(f"节点 '{from_node}' 存在自调用，可能导致内存泄漏")
        
        # 检测无限循环风险
        self._detect_infinite_loop_risk(config)
        
        # 检测状态膨胀风险
        self._detect_state_bloat_risk(config)
    
    def _detect_infinite_loop_risk(self, config: Dict[str, Any]):
        """检测无限循环风险"""
        nodes = config.get('nodes', {})
        edges = config.get('edges', [])
        
        # 查找没有退出条件的循环
        graph = defaultdict(list)
        edge_types = {}
        
        for edge in edges:
            from_node = edge.get('from')
            to_node = edge.get('to')
            edge_type = edge.get('type')
            if from_node and to_node:
                graph[from_node].append(to_node)
                edge_types[(from_node, to_node)] = edge_type
        
        # 检测循环中的边是否都有适当的退出条件
        # 这里简化处理，实际应该更复杂的分析
        for from_node, to_nodes in graph.items():
            if from_node in to_nodes:
                # 自循环
                edge_type = edge_types.get((from_node, from_node))
                if edge_type == 'simple':
                    self.warnings.append(f"节点 '{from_node}' 的自循环使用简单边，可能导致无限循环")
    
    def _detect_state_bloat_risk(self, config: Dict[str, Any]):
        """检测状态膨胀风险"""
        state_schema = config.get('state_schema', {})
        fields = state_schema.get('fields', {})
        
        if not isinstance(fields, dict):
            return
        
        # 检查大字段类型
        large_types = {'List[dict]', 'Dict', 'Any'}
        for field_name, field_config in fields.items():
            if isinstance(field_config, dict):
                field_type = field_config.get('type', '')
                if any(large_type in field_type for large_type in large_types):
                    self.warnings.append(f"状态字段 '{field_name}' 使用大类型 '{field_type}'，可能导致内存问题")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python validate_workflow_config.py <workflow_config_file>")
        print("示例: python validate_workflow_config.py configs/workflows/bad_example_workflow.yaml")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    print(f"正在验证工作流配置: {config_file}")
    print("=" * 60)
    
    validator = WorkflowConfigValidator()
    result = validator.validate_file(config_file)
    
    # 显示结果
    if result["valid"]:
        print("✅ 配置有效")
    else:
        print("❌ 配置无效")
    
    if result["errors"]:
        print(f"\n错误 ({len(result['errors'])}):")
        for i, error in enumerate(result["errors"], 1):
            print(f"  {i}. {error}")
    
    if result["warnings"]:
        print(f"\n警告 ({len(result['warnings'])}):")
        for i, warning in enumerate(result["warnings"], 1):
            print(f"  {i}. {warning}")
    
    # 返回适当的退出码
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()