# Session恢复机制改进方案

## 问题背景

当前Session模块在恢复会话时存在严重的设计缺陷：`SessionManager.restore_session` 依赖首次创建时缓存的 `workflow_id`，但 `WorkflowManager` 的ID在进程重启后不会被恢复，导致会话恢复在常见部署场景中直接失败。

## 问题分析

### 当前实现的问题

```python
# src/application/sessions/manager.py:232-233
workflow_id = session_data["metadata"]["workflow_id"]
workflow = self.workflow_manager.create_workflow(workflow_id)
```

**问题**：
1. `workflow_id` 是进程内存中的临时标识
2. 进程重启后 `WorkflowManager` 的工作流缓存丢失
3. 会话恢复完全依赖易失的ID，缺乏容错机制

### 影响范围
- 服务器重启后所有会话无法恢复
- 容器化部署场景下会话持久化失效
- 影响用户体验和系统可靠性

## 改进方案

### 方案概述

采用**配置路径为主键 + 容错恢复**的双重保障机制，确保会话恢复的稳定性。

### 核心设计

#### 1. 会话元数据增强

在会话元数据中增加配置路径和版本信息：

```python
session_metadata = {
    "session_id": session_id,
    "workflow_config_path": workflow_config_path,  # 主要恢复依据
    "workflow_id": workflow_id,                    # 辅助信息
    "workflow_version": workflow_config.version,   # 版本控制
    "workflow_checksum": self._calculate_config_checksum(workflow_config_path),
    # ... 其他元数据
}
```

#### 2. 改进的恢复策略

```python
def restore_session(self, session_id: str) -> Tuple[Any, AgentState]:
    """改进的会话恢复方法"""
    session_data = self.session_store.get_session(session_id)
    if not session_data:
        raise ValueError(f"会话 {session_id} 不存在")
    
    metadata = session_data["metadata"]
    config_path = metadata["workflow_config_path"]
    
    # 策略1: 优先使用配置路径重新加载
    try:
        workflow_id = self.workflow_manager.load_workflow(config_path)
        workflow = self.workflow_manager.create_workflow(workflow_id)
        
        # 验证配置一致性
        if not self._validate_workflow_consistency(metadata, workflow_id):
            logger.warning(f"工作流配置已变更，使用新配置恢复会话 {session_id}")
            
    except Exception as e:
        # 策略2: 回退到原始workflow_id
        logger.warning(f"基于配置路径恢复失败，尝试使用原始workflow_id: {e}")
        try:
            original_workflow_id = metadata["workflow_id"]
            workflow = self.workflow_manager.create_workflow(original_workflow_id)
        except Exception:
            # 策略3: 最终回退 - 重新加载并更新元数据
            logger.error(f"会话恢复失败，尝试重新创建工作流: {e}")
            workflow_id = self.workflow_manager.load_workflow(config_path)
            workflow = self.workflow_manager.create_workflow(workflow_id)
            
            # 更新会话元数据
            self._update_session_workflow_info(session_id, workflow_id)
    
    # 恢复状态
    state = self._deserialize_state(session_data["state"])
    return workflow, state
```

#### 3. 配置一致性验证

```python
def _validate_workflow_consistency(self, metadata: Dict[str, Any], workflow_id: str) -> bool:
    """验证工作流配置一致性"""
    current_config = self.workflow_manager.get_workflow_config(workflow_id)
    if not current_config:
        return False
    
    # 检查版本
    if metadata.get("workflow_version") != current_config.version:
        return False
    
    # 检查配置校验和
    current_checksum = self._calculate_config_checksum(
        metadata["workflow_config_path"]
    )
    return metadata.get("workflow_checksum") == current_checksum

def _calculate_config_checksum(self, config_path: str) -> str:
    """计算配置文件校验和"""
    import hashlib
    with open(config_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
```

#### 4. 元数据更新机制

```python
def _update_session_workflow_info(self, session_id: str, new_workflow_id: str) -> None:
    """更新会话中的工作流信息"""
    session_data = self.session_store.get_session(session_id)
    if not session_data:
        return
    
    workflow_config = self.workflow_manager.get_workflow_config(new_workflow_id)
    session_data["metadata"].update({
        "workflow_id": new_workflow_id,
        "workflow_version": workflow_config.version if workflow_config else "unknown",
        "workflow_checksum": self._calculate_config_checksum(
            session_data["metadata"]["workflow_config_path"]
        ),
        "updated_at": datetime.now().isoformat(),
        "recovery_info": {
            "recovered_at": datetime.now().isoformat(),
            "original_workflow_id": session_data["metadata"].get("workflow_id"),
            "reason": "workflow_recovery"
        }
    })
    
    self.session_store.save_session(session_id, session_data)
```

