"""状态机配置迁移工具

提供从传统状态机配置到子工作流配置的迁移功能。
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import yaml
from src.interfaces.dependency_injection import get_logger
from pathlib import Path

from .config_adapter import StateMachineConfigAdapter
from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import (
    StateMachineConfig, StateDefinition, StateType, Transition
)

logger = get_logger(__name__)


class StateMachineMigrationTool:
    """状态机配置迁移工具
    
    负责将传统状态机配置迁移到新的子工作流格式。
    """
    
    def __init__(self):
        """初始化迁移工具"""
        self._config_adapter = StateMachineConfigAdapter()
        self._migration_history: List[Dict[str, Any]] = []
    
    def migrate_from_file(self, input_file: str, output_file: str, 
                        backup: bool = True) -> bool:
        """从文件迁移配置
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            backup: 是否创建备份
            
        Returns:
            bool: 迁移是否成功
        """
        try:
            # 读取原始配置
            original_config = self._read_config_file(input_file)
            if not original_config:
                logger.error(f"无法读取配置文件: {input_file}")
                return False
            
            # 执行迁移
            migrated_config = self.migrate_config(original_config, input_file)
            if not migrated_config:
                logger.error("配置迁移失败")
                return False
            
            # 创建备份
            if backup:
                backup_file = self._create_backup(input_file)
                if backup_file:
                    logger.info(f"创建备份文件: {backup_file}")
            
            # 写入迁移后的配置
            success = self._write_config_file(migrated_config, output_file)
            if success:
                logger.info(f"配置迁移成功: {input_file} -> {output_file}")
                self._record_migration(input_file, output_file, True)
                return True
            else:
                logger.error("写入迁移配置失败")
                self._record_migration(input_file, output_file, False, "写入失败")
                return False
                
        except Exception as e:
            logger.error(f"迁移配置失败: {e}")
            self._record_migration(input_file, output_file, False, str(e))
            return False
    
    def migrate_config(self, config_data: Dict[str, Any], 
                      source: str = "") -> Optional[Dict[str, Any]]:
        """迁移配置数据
        
        Args:
            config_data: 原始配置数据
            source: 配置来源标识
            
        Returns:
            Optional[Dict[str, Any]]: 迁移后的配置数据
        """
        try:
            # 解析状态机配置
            state_machine_config = self._parse_state_machine_config(config_data)
            if not state_machine_config:
                logger.error("解析状态机配置失败")
                return None
            
            # 转换为子工作流配置
            subworkflow_config = self._config_adapter.convert_to_subworkflow_config(state_machine_config)
            
            # 添加迁移信息
            migration_info = {
                "migrated_from": source,
                "migration_timestamp": self._get_timestamp(),
                "original_config_type": "state_machine",
                "new_config_type": "subworkflow",
                "migration_version": "1.0"
            }
            
            subworkflow_config["migration_info"] = migration_info
            
            return subworkflow_config
            
        except Exception as e:
            logger.error(f"迁移配置数据失败: {e}")
            return None
    
    def _parse_state_machine_config(self, config_data: Dict[str, Any]) -> Optional[StateMachineConfig]:
        """解析状态机配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            Optional[StateMachineConfig]: 状态机配置
        """
        try:
            # 检查是否是状态机配置
            if not self._is_state_machine_config(config_data):
                logger.error("不是有效的状态机配置")
                return None
            
            # 创建状态机配置
            config = StateMachineConfig(
                name=config_data.get('name', 'migrated_state_machine'),
                description=config_data.get('description', '迁移的状态机配置'),
                version=config_data.get('version', '1.0.0'),
                initial_state=config_data.get('initial_state', 'start')
            )
            
            # 解析状态定义
            states_data = config_data.get('states', {})
            for state_name, state_data in states_data.items():
                state_def = self._parse_state_definition(state_name, state_data)
                if state_def:
                    config.add_state(state_def)
            
            # 验证配置
            errors = config.validate()
            if errors:
                logger.warning(f"状态机配置验证警告: {errors}")
            
            return config
            
        except Exception as e:
            logger.error(f"解析状态机配置失败: {e}")
            return None
    
    def _is_state_machine_config(self, config_data: Dict[str, Any]) -> bool:
        """检查是否是状态机配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            bool: 是否是状态机配置
        """
        # 检查必需的字段
        required_fields = ['name', 'states']
        for field in required_fields:
            if field not in config_data:
                return False
        
        # 检查状态定义
        states = config_data.get('states', {})
        if not isinstance(states, dict) or not states:
            return False
        
        return True
    
    def _parse_state_definition(self, state_name: str, 
                               state_data: Dict[str, Any]) -> Optional[StateDefinition]:
        """解析状态定义
        
        Args:
            state_name: 状态名称
            state_data: 状态数据
            
        Returns:
            Optional[StateDefinition]: 状态定义
        """
        try:
            # 解析状态类型
            state_type_str = state_data.get('type', 'process')
            state_type = self._parse_state_type(state_type_str)
            
            # 创建状态定义
            state_def = StateDefinition(
                name=state_name,
                state_type=state_type,
                handler=state_data.get('handler'),
                description=state_data.get('description', ''),
                config=state_data.get('config', {})
            )
            
            # 解析状态转移
            transitions_data = state_data.get('transitions', [])
            for transition_data in transitions_data:
                transition = self._parse_transition(transition_data)
                if transition:
                    state_def.add_transition(transition)
            
            return state_def
            
        except Exception as e:
            logger.error(f"解析状态定义失败: {state_name}, 错误: {e}")
            return None
    
    def _parse_state_type(self, state_type_str: str) -> StateType:
        """解析状态类型
        
        Args:
            state_type_str: 状态类型字符串
            
        Returns:
            StateType: 状态类型枚举
        """
        type_mapping = {
            'start': StateType.START,
            'end': StateType.END,
            'process': StateType.PROCESS,
            'decision': StateType.DECISION,
            'parallel': StateType.PARALLEL,
            'conditional': StateType.CONDITIONAL
        }
        
        return type_mapping.get(state_type_str.lower(), StateType.PROCESS)
    
    def _parse_transition(self, transition_data: Dict[str, Any]) -> Optional[Transition]:
        """解析状态转移
        
        Args:
            transition_data: 转移数据
            
        Returns:
            Optional[Transition]: 状态转移
        """
        try:
            target_state = transition_data.get('target')
            if not target_state:
                logger.warning("转移缺少目标状态")
                return None
            
            return Transition(
                target_state=target_state,
                condition=transition_data.get('condition'),
                description=transition_data.get('description', '')
            )
            
        except Exception as e:
            logger.error(f"解析状态转移失败: {e}")
            return None
    
    def _read_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """读取配置文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    logger.error(f"不支持的文件格式: {path.suffix}")
                    return None
                    
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return None
    
    def _write_config_file(self, config_data: Dict[str, Any], 
                          file_path: str) -> bool:
        """写入配置文件
        
        Args:
            config_data: 配置数据
            file_path: 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_data, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                elif path.suffix.lower() == '.json':
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    # 默认使用YAML格式
                    yaml.dump(config_data, f, default_flow_style=False,
                             allow_unicode=True, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"写入配置文件失败: {e}")
            return False
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """创建备份文件
        
        Args:
            file_path: 原文件路径
            
        Returns:
            Optional[str]: 备份文件路径
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            timestamp = self._get_timestamp().replace(':', '-')
            backup_path = path.parent / f"{path.stem}_backup_{timestamp}{path.suffix}"
            
            import shutil
            shutil.copy2(path, backup_path)
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"创建备份文件失败: {e}")
            return None
    
    def _get_timestamp(self) -> str:
        """获取时间戳
        
        Returns:
            str: 时间戳字符串
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _record_migration(self, input_file: str, output_file: str, 
                        success: bool, error_msg: str = "") -> None:
        """记录迁移历史
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            success: 是否成功
            error_msg: 错误信息
        """
        record = {
            "timestamp": self._get_timestamp(),
            "input_file": input_file,
            "output_file": output_file,
            "success": success,
            "error_message": error_msg
        }
        
        self._migration_history.append(record)
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史
        
        Returns:
            List[Dict[str, Any]]: 迁移历史记录
        """
        return self._migration_history.copy()
    
    def validate_migration(self, original_config: Dict[str, Any], 
                         migrated_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证迁移结果
        
        Args:
            original_config: 原始配置
            migrated_config: 迁移后配置
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []
        
        try:
            # 检查基本结构
            if "states" not in migrated_config:
                errors.append("迁移后配置缺少states字段")
            
            if "transitions" not in migrated_config:
                errors.append("迁移后配置缺少transitions字段")
            
            # 检查状态数量
            original_states = original_config.get('states', {})
            migrated_states = migrated_config.get('states', {})
            
            if len(original_states) != len(migrated_states):
                errors.append(f"状态数量不匹配: 原始{len(original_states)}, 迁移后{len(migrated_states)}")
            
            # 检查初始状态
            original_initial = original_config.get('initial_state')
            migrated_initial = migrated_config.get('initial_state')
            
            if original_initial != migrated_initial:
                errors.append(f"初始状态不匹配: 原始{original_initial}, 迁移后{migrated_initial}")
            
            # 检查迁移信息
            if "migration_info" not in migrated_config:
                errors.append("缺少迁移信息")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"验证过程中出错: {e}"]
    
    def generate_migration_report(self) -> str:
        """生成迁移报告
        
        Returns:
            str: 迁移报告
        """
        if not self._migration_history:
            return "暂无迁移记录"
        
        report_lines = ["# 状态机配置迁移报告\n"]
        report_lines.append(f"生成时间: {self._get_timestamp()}\n")
        
        successful_migrations = [r for r in self._migration_history if r["success"]]
        failed_migrations = [r for r in self._migration_history if not r["success"]]
        
        report_lines.append(f"总迁移次数: {len(self._migration_history)}")
        report_lines.append(f"成功迁移: {len(successful_migrations)}")
        report_lines.append(f"失败迁移: {len(failed_migrations)}\n")
        
        if successful_migrations:
            report_lines.append("## 成功迁移\n")
            for record in successful_migrations:
                report_lines.append(f"- {record['timestamp']}: {record['input_file']} -> {record['output_file']}")
        
        if failed_migrations:
            report_lines.append("\n## 失败迁移\n")
            for record in failed_migrations:
                report_lines.append(f"- {record['timestamp']}: {record['input_file']} -> {record['output_file']}")
                report_lines.append(f"  错误: {record['error_message']}")
        
        return "\n".join(report_lines)