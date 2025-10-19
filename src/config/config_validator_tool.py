"""配置验证工具"""

import sys
import argparse
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path

from .config_system import ConfigSystem
from .config_validator import ValidationResult, ConfigValidator
from .config_merger import ConfigMerger
from ..infrastructure.config_loader import YamlConfigLoader
from ..infrastructure.exceptions import ConfigurationError


class ConfigValidatorTool:
    """配置验证工具"""

    def __init__(self, config_path: str = "configs"):
        """初始化配置验证工具

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config_system: Optional[ConfigSystem] = None
        self._init_config_system()

    def _ensure_config_system(self) -> ConfigSystem:
        """确保配置系统已初始化

        Returns:
            配置系统实例

        Raises:
            RuntimeError: 如果配置系统未初始化
        """
        if self.config_system is None:
            raise RuntimeError("配置系统未初始化")
        return self.config_system

    def _init_config_system(self) -> None:
        """初始化配置系统"""
        try:
            config_loader = YamlConfigLoader(self.config_path)
            config_merger = ConfigMerger()
            config_validator = ConfigValidator()

            self.config_system = ConfigSystem(
                config_loader=config_loader,
                config_merger=config_merger,
                config_validator=config_validator,
                base_path=self.config_path,
            )
        except Exception as e:
            print(f"错误: 初始化配置系统失败: {e}")
            sys.exit(1)

    def validate_all(self) -> bool:
        """验证所有配置

        Returns:
            是否全部验证通过
        """
        print("开始验证所有配置...")
        print("=" * 50)

        all_valid = True

        # 验证全局配置
        if not self._validate_global_config():
            all_valid = False

        print()

        # 验证LLM配置
        if not self._validate_llm_configs():
            all_valid = False

        print()

        # 验证Agent配置
        if not self._validate_agent_configs():
            all_valid = False

        print()

        # 验证工具配置
        if not self._validate_tool_configs():
            all_valid = False

        print()
        print("=" * 50)
        if all_valid:
            print("✅ 所有配置验证通过")
        else:
            print("❌ 部分配置验证失败")

        return all_valid

    def _validate_global_config(self) -> bool:
        """验证全局配置

        Returns:
            是否验证通过
        """
        try:
            config_system = self._ensure_config_system()
            print("验证全局配置...")

            global_config = config_system.load_global_config()
            print(f"✅ 全局配置验证通过")
            print(f"   - 环境: {global_config.env}")
            print(f"   - 日志级别: {global_config.log_level}")
            print(f"   - 日志输出数量: {len(global_config.log_outputs)}")
            print(f"   - 敏感信息模式数量: {len(global_config.secret_patterns)}")
            return True
        except Exception as e:
            print(f"❌ 全局配置验证失败: {e}")
            return False

    def _validate_llm_configs(self) -> bool:
        """验证LLM配置

        Returns:
            是否全部验证通过
        """
        try:
            config_system = self._ensure_config_system()
            print("验证LLM配置...")

            llm_configs = config_system.list_configs("llms")

            if not llm_configs:
                print("⚠️  未找到LLM配置")
                return True

            all_valid = True

            for config_name in llm_configs:
                try:
                    llm_config = config_system.load_llm_config(config_name)
                    print(f"✅ LLM配置 '{config_name}' 验证通过")
                    print(f"   - 模型类型: {llm_config.model_type}")
                    print(f"   - 模型名称: {llm_config.model_name}")
                    if llm_config.group:
                        print(f"   - 所属组: {llm_config.group}")
                except Exception as e:
                    print(f"❌ LLM配置 '{config_name}' 验证失败: {e}")
                    all_valid = False

            return all_valid

        except Exception as e:
            print(f"❌ LLM配置验证失败: {e}")
            return False

    def _validate_agent_configs(self) -> bool:
        """验证Agent配置

        Returns:
            是否全部验证通过
        """
        try:
            config_system = self._ensure_config_system()
            print("验证Agent配置...")

            agent_configs = config_system.list_configs("agents")

            if not agent_configs:
                print("⚠️  未找到Agent配置")
                return True

            all_valid = True

            for config_name in agent_configs:
                try:
                    agent_config = config_system.load_agent_config(config_name)
                    print(f"✅ Agent配置 '{config_name}' 验证通过")
                    print(f"   - LLM: {agent_config.llm}")
                    print(f"   - 工具集数量: {len(agent_config.tool_sets)}")
                    print(f"   - 工具数量: {len(agent_config.tools)}")
                    if agent_config.group:
                        print(f"   - 所属组: {agent_config.group}")
                except Exception as e:
                    print(f"❌ Agent配置 '{config_name}' 验证失败: {e}")
                    all_valid = False

            return all_valid

        except Exception as e:
            print(f"❌ Agent配置验证失败: {e}")
            return False

    def _validate_tool_configs(self) -> bool:
        """验证工具配置

        Returns:
            是否全部验证通过
        """
        try:
            config_system = self._ensure_config_system()
            print("验证工具配置...")

            tool_configs = config_system.list_configs("tool-sets")

            if not tool_configs:
                print("⚠️  未找到工具配置")
                return True

            all_valid = True

            for config_name in tool_configs:
                try:
                    tool_config = config_system.load_tool_config(config_name)
                    print(f"✅ 工具配置 '{config_name}' 验证通过")
                    print(f"   - 工具数量: {len(tool_config.tools)}")
                    print(f"   - 超时时间: {tool_config.timeout}秒")
                    print(f"   - 最大重试次数: {tool_config.max_retries}")
                    if tool_config.group:
                        print(f"   - 所属组: {tool_config.group}")
                except Exception as e:
                    print(f"❌ 工具配置 '{config_name}' 验证失败: {e}")
                    all_valid = False

            return all_valid

        except Exception as e:
            print(f"❌ 工具配置验证失败: {e}")
            return False

    def validate_config(self, config_type: str, config_name: str) -> bool:
        """验证单个配置

        Args:
            config_type: 配置类型
            config_name: 配置名称

        Returns:
            是否验证通过
        """
        try:
            config_system = self._ensure_config_system()
            print(f"验证 {config_type} 配置 '{config_name}'...")

            if config_type == "global":
                config_system.load_global_config()
            elif config_type == "llm":
                config_system.load_llm_config(config_name)
            elif config_type == "agent":
                config_system.load_agent_config(config_name)
            elif config_type == "tool":
                config_system.load_tool_config(config_name)
            else:
                print(f"❌ 不支持的配置类型: {config_type}")
                return False

            print(f"✅ {config_type} 配置 '{config_name}' 验证通过")
            return True

        except Exception as e:
            print(f"❌ {config_type} 配置 '{config_name}' 验证失败: {e}")
            return False

    def list_configs(self, config_type: Optional[str] = None) -> None:
        """列出配置

        Args:
            config_type: 配置类型（可选）
        """
        try:
            config_system = self._ensure_config_system()

            if config_type:
                print(f"{config_type} 配置列表:")
                try:
                    configs = config_system.list_configs(config_type)
                    if configs:
                        for config_name in configs:
                            print(f"  - {config_name}")
                    else:
                        print(f"  未找到 {config_type} 配置")
                except Exception as e:
                    print(f"错误: 获取 {config_type} 配置列表失败: {e}")
            else:
                print("所有配置列表:")
                config_types = ["llms", "agents", "tool-sets"]

                for ct in config_types:
                    print(f"\n{ct}:")
                    try:
                        configs = config_system.list_configs(ct)
                        if configs:
                            for config_name in configs:
                                print(f"  - {config_name}")
                        else:
                            print(f"  未找到 {ct} 配置")
                    except Exception as e:
                        print(f"  错误: 获取 {ct} 配置列表失败: {e}")
        except Exception as e:
            print(f"错误: 配置系统未初始化: {e}")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="配置验证工具")
    parser.add_argument(
        "--config-path", default="configs", help="配置文件路径 (默认: configs)"
    )
    parser.add_argument(
        "--type", choices=["global", "llm", "agent", "tool"], help="配置类型"
    )
    parser.add_argument("--name", help="配置名称")
    parser.add_argument("--list", action="store_true", help="列出配置")
    parser.add_argument("--all", action="store_true", help="验证所有配置")

    args = parser.parse_args()

    # 检查配置路径是否存在
    if not Path(args.config_path).exists():
        print(f"错误: 配置路径不存在: {args.config_path}")
        sys.exit(1)

    # 创建验证工具
    validator = ConfigValidatorTool(args.config_path)

    # 执行操作
    if args.list:
        validator.list_configs(args.type)
    elif args.all:
        success = validator.validate_all()
        sys.exit(0 if success else 1)
    elif args.type and args.name:
        success = validator.validate_config(args.type, args.name)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
