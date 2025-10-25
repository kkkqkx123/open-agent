# 配置文件备份机制实现方案

## 概述

为了提高session恢复的可靠性，本文档提出了一套完整的配置文件备份机制。该机制在创建会话时自动备份相关配置文件，当原始配置文件不存在时，可以从备份中恢复，确保会话能够正常恢复。

## 配置依赖关系分析

### 1. 工作流配置依赖

基于对现有配置文件的分析，工作流配置存在以下依赖关系：

```
workflows/react.yaml
├── 引用 LLM 配置: "openai-gpt4"
│   └── 依赖: llms/provider/openai/openai-gpt4.yaml
│       ├── 继承: llms/provider/openai/common.yaml
│       └── 引用: llms/tokens_counter/openai_gpt4.yaml
├── 引用工具集: "default"
│   └── 依赖: tool-sets/basic-tools.yaml
│       └── 引用工具: calculator.yaml, weather.yaml
└── 可能引用Agent配置
    └── 依赖: agents/default.yaml
```

### 2. 需要备份的配置类型

#### 2.1 必须备份的配置
- **工作流配置文件** (`configs/workflows/*.yaml`)
  - 主要配置文件，直接决定工作流结构
  - 包含节点配置、边连接、入口点等核心信息

#### 2.2 建议备份的配置
- **LLM配置文件** (`configs/llms/**/*.yaml`)【暂时不备份，因为模型可以中途更换，不影响工作流恢复】
  - 工作流中引用的LLM配置
  - 包含模型参数、API密钥、重试配置等
  - **备份理由**：LLM配置变更频繁，API密钥可能丢失

- **工具集配置文件** (`configs/tool-sets/*.yaml`)
  - 工作流中引用的工具集配置
  - 定义了可用工具列表和工具参数
  - **备份理由**：工具配置可能被修改或删除

- **工具配置文件** (`configs/tools/*.yaml`)
  - 具体工具的实现配置
  - 包含工具参数、函数路径等
  - **备份理由**：工具实现可能变更

#### 2.3 可选备份的配置
- **Agent配置文件** (`configs/agents/*.yaml`)
  - Agent的系统提示和行为配置
  - **备份理由**：相对稳定，但可能包含重要的提示词

- **全局配置文件** (`configs/global.yaml`)
  - 系统级配置
  - **备份理由**：变更频率低，但影响全局行为

## 实现方案

### 1. 配置备份管理器

