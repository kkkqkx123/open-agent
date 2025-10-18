"""架构检查器单元测试"""

import ast
import pytest
import tempfile
from pathlib import Path

from src.infrastructure.architecture import ArchitectureChecker, LayerRule
from src.infrastructure.types import CheckResult


class TestArchitectureChecker:
    """架构检查器测试"""
    
    def test_define_layer_rules(self) -> None:
        """测试分层规则定义"""
        checker = ArchitectureChecker()
        rules = checker.layer_rules
        
        # 检查所有层级都已定义
        assert "domain" in rules
        assert "infrastructure" in rules
        assert "application" in rules
        assert "presentation" in rules
        
        # 检查领域层规则
        domain_rule = rules["domain"]
        assert len(domain_rule.allowed_dependencies) == 0
        assert "infrastructure" in domain_rule.forbidden_dependencies
        assert "application" in domain_rule.forbidden_dependencies
        assert "presentation" in domain_rule.forbidden_dependencies
        
        # 检查基础设施层规则
        infra_rule = rules["infrastructure"]
        assert "domain" in infra_rule.allowed_dependencies
        assert "application" in infra_rule.forbidden_dependencies
        assert "presentation" in infra_rule.forbidden_dependencies
        
        # 检查应用层规则
        app_rule = rules["application"]
        assert "domain" in app_rule.allowed_dependencies
        assert "infrastructure" in app_rule.allowed_dependencies
        assert "presentation" in app_rule.forbidden_dependencies
        
        # 检查表现层规则
        pres_rule = rules["presentation"]
        assert "domain" in pres_rule.allowed_dependencies
        assert "infrastructure" in pres_rule.allowed_dependencies
        assert "application" in pres_rule.allowed_dependencies
        assert len(pres_rule.forbidden_dependencies) == 0
    
    def test_match_path_pattern(self) -> None:
        """测试路径模式匹配"""
        checker = ArchitectureChecker()
        
        # 测试精确匹配
        path = Path("src/domain/entities.py")
        assert checker._match_path_pattern(path, "src/domain/*")
        assert not checker._match_path_pattern(path, "src/infrastructure/*")
        
        # 测试通配符匹配
        path = Path("src/domain/repository.py")
        assert checker._match_path_pattern(path, "src/domain/*")
        
        # 测试路径长度不匹配
        path = Path("src/domain/subdir/file.py")
        assert not checker._match_path_pattern(path, "src/domain/*")
    
    def test_determine_layer(self) -> None:
        """测试确定文件所属层级"""
        checker = ArchitectureChecker()
        
        # 测试各层级文件
        assert checker._determine_layer("src/domain/entities.py") == "domain"
        assert checker._determine_layer("src/infrastructure/repository.py") == "infrastructure"
        assert checker._determine_layer("src/application/service.py") == "application"
        assert checker._determine_layer("src/presentation/cli.py") == "presentation"
        
        # 测试不匹配的文件
        assert checker._determine_layer("src/unknown/file.py") is None
        assert checker._determine_layer("other/path/file.py") is None
    
    def test_extract_imports(self) -> None:
        """测试提取导入语句"""
        checker = ArchitectureChecker()
        current_file = Path("src/domain/entities.py")
        
        # 测试import语句
        code = """
import os
import sys
from typing import List, Dict
from .models import Entity
from src.infrastructure.repository import Repository
"""
        tree = ast.parse(code)
        imports = checker._extract_imports(tree, current_file)
        
        # 应该过滤掉外部库导入，只保留项目内部导入
        assert len(imports) >= 1
        assert any("models.py" in imp for imp in imports)
        assert any("repository.py" in imp for imp in imports)
    
    def test_resolve_import_path(self) -> None:
        """测试解析导入路径"""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "src"
            src_path.mkdir()
            
            # 创建测试文件结构
            domain_path = src_path / "domain"
            domain_path.mkdir()
            (domain_path / "__init__.py").touch()
            (domain_path / "entities.py").touch()
            
            infra_path = src_path / "infrastructure"
            infra_path.mkdir()
            (infra_path / "__init__.py").touch()
            (infra_path / "repository.py").touch()
            
            checker = ArchitectureChecker(str(src_path))
            current_file = src_path / "domain" / "test.py"
            
            # 测试相对导入
            import_path = checker._resolve_import_path(".models", current_file)
            assert import_path is not None
            assert "models.py" in import_path
            
            # 测试绝对导入
            import_path = checker._resolve_import_path("src.infrastructure.repository", current_file)
            assert import_path is not None
            assert "repository.py" in import_path
            
            # 测试外部库导入
            import_path = checker._resolve_import_path("os", current_file)
            assert import_path is None
    
    def test_check_layer_violations(self) -> None:
        """测试层级违规检查"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件结构
            self._create_test_files(temp_dir)
            
            checker = ArchitectureChecker(str(Path(temp_dir) / "src"))
            checker._build_import_graph()
            checker._map_files_to_layers()
            
            violations = checker._check_layer_violations()
            
            # 应该检测到违规
            assert len(violations) > 0
            
            # 检查违规详情
            violation = violations[0]
            assert "from_file" in violation
            assert "to_file" in violation
            assert "from_layer" in violation
            assert "to_layer" in violation
            assert "violation_type" in violation
    
    def test_check_circular_dependencies(self) -> None:
        """测试循环依赖检查"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建循环依赖文件
            self._create_circular_dependency_files(temp_dir)
            
            checker = ArchitectureChecker(str(Path(temp_dir) / "src"))
            checker._build_import_graph()
            
            cycles = checker._check_circular_dependencies()
            
            # 应该检测到循环依赖
            assert len(cycles) > 0
            
            # 检查循环路径
            cycle = cycles[0]
            assert isinstance(cycle, list)
            assert len(cycle) >= 2
    
    def test_check_architecture(self) -> None:
        """测试完整架构检查"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建合规的文件结构
            self._create_compliant_files(temp_dir)
            
            checker = ArchitectureChecker(str(Path(temp_dir) / "src"))
            results = checker.check_architecture()
            
            # 应该有层级检查和循环依赖检查的结果
            assert len(results) >= 2
            
            # 检查结果格式
            for result in results:
                assert isinstance(result, CheckResult)
                assert result.component in ["architecture_layer", "circular_dependency"]
    
    def test_generate_dependency_graph(self) -> None:
        """测试生成依赖图报告"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件结构
            self._create_test_files(temp_dir)
            
            checker = ArchitectureChecker(str(Path(temp_dir) / "src"))
            checker._build_import_graph()
            checker._map_files_to_layers()
            
            graph = checker.generate_dependency_graph()
            
            # 检查图结构
            assert "layers" in graph
            assert "import_graph" in graph
            assert "layer_mapping" in graph
            
            # 检查层级信息
            layers = graph["layers"]
            assert "domain" in layers
            assert "infrastructure" in layers
            assert "application" in layers
            assert "presentation" in layers
            
            # 检查层级详情
            for layer_name, layer_info in layers.items():
                assert "files" in layer_info
                assert "allowed_dependencies" in layer_info
                assert "forbidden_dependencies" in layer_info
    
    def _create_test_files(self, temp_dir: str) -> None:
        """创建测试文件"""
        src_path = Path(temp_dir) / "src"
        
        # 创建目录结构
        for layer in ["domain", "infrastructure", "application", "presentation"]:
            (src_path / layer).mkdir(parents=True)
            (src_path / layer / "__init__.py").touch()
        
        # 创建领域层文件
        (src_path / "domain" / "entities.py").write_text("""
from dataclasses import dataclass

@dataclass
class Entity:
    id: str
    name: str
""")

        # 创建基础设施层文件（违规：依赖应用层）
        (src_path / "infrastructure" / "repository.py").write_text("""
from src.domain.entities import Entity
from src.application.service import ApplicationService  # 违规

class Repository:
    def get(self, id: str) -> Entity:
        pass
""")

        # 创建应用层文件
        (src_path / "application" / "service.py").write_text("""
from src.domain.entities import Entity
from src.infrastructure.repository import Repository

class ApplicationService:
    def __init__(self, repository: Repository):
        self.repository = repository
""")

        # 创建表现层文件
        (src_path / "presentation" / "cli.py").write_text("""
from src.application.service import ApplicationService

class CLI:
    def __init__(self, service: ApplicationService):
        self.service = service
""")

    def _create_circular_dependency_files(self, temp_dir: str) -> None:
        """创建循环依赖文件"""
        src_path = Path(temp_dir) / "src"
        src_path.mkdir()
        
        # 创建循环依赖的模块
        (src_path / "module_a.py").write_text("""
from src.module_b import ModuleB

class ModuleA:
    def __init__(self):
        self.b = ModuleB()
""")

        (src_path / "module_b.py").write_text("""
from src.module_a import ModuleA

class ModuleB:
    def __init__(self):
        self.a = ModuleA()
""")

    def _create_compliant_files(self, temp_dir: str) -> None:
        """创建合规的文件结构"""
        src_path = Path(temp_dir) / "src"
        
        # 创建目录结构
        for layer in ["domain", "infrastructure", "application", "presentation"]:
            (src_path / layer).mkdir(parents=True)
            (src_path / layer / "__init__.py").touch()
        
        # 创建领域层文件（无依赖）
        (src_path / "domain" / "entities.py").write_text("""
from dataclasses import dataclass

@dataclass
class Entity:
    id: str
    name: str
""")

        # 创建基础设施层文件（依赖领域层）
        (src_path / "infrastructure" / "repository.py").write_text("""
from src.domain.entities import Entity

class Repository:
    def get(self, id: str) -> Entity:
        pass
""")

        # 创建应用层文件（依赖领域层和基础设施层）
        (src_path / "application" / "service.py").write_text("""
from src.domain.entities import Entity
from src.infrastructure.repository import Repository

class ApplicationService:
    def __init__(self, repository: Repository):
        self.repository = repository
""")

        # 创建表现层文件（依赖应用层）
        (src_path / "presentation" / "cli.py").write_text("""
from src.application.service import ApplicationService

class CLI:
    def __init__(self, service: ApplicationService):
        self.service = service
""")