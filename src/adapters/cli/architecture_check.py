"""架构分层检查工具"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass

from src.interfaces.container.exceptions import ContainerException
from .check_result import CheckResult


class ArchitectureViolationError(ContainerException):
    """架构违规异常"""
    pass


@dataclass
class LayerRule:
    """分层规则"""

    layer_name: str
    allowed_dependencies: Set[str]  # 允许依赖的层级
    forbidden_dependencies: Set[str]  # 禁止依赖的层级
    path_patterns: List[str]  # 路径模式


class ArchitectureChecker:
    """架构分层检查器"""

    def __init__(self, base_path: str = "src"):
        self.base_path = Path(base_path)
        self.layer_rules = self._define_layer_rules()
        self.import_graph: Dict[str, Set[str]] = {}
        self.layer_mapping: Dict[str, str] = {}

    def _define_layer_rules(self) -> Dict[str, LayerRule]:
        """定义分层规则"""
        return {
            "domain": LayerRule(
                layer_name="domain",
                allowed_dependencies=set(),  # 领域层不依赖任何其他层级
                forbidden_dependencies={
                    "infrastructure",
                    "application",
                    "presentation",
                },
                path_patterns=["src/domain/*"],
            ),
            "infrastructure": LayerRule(
                layer_name="infrastructure",
                allowed_dependencies={"domain"},  # 基础设施层可以依赖领域层
                forbidden_dependencies={"application", "presentation"},
                path_patterns=["src/infrastructure/*"],
            ),
            "application": LayerRule(
                layer_name="application",
                allowed_dependencies={
                    "domain",
                    "infrastructure",
                },  # 应用层可以依赖领域层和基础设施层
                forbidden_dependencies={"presentation"},
                path_patterns=["src/application/*"],
            ),
            "presentation": LayerRule(
                layer_name="presentation",
                allowed_dependencies={
                    "domain",
                    "infrastructure",
                    "application",
                },  # 表现层可以依赖所有其他层级
                forbidden_dependencies=set(),
                path_patterns=["src/presentation/*"],
            ),
        }

    def check_architecture(self) -> List[CheckResult]:
        """检查架构分层"""
        results = []

        # 构建导入图
        self._build_import_graph()

        # 映射文件到层级
        self._map_files_to_layers()

        # 检查每个文件的依赖关系
        violations = self._check_layer_violations()

        if violations:
            for violation in violations:
                results.append(
                    CheckResult(
                        component="architecture_layer",
                        status="ERROR",
                        message=f"Layer violation: {violation['from_file']} ({violation['from_layer']}) "
                        f"imports {violation['to_file']} ({violation['to_layer']})",
                        details=violation,
                    )
                )
        else:
            results.append(
                CheckResult(
                    component="architecture_layer",
                    status="PASS",
                    message="No architecture layer violations found",
                )
            )

        # 检查循环依赖
        circular_deps = self._check_circular_dependencies()
        if circular_deps:
            for cycle in circular_deps:
                results.append(
                    CheckResult(
                        component="circular_dependency",
                        status="ERROR",
                        message=f"Circular dependency detected: {' -> '.join(cycle)}",
                        details={"cycle": cycle},
                    )
                )
        else:
            results.append(
                CheckResult(
                    component="circular_dependency",
                    status="PASS",
                    message="No circular dependencies found",
                )
            )

        return results

    def _build_import_graph(self) -> None:
        """构建导入图"""
        self.import_graph.clear()

        for py_file in self.base_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                # 尝试多种编码方式
                content = None
                for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
                    try:
                        with open(py_file, "r", encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue

                if content is None:
                    print(f"Warning: Failed to decode {py_file} with any encoding")
                    continue

                tree = ast.parse(content)
                imports = self._extract_imports(tree, py_file)
                self.import_graph[str(py_file)] = imports

            except Exception as e:
                print(f"Warning: Failed to parse {py_file}: {e}")

    def _extract_imports(self, tree: ast.AST, current_file: Path) -> Set[str]:
        """提取导入语句"""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_path = self._resolve_import_path(alias.name, current_file)
                    if import_path is not None:
                        imports.add(import_path)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # 构建完整的模块名，包括相对导入的点
                    module_name = "." * node.level + (node.module or "")
                    import_path = self._resolve_import_path(module_name, current_file)
                    if import_path is not None:
                        imports.add(import_path)
                else:
                    # 处理 from . import xxx 的情况
                    module_name = "." * node.level
                    import_path = self._resolve_import_path(module_name, current_file)
                    if import_path is not None:
                        imports.add(import_path)

        return imports

    def _resolve_import_path(
        self, module_name: str, current_file: Path
    ) -> Optional[str]:
        """解析导入路径为文件路径"""
        # 处理相对导入
        if module_name.startswith("."):
            level = len(module_name) - len(module_name.lstrip("."))
            module_name = module_name.lstrip(".")

            # 计算相对路径 - 从当前文件的目录开始，向上移动 (level-1) 层
            parent_dir = current_file.parent
            for _ in range(level - 1):
                parent_dir = parent_dir.parent

            if module_name:
                import_path = parent_dir / module_name.replace(".", "/")
            else:
                import_path = parent_dir
        else:
            # 处理绝对导入
            if module_name.startswith("src"):
                # 确保我们使用正确的基础路径
                import_path = self.base_path / module_name.replace(".", "/").replace(
                    "src/", "", 1
                )
            else:
                # 外部库导入，跳过
                return None

        # 查找对应的Python文件 - 优先查找.py文件
        py_file = Path(str(import_path) + ".py")
        if py_file.exists():
            return str(py_file)

        # 如果.py文件不存在，尝试查找包目录
        if import_path.is_dir():
            init_file = import_path / "__init__.py"
            if init_file.exists():
                return str(init_file)

        # 尝试查找包目录（如果import_path不是目录）
        if import_path.parent.exists():
            # 只有当模块名为空时（即 from . import xxx）才返回父目录的__init__.py
            if not module_name:
                init_file = import_path.parent / "__init__.py"
                if init_file.exists():
                    return str(init_file)

        return None

    def _map_files_to_layers(self) -> None:
        """映射文件到层级"""
        self.layer_mapping.clear()

        for file_path in self.import_graph.keys():
            layer = self._determine_layer(file_path)
            if layer:
                self.layer_mapping[file_path] = layer

    def _determine_layer(self, file_path: str) -> Optional[str]:
        """确定文件所属层级"""
        try:
            path_obj = Path(file_path)
            relative_path = path_obj.relative_to(self.base_path.parent)
        except ValueError:
            # 如果无法计算相对路径，尝试直接匹配
            path_obj = Path(file_path)
            relative_path = path_obj

        for layer_name, rule in self.layer_rules.items():
            for pattern in rule.path_patterns:
                if self._match_path_pattern(relative_path, pattern):
                    return layer_name

        return None

    def _match_path_pattern(self, path: Path, pattern: str) -> bool:
        """匹配路径模式"""
        pattern_parts = pattern.split("/")
        path_parts = path.parts

        # 处理绝对路径和相对路径
        if len(path_parts) >= len(pattern_parts):
            # 从后向前匹配
            for i in range(1, len(pattern_parts) + 1):
                pattern_part = pattern_parts[-i]
                path_part = path_parts[-i]

                if pattern_part != "*" and pattern_part != path_part:
                    return False
            return True
        else:
            return False

    def _check_layer_violations(self) -> List[Dict[str, Any]]:
        """检查层级违规"""
        violations = []

        for from_file, imports in self.import_graph.items():
            from_layer = self.layer_mapping.get(from_file)
            if not from_layer:
                continue

            from_rule = self.layer_rules[from_layer]

            for to_file in imports:
                to_layer = self.layer_mapping.get(to_file)
                if not to_layer:
                    continue

                # 检查是否是禁止的依赖
                if to_layer in from_rule.forbidden_dependencies:
                    violations.append(
                        {
                            "from_file": from_file,
                            "to_file": to_file,
                            "from_layer": from_layer,
                            "to_layer": to_layer,
                            "violation_type": "forbidden_dependency",
                        }
                    )

                # 检查是否是允许的依赖
                elif to_layer not in from_rule.allowed_dependencies:
                    violations.append(
                        {
                            "from_file": from_file,
                            "to_file": to_file,
                            "from_layer": from_layer,
                            "to_layer": to_layer,
                            "violation_type": "unallowed_dependency",
                        }
                    )

        return violations

    def _check_circular_dependencies(self) -> List[List[str]]:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.import_graph.get(node, []):
                if dfs(neighbor, path.copy()):
                    return True

            rec_stack.remove(node)
            return False

        for node in self.import_graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def generate_dependency_graph(self) -> Dict[str, Any]:
        """生成依赖图报告"""
        return {
            "layers": {
                layer_name: {
                    "files": [
                        f for f, l in self.layer_mapping.items() if l == layer_name
                    ],
                    "allowed_dependencies": list(rule.allowed_dependencies),
                    "forbidden_dependencies": list(rule.forbidden_dependencies),
                }
                for layer_name, rule in self.layer_rules.items()
            },
            "import_graph": {
                file: list(imports) for file, imports in self.import_graph.items()
            },
            "layer_mapping": self.layer_mapping,
        }