```python
from pathlib import Path
from typing import Dict, List, Optional, Set
import shutil
import json
import yaml
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConfigBackupManager:
    """配置备份管理器"""
    
    def __init__(self, backup_root_dir: Path):
        """初始化备份管理器
        
        Args:
            backup_root_dir: 备份根目录
        """
        self.backup_root_dir = backup_root_dir
        self.backup_root_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置类型映射
        self.config_type_mapping = {
            'workflows': 'configs/workflows',
            'llms': 'configs/llms',
            'tool-sets': 'configs/tool-sets',
            'tools': 'configs/tools',
            'agents': 'configs/agents',
            'global': 'configs'
        }
    
    def backup_workflow_configs(self, workflow_config_path: str, session_id: str) -> Dict[str, str]:
        """备份工作流相关配置
        
        Args:
            workflow_config_path: 工作流配置文件路径
            session_id: 会话ID
            
        Returns:
            Dict[str, str]: 备份文件路径映射
        """
        backup_paths = {}
        
        try:
            # 创建会话专用备份目录
            session_backup_dir = self.backup_root_dir / session_id
            session_backup_dir.mkdir(exist_ok=True)
            
            # 1. 备份主要工作流配置
            workflow_backup_path = self._backup_single_file(
                workflow_config_path, 
                session_backup_dir / "workflows"
            )
            if workflow_backup_path:
                backup_paths['workflow'] = workflow_backup_path
            
            # 2. 分析并备份依赖配置
            dependency_paths = self._analyze_workflow_dependencies(workflow_config_path)
            for config_type, config_paths in dependency_paths.items():
                for config_path in config_paths:
                    backup_path = self._backup_single_file(
                        config_path,
                        session_backup_dir / config_type
                    )
                    if backup_path:
                        backup_key = f"{config_type}_{Path(config_path).stem}"
                        backup_paths[backup_key] = backup_path
            
            # 3. 生成备份清单
            self._generate_backup_manifest(session_backup_dir, backup_paths)
            
            logger.info(f"配置备份完成: {session_id}, 备份文件数: {len(backup_paths)}")
            return backup_paths
            
        except Exception as e:
            logger.error(f"配置备份失败: {session_id}, error: {e}")
            return {}
    
    def restore_from_backup(self, session_id: str, target_config_path: str) -> bool:
        """从备份恢复配置
        
        Args:
            session_id: 会话ID
            target_config_path: 目标配置路径
            
        Returns:
            bool: 是否成功恢复
        """
        try:
            session_backup_dir = self.backup_root_dir / session_id
            if not session_backup_dir.exists():
                logger.warning(f"会话备份目录不存在: {session_id}")
                return False
            
            # 读取备份清单
            manifest_path = session_backup_dir / "backup_manifest.json"
            if not manifest_path.exists():
                logger.warning(f"备份清单不存在: {manifest_path}")
                return False
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 查找目标配置的备份
            config_name = Path(target_config_path).stem
            backup_key = f"workflow_{config_name}"
            
            if backup_key not in manifest:
                logger.warning(f"配置文件备份不存在: {target_config_path}")
                return False
            
            backup_path = Path(manifest[backup_key])
            if not backup_path.exists():
                logger.warning(f"备份文件不存在: {backup_path}")
                return False
            
            # 确保目标目录存在
            target_dir = Path(target_config_path).parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制备份文件到目标位置
            shutil.copy2(backup_path, target_config_path)
            logger.info(f"配置恢复成功: {backup_path} -> {target_config_path}")
            return True
            
        except Exception as e:
            logger.error(f"配置恢复失败: {session_id}, {target_config_path}, error: {e}")
            return False
    
    def _backup_single_file(self, config_path: str, backup_dir: Path) -> Optional[str]:
        """备份单个配置文件
        
        Args:
            config_path: 配置文件路径
            backup_dir: 备份目录
            
        Returns:
            Optional[str]: 备份文件路径，失败时返回None
        """
        try:
            source_path = Path(config_path)
            if not source_path.exists():
                logger.warning(f"配置文件不存在: {config_path}")
                return None
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / source_path.name
            
            shutil.copy2(source_path, backup_path)
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"备份文件失败: {config_path}, error: {e}")
            return None
    
    def _analyze_workflow_dependencies(self, workflow_config_path: str) -> Dict[str, List[str]]:
        """分析工作流配置的依赖关系
        
        Args:
            workflow_config_path: 工作流配置文件路径
            
        Returns:
            Dict[str, List[str]]: 按类型分组的依赖配置路径
        """
        dependencies = {
            'llms': [],
            'tool-sets': [],
            'tools': [],
            'agents': []
        }
        
        try:
            with open(workflow_config_path, 'r', encoding='utf-8') as f:
                workflow_config = yaml.safe_load(f)
            
            # 分析LLM依赖
            llm_clients = self._extract_llm_clients(workflow_config)
            for llm_client in llm_clients:
                llm_config_path = f"configs/llms/provider/{self._get_provider_from_client(llm_client)}/{llm_client}.yaml"
                if Path(llm_config_path).exists():
                    dependencies['llms'].append(llm_config_path)
                
                # 添加token counter配置
                token_counter_path = f"configs/llms/tokens_counter/{llm_client}.yaml"
                if Path(token_counter_path).exists():
                    dependencies['llms'].append(token_counter_path)
            
            # 分析工具集依赖
            tool_sets = self._extract_tool_sets(workflow_config)
            for tool_set in tool_sets:
                tool_set_config_path = f"configs/tool-sets/{tool_set}.yaml"
                if Path(tool_set_config_path).exists():
                    dependencies['tool-sets'].append(tool_set_config_path)
                
                # 分析工具集中的具体工具
                tool_dependencies = self._analyze_tool_set_dependencies(tool_set_config_path)
                dependencies['tools'].extend(tool_dependencies)
            
            # 分析Agent依赖（如果存在）
            agent_configs = self._extract_agent_configs(workflow_config)
            for agent_config in agent_configs:
                agent_config_path = f"configs/agents/{agent_config}.yaml"
                if Path(agent_config_path).exists():
                    dependencies['agents'].append(agent_config_path)
            
        except Exception as e:
            logger.error(f"分析工作流依赖失败: {workflow_config_path}, error: {e}")
        
        return dependencies
    
    def _extract_llm_clients(self, workflow_config: Dict) -> List[str]:
        """从工作流配置中提取LLM客户端"""
        llm_clients = set()
        
        # 从节点配置中提取
        nodes = workflow_config.get('nodes', {})
        for node_config in nodes.values():
            llm_client = node_config.get('config', {}).get('llm_client')
            if llm_client:
                llm_clients.add(llm_client)
        
        return list(llm_clients)
    
    def _extract_tool_sets(self, workflow_config: Dict) -> List[str]:
        """从工作流配置中提取工具集"""
        tool_sets = set()
        
        # 从节点配置中提取
        nodes = workflow_config.get('nodes', {})
        for node_config in nodes.values():
            tool_manager = node_config.get('config', {}).get('tool_manager')
            if tool_manager and tool_manager != 'default':
                tool_sets.add(tool_manager)
        
        return list(tool_sets)
    
    def _extract_agent_configs(self, workflow_config: Dict) -> List[str]:
        """从工作流配置中提取Agent配置"""
        agent_configs = set()
        
        # 从additional_config中提取
        additional_config = workflow_config.get('additional_config', {})
        agent_config = additional_config.get('agent_config')
        if agent_config:
            agent_configs.add(agent_config)
        
        return list(agent_configs)
    
    def _get_provider_from_client(self, llm_client: str) -> str:
        """从LLM客户端名称推断提供商"""
        if llm_client.startswith('openai-'):
            return 'openai'
        elif llm_client.startswith('anthropic-'):
            return 'anthropic'
        elif llm_client.startswith('gemini-'):
            return 'gemini'
        else:
            return 'unknown'
    
    def _analyze_tool_set_dependencies(self, tool_set_config_path: str) -> List[str]:
        """分析工具集的依赖工具"""
        tool_dependencies = []
        
        try:
            with open(tool_set_config_path, 'r', encoding='utf-8') as f:
                tool_set_config = yaml.safe_load(f)
            
            tools = tool_set_config.get('tools', [])
            for tool in tools:
                tool_config_path = f"configs/tools/{tool}.yaml"
                if Path(tool_config_path).exists():
                    tool_dependencies.append(tool_config_path)
                    
        except Exception as e:
            logger.error(f"分析工具集依赖失败: {tool_set_config_path}, error: {e}")
        
        return tool_dependencies
    
    def _generate_backup_manifest(self, backup_dir: Path, backup_paths: Dict[str, str]) -> None:
        """生成备份清单
        
        Args:
            backup_dir: 备份目录
            backup_paths: 备份文件路径映射
        """
        manifest = {
            'session_id': backup_dir.name,
            'backup_time': datetime.now().isoformat(),
            'backup_files': backup_paths,
            'total_files': len(backup_paths)
        }
        
        manifest_path = backup_dir / "backup_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    def cleanup_old_backups(self, max_backup_age_days: int = 30) -> None:
        """清理旧备份
        
        Args:
            max_backup_age_days: 最大备份保留天数
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_backup_age_days * 24 * 3600)
            
            for session_dir in self.backup_root_dir.iterdir():
                if session_dir.is_dir():
                    manifest_path = session_dir / "backup_manifest.json"
                    if manifest_path.exists():
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        backup_time = datetime.fromisoformat(manifest['backup_time']).timestamp()
                        if backup_time < cutoff_time:
                            shutil.rmtree(session_dir)
                            logger.info(f"清理旧备份: {session_dir.name}")
                            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
```

