"""TUI布局配置系统"""

import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict

from .layout import LayoutConfig, RegionConfig, LayoutRegion


@dataclass
class ThemeConfig:
    """主题配置"""
    name: str = "default"
    primary_color: str = "blue"
    secondary_color: str = "green"
    accent_color: str = "cyan"
    text_color: str = "white"
    border_style: str = "round"
    background_color: Optional[str] = None


@dataclass
class BehaviorConfig:
    """行为配置"""
    auto_save: bool = True
    auto_save_interval: int = 300  # 秒
    max_history: int = 1000
    scroll_speed: int = 5
    animation_enabled: bool = True
    refresh_rate: int = 10  # FPS


@dataclass
class TUIConfig:
    """TUI完整配置"""
    layout: LayoutConfig
    theme: ThemeConfig
    behavior: BehaviorConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "layout": self._layout_to_dict(),
            "theme": asdict(self.theme),
            "behavior": asdict(self.behavior)
        }
    
    def _layout_to_dict(self) -> Dict[str, Any]:
        """将布局配置转换为字典"""
        regions = {}
        for region, config in self.layout.regions.items():
            regions[region.value] = {
                "name": config.name,
                "min_size": config.min_size,
                "max_size": config.max_size,
                "ratio": config.ratio,
                "resizable": config.resizable,
                "visible": config.visible
            }
        
        return {
            "regions": regions,
            "min_terminal_width": self.layout.min_terminal_width,
            "min_terminal_height": self.layout.min_terminal_height,
            "responsive_breakpoints": self.layout.responsive_breakpoints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TUIConfig":
        """从字典创建配置"""
        layout_data = data.get("layout", {})
        theme_data = data.get("theme", {})
        behavior_data = data.get("behavior", {})
        
        # 重建布局配置
        regions = {}
        for region_name, region_data in layout_data.get("regions", {}).items():
            region_enum = LayoutRegion(region_name)
            regions[region_enum] = RegionConfig(
                name=region_data["name"],
                min_size=region_data["min_size"],
                max_size=region_data.get("max_size"),
                ratio=region_data["ratio"],
                resizable=region_data["resizable"],
                visible=region_data["visible"]
            )
        
        layout_config = LayoutConfig(
            regions=regions,
            min_terminal_width=layout_data.get("min_terminal_width", 80),
            min_terminal_height=layout_data.get("min_terminal_height", 24),
            responsive_breakpoints=layout_data.get("responsive_breakpoints")
        )
        
        # 重建主题配置
        theme_config = ThemeConfig(**theme_data)
        
        # 重建行为配置
        behavior_config = BehaviorConfig(**behavior_data)
        
        return cls(
            layout=layout_config,
            theme=theme_config,
            behavior=behavior_config
        )


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[Path] = None) -> None:
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or Path.home() / ".modular-agent" / "tui_config.yaml"
        self.config: Optional[TUIConfig] = None
        
        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> TUIConfig:
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.json':
                        data = json.load(f)
                    else:
                        data = yaml.safe_load(f)
                
                self.config = TUIConfig.from_dict(data)
                return self.config
                
            except Exception as e:
                print(f"警告: 加载配置文件失败，使用默认配置: {e}")
        
        # 使用默认配置
        self.config = self._create_default_config()
        self.save_config()
        return self.config
    
    def save_config(self) -> None:
        """保存配置"""
        if not self.config:
            return
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(self.config.to_dict(), f, default_flow_style=False, allow_unicode=True)
                    
        except Exception as e:
            print(f"警告: 保存配置文件失败: {e}")
    
    def get_config(self) -> TUIConfig:
        """获取当前配置"""
        if not self.config:
            self.config = self.load_config()
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """更新配置"""
        if not self.config:
            return
        
        # 更新主题配置
        if "theme" in kwargs:
            theme_data = kwargs["theme"]
            for key, value in theme_data.items():
                if hasattr(self.config.theme, key):
                    setattr(self.config.theme, key, value)
        
        # 更新行为配置
        if "behavior" in kwargs:
            behavior_data = kwargs["behavior"]
            for key, value in behavior_data.items():
                if hasattr(self.config.behavior, key):
                    setattr(self.config.behavior, key, value)
        
        # 更新布局配置
        if "layout" in kwargs:
            layout_data = kwargs["layout"]
            
            if "regions" in layout_data:
                for region_name, region_data in layout_data["regions"].items():
                    try:
                        region_enum = LayoutRegion(region_name)
                        if region_enum in self.config.layout.regions:
                            for key, value in region_data.items():
                                if hasattr(self.config.layout.regions[region_enum], key):
                                    setattr(self.config.layout.regions[region_enum], key, value)
                    except ValueError:
                        continue  # 忽略无效的区域名称
            
            # 更新其他布局属性
            for key, value in layout_data.items():
                if key != "regions" and hasattr(self.config.layout, key):
                    setattr(self.config.layout, key, value)
        
        # 保存更新后的配置
        self.save_config()
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.config = self._create_default_config()
        self.save_config()
    
    def _create_default_config(self) -> TUIConfig:
        """创建默认配置"""
        # 默认布局配置
        from .layout import LayoutManager
        layout_manager = LayoutManager()
        layout_config = layout_manager.config
        
        # 默认主题配置
        theme_config = ThemeConfig()
        
        # 默认行为配置
        behavior_config = BehaviorConfig()
        
        return TUIConfig(
            layout=layout_config,
            theme=theme_config,
            behavior=behavior_config
        )
    
    def export_config(self, export_path: Path, format: str = "yaml") -> None:
        """导出配置到文件
        
        Args:
            export_path: 导出路径
            format: 导出格式 ("yaml" 或 "json")
        """
        if not self.config:
            return
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                if format.lower() == "json":
                    json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(self.config.to_dict(), f, default_flow_style=False, allow_unicode=True)
                    
        except Exception as e:
            raise RuntimeError(f"导出配置失败: {e}")
    
    def import_config(self, import_path: Path) -> None:
        """从文件导入配置
        
        Args:
            import_path: 导入路径
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                if import_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            self.config = TUIConfig.from_dict(data)
            self.save_config()
            
        except Exception as e:
            raise RuntimeError(f"导入配置失败: {e}")


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_tui_config() -> TUIConfig:
    """获取TUI配置
    
    Returns:
        TUIConfig: TUI配置对象
    """
    return get_config_manager().get_config()