## 实现细节

### 1. 会话创建时的改进

```python
def create_session(
    self,
    workflow_config_path: str,
    agent_config: Optional[Dict[str, Any]] = None,
    initial_state: Optional[AgentState] = None
) -> str:
    """改进的会话创建方法"""
    # 加载工作流配置
    workflow_id = self.workflow_manager.load_workflow(workflow_config_path)
    workflow = self.workflow_manager.create_workflow(workflow_id)
    workflow_config = self.workflow_manager.get_workflow_config(workflow_id)
    
    # 生成会话ID
    session_id = self._generate_session_id(workflow_config_path)
    
    # 准备增强的元数据
    session_metadata = {
        "session_id": session_id,
        "workflow_config_path": workflow_config_path,
        "workflow_id": workflow_id,
        "workflow_version": workflow_config.version if workflow_config else "1.0.0",
        "workflow_checksum": self._calculate_config_checksum(workflow_config_path),
        "agent_config": agent_config or {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "active"
    }
    
    # ... 其余创建逻辑保持不变
```

### 2. 错误处理和日志记录

```python
def restore_session(self, session_id: str) -> Tuple[Any, AgentState]:
    """带详细错误处理的会话恢复"""
    try:
        session_data = self.session_store.get_session(session_id)
        if not session_data:
            raise ValueError(f"会话 {session_id} 不存在")
        
        metadata = session_data["metadata"]
        config_path = metadata["workflow_config_path"]
        
        # 检查配置文件是否存在
        if not Path(config_path).exists():
            raise FileNotFoundError(f"工作流配置文件不存在: {config_path}")
        
        # 恢复逻辑...
        return self._restore_workflow_with_fallback(metadata, session_data)
        
    except Exception as e:
        logger.error(f"会话恢复失败: session_id={session_id}, error={e}")
        # 记录详细的恢复失败信息
        self._log_recovery_failure(session_id, e)
        raise
```

### 3. 恢复状态跟踪

```python
def _log_recovery_failure(self, session_id: str, error: Exception) -> None:
    """记录恢复失败信息"""
    recovery_log = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "recovery_attempts": self._get_recovery_attempts(session_id) + 1
    }
    
    # 保存恢复日志
    self._save_recovery_log(recovery_log)
```

## 测试策略

### 单元测试

```python
def test_session_recovery_with_missing_workflow():
    """测试工作流不存在时的恢复"""
    # 创建会话
    session_id = session_manager.create_session("configs/workflows/test.yaml")
    
    # 模拟工作流管理器重启（清空缓存）
    session_manager.workflow_manager._workflows.clear()
    
    # 恢复会话应该成功
    workflow, state = session_manager.restore_session(session_id)
    assert workflow is not None
    assert "recovery_info" in session_manager.get_session(session_id)["metadata"]

def test_session_recovery_with_config_change():
    """测试配置变更时的恢复"""
    # 创建会话
    session_id = session_manager.create_session("configs/workflows/test.yaml")
    
    # 修改配置文件
    with open("configs/workflows/test.yaml", "w") as f:
        f.write("# 修改后的配置")
    
    # 恢复会话应该使用新配置
    workflow, state = session_manager.restore_session(session_id)
    assert workflow is not None
```

### 集成测试

```python
def test_session_recovery_in_production_scenario():
    """测试生产环境场景下的会话恢复"""
    # 模拟完整的部署流程
    # 1. 创建会话并执行工作流
    # 2. 模拟服务器重启
    # 3. 验证会话恢复能力
    # 4. 验证状态一致性
```

## 部署和迁移

### 向后兼容性

- 现有会话数据自动迁移到新格式
- 提供迁移工具处理历史会话
- 保持API接口不变

### 监控和告警

- 记录恢复成功率指标
- 设置恢复失败告警
- 监控配置变更影响

## 预期效果

### 改进前
- 进程重启后会话恢复失败率：~100%
- 配置变更导致会话不可用
- 缺乏恢复机制

### 改进后  
- 进程重启后会话恢复成功率：>99%
- 配置变更自动适应
- 完整的错误处理和日志记录

## 实施计划

### 阶段1：核心恢复机制（1-2周）
1. 实现配置路径为主的恢复策略
2. 添加配置一致性验证
3. 实现错误回退机制

### 阶段2：增强功能（1周）
1. 添加配置校验和验证
2. 实现恢复日志记录
3. 完善错误处理

### 阶段3：测试和优化（1周）
1. 编写完整的测试用例
2. 性能优化和压力测试
3. 文档更新和部署

这个改进方案将显著提升系统的可靠性和用户体验，确保会话在各类部署场景下都能稳定恢复。