### 2. 集成到SessionManager

```python
# 在SessionManager中添加配置备份功能

class SessionManager(ISessionManager):
    def __init__(
        self,
        workflow_manager: IWorkflowManager,
        session_store: ISessionStore,
        git_manager: Optional[IGitManager] = None,
        storage_path: Optional[Path] = None,
        enable_config_backup: bool = True
    ) -> None:
        """初始化会话管理器"""
        # ... 现有初始化代码 ...
        
        # 添加配置备份管理器
        self.enable_config_backup = enable_config_backup
        if self.enable_config_backup:
            backup_dir = self.storage_path / "config_backups"
            self.config_backup_manager = ConfigBackupManager(backup_dir)
        else:
            self.config_backup_manager = None
    
    def create_session(
        self,
        workflow_config_path: str,
        agent_config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[AgentState] = None
    ) -> str:
        """创建新会话"""
        # ... 现有创建逻辑 ...
        
        # 添加配置备份
        if self.config_backup_manager:
            backup_paths = self.config_backup_manager.backup_workflow_configs(
                workflow_config_path, session_id
            )
            if backup_paths:
                session_metadata["config_backup_paths"] = backup_paths
                # 重新保存会话数据以包含备份路径
                self.session_store.save_session(session_id, session_data)
        
        return session_id
    
    def _restore_workflow_with_fallback(self, metadata: Dict[str, Any], session_data: Dict[str, Any]) -> Tuple[Any, AgentState]:
        """带回退机制的工作流恢复"""
        session_id = metadata.get("session_id", "unknown")
        config_path = metadata["workflow_config_path"]
        
        # 策略1: 优先使用配置路径重新加载
        try:
            # 检查配置文件是否存在
            if not Path(config_path).exists():
                # 尝试从备份恢复
                if self.config_backup_manager and self._try_restore_from_backup(session_id, config_path):
                    logger.info(f"从备份恢复配置文件: {config_path}")
                else:
                    raise FileNotFoundError(f"工作流配置文件不存在: {config_path}")
            
            workflow_id = self.workflow_manager.load_workflow(config_path)
            workflow = self.workflow_manager.create_workflow(workflow_id)
            
            # 验证配置一致性
            if not self._validate_workflow_consistency(metadata, workflow_id):
                logger.warning(f"工作流配置已变更，使用新配置恢复会话 {session_id}")
                
            # 恢复状态
            state = self._deserialize_state(session_data["state"])
            
            # 重置恢复尝试计数
            if session_id in self._recovery_attempts:
                del self._recovery_attempts[session_id]
                
            return workflow, state
            
        except Exception as e:
            # ... 现有回退逻辑 ...
    
    def _try_restore_from_backup(self, session_id: str, config_path: str) -> bool:
        """尝试从备份恢复配置文件
        
        Args:
            session_id: 会话ID
            config_path: 配置文件路径
            
        Returns:
            bool: 是否成功恢复
        """
        if not self.config_backup_manager:
            return False
        
        return self.config_backup_manager.restore_from_backup(session_id, config_path)
```

