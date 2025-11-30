# Thread检查点子模块架构图

## 1. 整体架构图

```mermaid
graph TB
    subgraph "Sessions层"
        S1[Session Manager]
    end
    
    subgraph "Threads层"
        T1[Thread实体]
        T2[Thread服务层]
        
        subgraph "Thread检查点子模块"
            CM[ThreadCheckpointManager]
            
            subgraph "存储层"
                LG[LangGraph适配器]
                MEM[内存存储]
                FILE[文件存储]
            end
            
            subgraph "策略层"
                AS[自动保存策略]
                CL[清理策略]
                CP[压缩策略]
            end
            
            subgraph "操作层"
                CO[创建操作]
                RO[恢复操作]
                LO[列表操作]
                DO[删除操作]
            end
            
            subgraph "快照管理"
                SM[快照管理器]
                SO[快照操作]
            end
            
            subgraph "分支管理"
                BM[分支管理器]
                BO[分支操作]
            end
        end
    end
    
    subgraph "Workflow层"
        W1[Workflow执行协调器]
        W2[LangGraph适配器]
    end
    
    subgraph "LangGraph层"
        LG1[LangGraph Checkpoint]
        LG2[LangGraph Storage]
    end
    
    S1 --> T2
    T2 --> T1
    T1 --> CM
    CM --> LG
    CM --> MEM
    CM --> FILE
    CM --> AS
    CM --> CL
    CM --> CP
    CM --> CO
    CM --> RO
    CM --> LO
    CM --> DO
    CM --> SM
    CM --> BM
    SM --> SO
    BM --> BO
    W1 --> W2
    W2 --> CM
    LG --> LG1
    LG1 --> LG2
```

## 2. 检查点子模块详细架构

```mermaid
graph LR
    subgraph "Thread检查点子模块"
        subgraph "管理器层"
            MGR[ThreadCheckpointManager]
        end
        
        subgraph "存储抽象层"
            STORAGE[IThreadCheckpointStorage]
        end
        
        subgraph "存储实现层"
            LG_ADAPTER[LangGraphCheckpointAdapter]
            MEM_STORAGE[MemoryCheckpointStorage]
            FILE_STORAGE[FileCheckpointStorage]
        end
        
        subgraph "策略层"
            POLICY[IThreadCheckpointPolicy]
            AUTO_POLICY[AutoSavePolicy]
            CLEANUP_POLICY[CleanupPolicy]
            COMPRESS_POLICY[CompressionPolicy]
        end
        
        subgraph "操作层"
            OPERATIONS[IThreadCheckpointOperations]
            CREATE_OP[CreateCheckpoint]
            RESTORE_OP[RestoreCheckpoint]
            LIST_OP[ListCheckpoints]
            DELETE_OP[DeleteCheckpoint]
        end
        
        subgraph "快照管理"
            SNAPSHOT_MGR[ThreadSnapshotManager]
            SNAPSHOT_OPS[SnapshotOperations]
        end
        
        subgraph "分支管理"
            BRANCH_MGR[ThreadBranchManager]
            BRANCH_OPS[BranchOperations]
        end
    end
    
    MGR --> STORAGE
    MGR --> POLICY
    MGR --> OPERATIONS
    MGR --> SNAPSHOT_MGR
    MGR --> BRANCH_MGR
    
    STORAGE --> LG_ADAPTER
    STORAGE --> MEM_STORAGE
    STORAGE --> FILE_STORAGE
    
    POLICY --> AUTO_POLICY
    POLICY --> CLEANUP_POLICY
    POLICY --> COMPRESS_POLICY
    
    OPERATIONS --> CREATE_OP
    OPERATIONS --> RESTORE_OP
    OPERATIONS --> LIST_OP
    OPERATIONS --> DELETE_OP
    
    SNAPSHOT_MGR --> SNAPSHOT_OPS
    BRANCH_MGR --> BRANCH_OPS
```

## 3. 数据流图

```mermaid
sequenceDiagram
    participant WS as Workflow服务
    participant TS as Thread服务
    participant TC as ThreadCheckpointManager
    participant LG as LangGraph适配器
    participant LG_DB as LangGraph存储
    
    WS->>TS: 执行工作流
    TS->>TC: 创建检查点
    TC->>LG: 保存到LangGraph
    LG->>LG_DB: 持久化存储
    LG_DB-->>LG: 返回检查点ID
    LG-->>TC: 返回检查点ID
    TC-->>TS: 返回检查点ID
    TS-->>WS: 继续执行
    
    WS->>TS: 恢复状态
    TS->>TC: 从检查点恢复
    TC->>LG: 从LangGraph加载
    LG->>LG_DB: 查询检查点
    LG_DB-->>LG: 返回检查点数据
    LG-->>TC: 返回状态数据
    TC-->>TS: 返回状态数据
    TS-->>WS: 恢复执行
```

## 4. 组件交互图

```mermaid
graph TB
    subgraph "外部接口"
        API[Thread API]
        WF[Workflow API]
    end
    
    subgraph "服务层"
        TS[ThreadService]
        WS[WorkflowService]
    end
    
    subgraph "Thread检查点子模块"
        MGR[ThreadCheckpointManager]
        
        subgraph "存储层"
            STORAGE[Storage Layer]
            LANGGRAPH[LangGraph Storage]
            MEMORY[Memory Storage]
            FILE[File Storage]
        end
        
        subgraph "功能模块"
            SNAPSHOT[Snapshot Manager]
            BRANCH[Branch Manager]
            POLICY[Policy Engine]
        end
    end
    
    subgraph "底层存储"
        LG_DB[LangGraph DB]
        FS[File System]
        RAM[Memory]
    end
    
    API --> TS
    WF --> WS
    TS --> MGR
    WS --> MGR
    MGR --> STORAGE
    MGR --> SNAPSHOT
    MGR --> BRANCH
    MGR --> POLICY
    STORAGE --> LANGGRAPH
    STORAGE --> MEMORY
    STORAGE --> FILE
    LANGGRAPH --> LG_DB
    FILE --> FS
    MEMORY --> RAM
```

