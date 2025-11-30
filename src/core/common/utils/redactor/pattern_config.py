"""脱敏模式配置管理系统"""

import json
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import os
from .redactor import RedactorPattern, PatternCategory
from .regex_optimizer import regex_optimizer, OptimizationLevel

try:
    import toml  # type: ignore
except ImportError:
    toml = None

# 尝试导入项目的配置加载器
try:
    from src.core.config.config_loader import ConfigLoader
    HAS_CONFIG_LOADER = True
except ImportError as e:
    # 记录导入失败的原因，便于调试
    HAS_CONFIG_LOADER = False
    _CONFIG_LOADER_IMPORT_ERROR = str(e)
else:
    _CONFIG_LOADER_IMPORT_ERROR = None


class ConfigFormat(Enum):
    """配置文件格式枚举"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class PatternConfig:
    """模式配置数据类"""
    name: str
    pattern: str
    category: str
    description: str
    priority: int = 0
    flags: int = 0
    replacement: Optional[str] = None
    enabled: bool = True
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_redactor_pattern(self) -> RedactorPattern:
        """转换为RedactorPattern对象

        Returns:
            RedactorPattern对象
        """
        return RedactorPattern(
            name=self.name,
            pattern=self.pattern,
            category=PatternCategory(self.category),
            description=self.description,
            priority=self.priority,
            flags=self.flags,
            replacement=self.replacement
        )


@dataclass
class RedactorConfig:
    """脱敏器配置数据类"""
    patterns: List[PatternConfig]
    default_replacement: str = "***"
    optimization_level: str = "basic"
    enable_unicode: bool = True
    enable_boundary_matching: bool = True
    cache_patterns: bool = True
    performance_monitoring: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            配置字典
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RedactorConfig':
        """从字典创建配置

        Args:
            data: 配置字典

        Returns:
            RedactorConfig对象
        """
        patterns = [PatternConfig(**p) for p in data.get('patterns', [])]
        
        return cls(
            patterns=patterns,
            default_replacement=data.get('default_replacement', '***'),
            optimization_level=data.get('optimization_level', 'basic'),
            enable_unicode=data.get('enable_unicode', True),
            enable_boundary_matching=data.get('enable_boundary_matching', True),
            cache_patterns=data.get('cache_patterns', True),
            performance_monitoring=data.get('performance_monitoring', False)
        )


class PatternConfigManager:
    """模式配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        # 配置目录优先级：
        # 1. 显式指定的 config_dir
        # 2. 项目根目录下的 configs/redactor（推荐）
        # 3. 代码内部的 configs 目录（仅作为备选）
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 使用当前工作目录作为项目根目录
            project_root = Path.cwd()
            project_config_dir = project_root / "configs" / "redactor"
            
            # 优先使用项目配置目录
            if project_config_dir.exists():
                self.config_dir = project_config_dir
            else:
                # 如果项目配置目录不存在，回退到内部配置目录
                self.config_dir = Path(__file__).parent / "configs"
        
        # 注意：不在这里创建目录，让配置加载逻辑决定是否需要创建
        
        self._configs: Dict[str, RedactorConfig] = {}
        self._load_default_configs()

    def _load_default_configs(self):
        """加载默认配置
        
        配置优先级：
        1. configs/redactor/default.yaml（项目配置）
        2. 硬编码默认配置（仅在配置文件不存在时使用）
        """
        # 尝试从项目配置目录加载配置
        if HAS_CONFIG_LOADER:
            try:
                config_loader = ConfigLoader(base_path=Path("configs"))  # type: ignore
                config_data = config_loader.load("redactor/default")
                self._configs['default'] = RedactorConfig.from_dict(config_data)
                # 成功加载项目配置，不需要保存到本地文件
                return
            except Exception:
                # 如果项目配置加载失败，继续尝试其他方式
                pass
        
        # 尝试直接从配置文件加载（不使用 ConfigLoader）
        config_file = self.config_dir / "default.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
                self._configs['default'] = RedactorConfig.from_dict(config_dict)
                return
            except Exception:
                # 配置文件存在但加载失败，继续使用硬编码配置
                pass
        
        # 最后的备选：使用硬编码的默认配置
        default_config = self._create_default_config()
        self._configs['default'] = default_config
        
        # 不再自动保存默认配置文件
        # 如果需要保存配置，应该显式调用 save_config() 方法

    def _create_default_config(self) -> RedactorConfig:
        """创建默认配置

        Returns:
            默认配置对象
        """
        default_patterns = [
            PatternConfig(
                name="email",
                pattern=r"(?<![a-zA-Z0-9._%+-\u4e00-\u9fff])[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?![a-zA-Z0-9.-\u4e00-\u9fff])",
                category="contact",
                description="邮箱地址",
                priority=90,
                flags=2,  # re.IGNORECASE
                tags=["email", "contact", "pii"]
            ),
            PatternConfig(
                name="phone_china",
                pattern=r"(?<!\d)1[3-9]\d{9}(?!\d)",
                category="contact",
                description="中国手机号",
                priority=90,
                tags=["phone", "contact", "china", "pii"]
            ),
            PatternConfig(
                name="id_card_china",
                pattern=r"(?<!\d)[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
                category="identity",
                description="中国身份证号",
                priority=95,
                tags=["id", "identity", "china", "pii"]
            ),
            PatternConfig(
                name="credit_card",
                pattern=r"(?<!\d)(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})(?!\d)",
                category="financial",
                description="信用卡号",
                priority=95,
                tags=["credit_card", "financial", "pii"]
            ),
            PatternConfig(
                name="openai_api_key",
                pattern=r"sk-[a-zA-Z0-9]{20,}",
                category="credentials",
                description="OpenAI API密钥",
                priority=100,
                tags=["api_key", "credentials", "openai"]
            ),
            PatternConfig(
                name="password_field",
                pattern=r'(?i)(password|passwd|pwd|密码)["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
                category="technical",
                description="密码字段",
                priority=100,
                tags=["password", "credentials", "security"]
            ),
        ]
        
        return RedactorConfig(
            patterns=default_patterns,
            default_replacement="***",
            optimization_level="basic",
            enable_unicode=True,
            enable_boundary_matching=True,
            cache_patterns=True,
            performance_monitoring=False
        )

    def save_config(self, name: str, config: RedactorConfig, format: ConfigFormat = ConfigFormat.YAML) -> str:
        """保存配置到文件

        Args:
            name: 配置名称
            config: 配置对象
            format: 文件格式

        Returns:
            配置文件路径
            
        Note:
            此方法会显式保存配置到文件。请注意：
            - 保存到项目配置目录会覆盖现有配置
            - 建议在开发环境中使用内部配置目录
            - 生产环境应该通过配置管理工具管理配置文件
        """
        filename = f"{name}.{format.value}"
        filepath = self.config_dir / filename
        
        # 检查是否在项目配置目录中
        if self.is_using_project_config() and name == "default":
            import warnings
            warnings.warn(
                f"正在保存默认配置到项目配置目录 ({self.config_dir})，"
                "这会覆盖现有的项目配置。请确认这是您想要的操作。",
                UserWarning
            )
        
        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True, parents=True)
        
        config_dict = config.to_dict()
        
        if format == ConfigFormat.JSON:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
        elif format == ConfigFormat.YAML:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        elif format == ConfigFormat.TOML:
            if toml is None:
                raise ImportError("TOML support requires 'toml' package. Install with: pip install toml")
            with open(filepath, 'w', encoding='utf-8') as f:
                toml.dump(config_dict, f)
        
        self._configs[name] = config
        return str(filepath)
    
    def is_using_project_config(self) -> bool:
        """检查是否使用项目配置目录
        
        Returns:
            True 如果使用项目配置目录 (configs/redactor/)
        """
        config_dir_str = str(self.config_dir).replace('\\', '/')  # 统一路径分隔符
        return config_dir_str.endswith("/configs/redactor") or "/configs/redactor" in config_dir_str
    
    def get_config_source_info(self) -> Dict[str, Any]:
        """获取配置源信息
        
        Returns:
            包含配置源信息的字典
        """
        return {
            "config_dir": str(self.config_dir),
            "is_project_config": self.is_using_project_config(),
            "config_file_exists": (self.config_dir / "default.yaml").exists(),
            "has_config_loader": HAS_CONFIG_LOADER,
            "config_loader_import_error": _CONFIG_LOADER_IMPORT_ERROR if not HAS_CONFIG_LOADER else None,
            "project_config_dir": str(Path(__file__).parent.parent.parent.parent.parent / "configs" / "redactor"),
            "internal_config_dir": str(Path(__file__).parent / "configs")
        }

    def load_config(self, name: str, format: Optional[ConfigFormat] = None) -> RedactorConfig:
        """从文件加载配置

        Args:
            name: 配置名称
            format: 文件格式（如果为None，则自动检测）

        Returns:
            配置对象
        """
        if name in self._configs:
            return self._configs[name]
        
        # 优先尝试从项目配置目录加载
        if HAS_CONFIG_LOADER and format is None:
            try:
                config_loader = ConfigLoader(base_path=Path("configs"))  # type: ignore
                config_data = config_loader.load(f"redactor/{name}")
                config = RedactorConfig.from_dict(config_data)
                self._configs[name] = config
                return config
            except Exception:
                # 如果项目配置加载失败，回退到本地文件
                pass
        
        # 从本地文件加载
        if format is None:
            for fmt in ConfigFormat:
                filepath = self.config_dir / f"{name}.{fmt.value}"
                if filepath.exists():
                    format = fmt
                    break
            else:
                raise FileNotFoundError(f"配置文件 '{name}' 不存在")
        
        filepath = self.config_dir / f"{name}.{format.value}"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            if format == ConfigFormat.JSON:
                config_dict = json.load(f)
            elif format == ConfigFormat.YAML:
                config_dict = yaml.safe_load(f)
            elif format == ConfigFormat.TOML:
                if toml is None:
                    raise ImportError("TOML support requires 'toml' package. Install with: pip install toml")
                config_dict = toml.load(f)
        
        config = RedactorConfig.from_dict(config_dict)
        self._configs[name] = config
        return config

    def get_config(self, name: str) -> RedactorConfig:
        """获取配置

        Args:
            name: 配置名称

        Returns:
            配置对象
        """
        if name not in self._configs:
            self.load_config(name)
        return self._configs[name]

    def list_configs(self) -> List[str]:
        """列出所有配置

        Returns:
            配置名称列表
        """
        configs = []
        for file in self.config_dir.iterdir():
            if file.is_file() and file.suffix in ['.json', '.yaml', '.yml', '.toml']:
                config_name = file.stem
                configs.append(config_name)
        return configs

    def delete_config(self, name: str) -> bool:
        """删除配置

        Args:
            name: 配置名称

        Returns:
            是否删除成功
        """
        # 删除文件
        deleted = False
        for fmt in ConfigFormat:
            filepath = self.config_dir / f"{name}.{fmt.value}"
            if filepath.exists():
                filepath.unlink()
                deleted = True
        
        # 从内存中删除
        if name in self._configs:
            del self._configs[name]
        
        return deleted

    def add_pattern_to_config(self, config_name: str, pattern_config: PatternConfig) -> bool:
        """向配置添加模式

        Args:
            config_name: 配置名称
            pattern_config: 模式配置

        Returns:
            是否添加成功
        """
        try:
            config = self.get_config(config_name)
            
            # 检查是否已存在同名模式
            for i, existing_pattern in enumerate(config.patterns):
                if existing_pattern.name == pattern_config.name:
                    config.patterns[i] = pattern_config
                    break
            else:
                config.patterns.append(pattern_config)
            
            # 重新排序
            config.patterns.sort(key=lambda p: p.priority, reverse=True)
            
            # 保存配置
            self.save_config(config_name, config)
            return True
        except Exception:
            return False

    def remove_pattern_from_config(self, config_name: str, pattern_name: str) -> bool:
        """从配置删除模式

        Args:
            config_name: 配置名称
            pattern_name: 模式名称

        Returns:
            是否删除成功
        """
        try:
            config = self.get_config(config_name)
            
            # 查找并删除模式
            for i, pattern in enumerate(config.patterns):
                if pattern.name == pattern_name:
                    del config.patterns[i]
                    self.save_config(config_name, config)
                    return True
            
            return False
        except Exception:
            return False

    def get_patterns_by_category(self, config_name: str, category: str) -> List[PatternConfig]:
        """根据分类获取模式

        Args:
            config_name: 配置名称
            category: 分类名称

        Returns:
            模式配置列表
        """
        config = self.get_config(config_name)
        return [p for p in config.patterns if p.category == category]

    def get_patterns_by_tag(self, config_name: str, tag: str) -> List[PatternConfig]:
        """根据标签获取模式

        Args:
            config_name: 配置名称
            tag: 标签

        Returns:
            模式配置列表
        """
        config = self.get_config(config_name)
        return [p for p in config.patterns if p.tags and tag in p.tags]

    def validate_config(self, config: RedactorConfig) -> List[str]:
        """验证配置

        Args:
            config: 配置对象

        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证模式
        pattern_names = set()
        for pattern in config.patterns:
            # 检查名称唯一性
            if pattern.name in pattern_names:
                errors.append(f"模式名称 '{pattern.name}' 重复")
            pattern_names.add(pattern.name)
            
            # 验证正则表达式
            is_valid, error_msg = regex_optimizer.validate_pattern(pattern.pattern)
            if not is_valid:
                errors.append(f"模式 '{pattern.name}' 的正则表达式无效: {error_msg}")
            
            # 验证分类
            try:
                PatternCategory(pattern.category)
            except ValueError:
                errors.append(f"模式 '{pattern.name}' 的分类 '{pattern.category}' 无效")
        
        # 验证优化级别
        try:
            OptimizationLevel(config.optimization_level)
        except ValueError:
            errors.append(f"优化级别 '{config.optimization_level}' 无效")
        
        return errors

    def export_config_template(self, filepath: str, format: ConfigFormat = ConfigFormat.YAML):
        """导出配置模板

        Args:
            filepath: 文件路径
            format: 文件格式
        """
        template_config = self._create_default_config()
        
        # 清空模式列表，只保留示例
        template_config.patterns = [
            PatternConfig(
                name="example_pattern",
                pattern=r"example_regex",
                category="contact",
                description="示例模式",
                priority=50,
                tags=["example"]
            )
        ]
        
        config_dict = template_config.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if format == ConfigFormat.JSON:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            elif format == ConfigFormat.YAML:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif format == ConfigFormat.TOML:
                if toml is None:
                    raise ImportError("TOML support requires 'toml' package. Install with: pip install toml")
                toml.dump(config_dict, f)

    def merge_configs(self, config_names: List[str], output_name: str) -> RedactorConfig:
        """合并多个配置

        Args:
            config_names: 要合并的配置名称列表
            output_name: 输出配置名称

        Returns:
            合并后的配置
        """
        merged_patterns = []
        seen_names = set()
        
        for config_name in config_names:
            config = self.get_config(config_name)
            
            for pattern in config.patterns:
                if pattern.name not in seen_names:
                    merged_patterns.append(pattern)
                    seen_names.add(pattern.name)
        
        # 按优先级排序
        merged_patterns.sort(key=lambda p: p.priority, reverse=True)
        
        merged_config = RedactorConfig(
            patterns=merged_patterns,
            default_replacement="***",
            optimization_level="basic",
            enable_unicode=True,
            enable_boundary_matching=True,
            cache_patterns=True,
            performance_monitoring=False
        )
        
        self.save_config(output_name, merged_config)
        return merged_config


# 全局配置管理器实例
pattern_config_manager = PatternConfigManager()