### 3. 配置备份策略

#### 3.1 备份时机
- **会话创建时**：自动备份所有相关配置
- **配置更新时**：可选择增量备份
- **定期维护**：清理过期备份

#### 3.2 备份范围策略
```python
# 可配置的备份策略
BACKUP_STRATEGIES = {
    'minimal': {
        'description': '最小备份策略',
        'backup_types': ['workflows'],
        'exclude_patterns': []
    },
    'standard': {
        'description': '标准备份策略',
        'backup_types': ['workflows', 'llms', 'tool-sets'],
        'exclude_patterns': ['*_test.yaml', '*_dev.yaml']
    },
    'comprehensive': {
        'description': '全面备份策略',
        'backup_types': ['workflows', 'llms', 'tool-sets', 'tools', 'agents', 'global'],
        'exclude_patterns': []
    }
}
```

#### 3.3 存储优化
- **去重机制**：相同配置文件只保存一份，使用引用计数
- **压缩存储**：对大型配置文件进行压缩
- **版本管理**：保留配置文件的多个版本

## 使用示例

### 1. 基本使用

```python
# 创建会话管理器（启用配置备份）
session_manager = SessionManager(
    workflow_manager=workflow_manager,
    session_store=session_store,
    storage_path=Path("./sessions"),
    enable_config_backup=True
)

# 创建会话（自动备份配置）
session_id = session_manager.create_session("configs/workflows/react.yaml")

# 恢复会话（自动从备份恢复缺失的配置）
workflow, state = session_manager.restore_session(session_id)
```

### 2. 高级配置

```python
# 自定义备份策略
config_backup_manager = ConfigBackupManager(
    backup_root_dir=Path("./custom_backups")
)

# 手动备份配置
backup_paths = config_backup_manager.backup_workflow_configs(
    "configs/workflows/react.yaml",
    "session_123"
)

# 手动恢复配置
success = config_backup_manager.restore_from_backup(
    "session_123",
    "configs/workflows/react.yaml"
)
```

## 监控和维护

### 1. 备份状态监控

```python
def get_backup_statistics(backup_manager: ConfigBackupManager) -> Dict[str, Any]:
    """获取备份统计信息"""
    stats = {
        'total_sessions': 0,
        'total_backups': 0,
        'storage_size_mb': 0,
        'oldest_backup': None,
        'newest_backup': None
    }
    
    for session_dir in backup_manager.backup_root_dir.iterdir():
        if session_dir.is_dir():
            stats['total_sessions'] += 1
            
            manifest_path = session_dir / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                stats['total_backups'] += manifest['total_files']
                
                # 计算存储大小
                for backup_path in manifest['backup_files'].values():
                    if Path(backup_path).exists():
                        stats['storage_size_mb'] += Path(backup_path).stat().st_size / (1024 * 1024)
    
    return stats
```

### 2. 定期维护任务

```python
def schedule_backup_maintenance():
    """定期备份维护任务"""
    backup_manager = ConfigBackupManager(Path("./sessions/config_backups"))
    
    # 清理30天前的备份
    backup_manager.cleanup_old_backups(max_backup_age_days=30)
    
    # 生成备份报告
    stats = get_backup_statistics(backup_manager)
    logger.info(f"备份统计: {stats}")
```

## 总结

配置文件备份机制通过以下方式提高了session恢复的可靠性：

1. **自动备份**：在会话创建时自动备份所有相关配置
2. **智能恢复**：当原始配置缺失时自动从备份恢复
3. **依赖分析**：自动分析并备份配置文件的依赖关系
4. **存储优化**：通过去重和压缩优化存储空间
5. **监控维护**：提供备份状态监控和定期清理功能

该机制确保了即使在配置文件被删除、修改或损坏的情况下，会话仍能够正常恢复，显著提高了系统的可靠性和用户体验。