## 5. 状态转换图

```mermaid
stateDiagram-v2
    [*] --> Created: 创建Thread
    Created --> Running: 开始执行
    Running --> Checkpointed: 创建检查点
    Checkpointed --> Running: 继续执行
    Running --> Paused: 暂停执行
    Paused --> Restored: 从检查点恢复
    Restored --> Running: 继续执行
    Running --> Completed: 执行完成
    Paused --> Completed: 直接完成
    Completed --> [*]: 销毁Thread
    
    Running --> Snapshotted: 创建快照
    Snapshotted --> Running: 继续执行
    Running --> Branched: 创建分支
    Branched --> Running: 继续执行
    
    state Checkpointed {
        [*] --> Auto: 自动检查点
        [*] --> Manual: 手动检查点
        [*] --> Snapshot: 快照检查点
    }
```

## 6. 部署架构图

```mermaid
graph TB
    subgraph "应用层"
        APP[应用程序]
        API_GATEWAY[API网关]
    end
    
    subgraph "服务层"
        THREAD_SVC[Thread服务]
        WORKFLOW_SVC[Workflow服务]
        CHECKPOINT_SVC[检查点服务]
    end
    
    subgraph "核心层"
        THREAD_CORE[Thread核心]
        CHECKPOINT_CORE[检查点核心]
        LANGGRAPH_CORE[LangGraph核心]
    end
    
    subgraph "存储层"
        LANGGRAPH_DB[(LangGraph DB)]
        FILE_STORAGE[(文件存储)]
        CACHE[(缓存)]
    end
    
    APP --> API_GATEWAY
    API_GATEWAY --> THREAD_SVC
    API_GATEWAY --> WORKFLOW_SVC
    THREAD_SVC --> CHECKPOINT_SVC
    WORKFLOW_SVC --> CHECKPOINT_SVC
    THREAD_SVC --> THREAD_CORE
    CHECKPOINT_SVC --> CHECKPOINT_CORE
    WORKFLOW_SVC --> LANGGRAPH_CORE
    CHECKPOINT_CORE --> LANGGRAPH_DB
    CHECKPOINT_CORE --> FILE_STORAGE
    CHECKPOINT_CORE --> CACHE
```

## 7. 错误处理流程图

```mermaid
flowchart TD
    START[开始操作] --> TRY[尝试执行]
    TRY --> SUCCESS{操作成功?}
    SUCCESS -->|是| LOG_SUCCESS[记录成功日志]
    SUCCESS -->|否| CATCH[捕获异常]
    
    CATCH --> ERROR_TYPE{异常类型}
    ERROR_TYPE -->|存储错误| STORAGE_ERROR[存储异常处理]
    ERROR_TYPE -->|网络错误| NETWORK_ERROR[网络异常处理]
    ERROR_TYPE -->|数据错误| DATA_ERROR[数据异常处理]
    ERROR_TYPE -->|其他错误| GENERAL_ERROR[通用异常处理]
    
    STORAGE_ERROR --> RETRY{是否重试?}
    NETWORK_ERROR --> RETRY
    DATA_ERROR --> LOG_ERROR[记录错误日志]
    GENERAL_ERROR --> LOG_ERROR
    
    RETRY -->|是| WAIT[等待重试]
    RETRY -->|否| LOG_ERROR
    WAIT --> TRY
    
    LOG_SUCCESS --> RETURN_SUCCESS[返回成功结果]
    LOG_ERROR --> RETURN_ERROR[返回错误结果]
    
    RETURN_SUCCESS --> END[结束]
    RETURN_ERROR --> END
```

## 8. 性能监控图

```mermaid
graph LR
    subgraph "性能指标收集"
        COLLECTOR[指标收集器]
        TIMER[操作计时器]
        COUNTER[操作计数器]
        GAUGE[状态监控器]
    end
    
    subgraph "性能指标"
        LATENCY[延迟指标]
        THROUGHPUT[吞吐量指标]
        ERROR_RATE[错误率指标]
        RESOURCE_USAGE[资源使用指标]
    end
    
    subgraph "监控输出"
        DASHBOARD[监控面板]
        ALERTS[告警系统]
        LOGS[日志系统]
        METRICS_DB[指标数据库]
    end
    
    COLLECTOR --> TIMER
    COLLECTOR --> COUNTER
    COLLECTOR --> GAUGE
    
    TIMER --> LATENCY
    COUNTER --> THROUGHPUT
    COUNTER --> ERROR_RATE
    GAUGE --> RESOURCE_USAGE
    
    LATENCY --> DASHBOARD
    THROUGHPUT --> DASHBOARD
    ERROR_RATE --> ALERTS
    RESOURCE_USAGE --> ALERTS
    
    DASHBOARD --> METRICS_DB
    ALERTS --> LOGS
    LOGS --> METRICS_DB
```

这些架构图清晰地展示了Thread检查点子模块的设计思路，包括组件关系、数据流、状态转换等关键方面，为后续的实现提供了详细的指导。