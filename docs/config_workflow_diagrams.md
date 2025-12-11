# 配置系统工作流图表

## 1. 配置加载完整工作流

```mermaid
flowchart TD
    A[配置请求] --> B[ConfigProvider.get_config]
    B --> C{检查缓存}
    C -->|有效| D[返回缓存配置]
    C -->|无效| E[ConfigImpl.load_config]
    
    E --> F[ConfigLoader.load]
    F --> G[读取配置文件]
    G --> H[解析配置格式]
    H --> I[原始配置数据]
    
    I --> J[ProcessorChain.process]
    J --> K[InheritanceProcessor]
    K --> L[EnvironmentProcessor]
    L --> M[ReferenceProcessor]
    M --> N[TransformationProcessor]
    N --> O[ValidationProcessor]
    O --> P[处理后配置]
    
    P --> Q[ConfigImpl.validate_config]
    Q --> R{验证结果}
    R -->|失败| S[抛出验证异常]
    R -->|成功| T[ConfigImpl.transform_config]
    T --> U[最终配置]
    U --> V[更新缓存]
    V --> W[返回配置]
```

## 2. 模块依赖关系图

```mermaid
graph TB
    subgraph "基础设施层"
        CL[ConfigLoader]
        SL[SchemaLoader]
    end
    
    subgraph "注册中心层"
        CR[ConfigRegistry]
        SR[SchemaRegistry]
    end
    
    subgraph "工厂层"
        CF[ConfigFactory]
    end
    
    subgraph "处理器层"
        BP[BaseProcessor]
        EP[EnvironmentProcessor]
        IP[InheritanceProcessor]
        RP[ReferenceProcessor]
        TP[TransformationProcessor]
        VP[ValidationProcessor]
        DP[DiscoveryProcessor]
        TC[TypeConverter]
    end
    
    subgraph "实现层"
        PC[ConfigProcessorChain]
        BCI[BaseConfigImpl]
        BSG[BaseSchemaGenerator]
    end
    
    subgraph "提供者层"
        BCP[BaseConfigProvider]
    end
    
    %% 依赖关系
    CF --> CR
    CF --> CL
    CF --> SL
    CF --> PC
    CF --> BCI
    CF --> BCP
    
    CR --> SR
    CR --> PC
    
    EP --> BP
    IP --> BP
    RP --> BP
    TP --> BP
    VP --> BP
    DP --> BP
    
    TP --> TC
    VP --> SR
    DP --> CL
    
    PC --> EP
    PC --> IP
    PC --> RP
    PC --> TP
    PC --> VP
    
    BCI --> CL
    BCI --> PC
    BCI --> SL
    
    BCP --> BCI
    
    BSG --> BCP
```

## 3. 配置发现流程图

```mermaid
flowchart TD
    A[配置发现请求] --> B[DiscoveryProcessor.discover_files]
    B --> C[DiscoveryStrategy.discover_files]
    C --> D[遍历配置目录]
    D --> E[过滤支持的文件格式]
    E --> F[创建ConfigFileInfo]
    F --> G[提取文件元数据]
    G --> H[确定配置类型]
    H --> I[返回文件列表]
    
    I --> J[DiscoveryStrategy.get_file_hierarchy]
    J --> K[按类型分组文件]
    K --> L[构建层次结构]
    L --> M[返回层次结构]
    
    M --> N[配置加载请求]
    N --> O[ConfigLoader.load]
    O --> P[返回配置数据]
```

## 4. 处理器链执行流程

```mermaid
sequenceDiagram
    participant PC as ProcessorChain
    participant IP as InheritanceProcessor
    participant EP as EnvironmentProcessor
    participant RP as ReferenceProcessor
    participant TP as TransformationProcessor
    participant VP as ValidationProcessor
    
    PC->>IP: process(config, path)
    IP->>IP: _pre_process
    IP->>IP: _process_internal
    IP->>IP: _post_process
    IP-->>PC: processed_config
    
    PC->>EP: process(config, path)
    EP->>EP: _pre_process
    EP->>EP: _process_internal
    EP->>EP: _post_process
    EP-->>PC: processed_config
    
    PC->>RP: process(config, path)
    RP->>RP: _pre_process
    RP->>RP: _process_internal
    RP->>RP: _post_process
    RP-->>PC: processed_config
    
    PC->>TP: process(config, path)
    TP->>TP: _pre_process
    TP->>TP: _process_internal
    TP->>TP: _post_process
    TP-->>PC: processed_config
    
    PC->>VP: process(config, path)
    VP->>VP: _pre_process
    VP->>VP: _process_internal
    VP->>VP: _post_process
    VP-->>PC: final_config
    
    PC-->>调用者: 最终配置
```

## 5. 配置工厂初始化流程

```mermaid
flowchart TD
    A[创建ConfigFactory] --> B[初始化ConfigRegistry]
    B --> C[注册基础处理器]
    
    C --> D[创建EnvironmentProcessor]
    D --> E[注册到Registry]
    
    E --> F[创建InheritanceProcessor]
    F --> G[注册到Registry]
    
    G --> H[创建ReferenceProcessor]
    H --> I[注册到Registry]
    
    I --> J[创建TypeConverter]
    J --> K[创建TransformationProcessor]
    K --> L[注册到Registry]
    
    L --> M[创建ValidationProcessor]
    M --> N[注册到Registry]
    
    N --> O[工厂初始化完成]
```

## 6. 模块配置注册流程

```mermaid
flowchart TD
    A[register_module_config] --> B{是否有schema}
    B -->|有| C[注册schema到Registry]
    B -->|无| D[跳过schema注册]
    
    C --> E{是否有processor_names}
    D --> E
    E -->|有| F[创建ProcessorChain]
    E -->|无| G[使用默认ProcessorChain]
    
    F --> H[注册ProcessorChain到Registry]
    G --> I[创建ConfigImpl]
    H --> I
    
    I --> J[注册ConfigImpl到Registry]
    J --> K[创建ConfigProvider]
    K --> L[注册ConfigProvider到Registry]
    L --> M[注册完成]
```

## 7. 配置缓存管理流程

```mermaid
stateDiagram-v2
    [*] --> 检查缓存
    检查缓存 --> 缓存有效: 缓存存在且未过期
    检查缓存 --> 加载配置: 缓存无效或不存在
    
    加载配置 --> 处理配置
    处理配置 --> 验证配置
    验证配置 --> 转换配置
    转换配置 --> 更新缓存
    更新缓存 --> 返回配置
    
    缓存有效 --> 返回配置
    返回配置 --> [*]
    
    state 清除缓存 {
        [*] --> 清除特定配置
        清除特定配置 --> [*]
        [*] --> 清除所有缓存
        清除所有缓存 --> [*]
    }
```

## 8. 配置验证流程

```mermaid
flowchart TD
    A[配置验证请求] --> B[获取配置Schema]
    B --> C{Schema是否存在}
    C -->|不存在| D[返回验证成功]
    C -->|存在| E[执行Schema验证]
    
    E --> F[检查必需字段]
    F --> G[检查字段类型]
    G --> H[检查字段格式]
    H --> I[检查值范围]
    I --> J[检查自定义规则]
    
    J --> K{验证结果}
    K -->|成功| L[返回验证成功]
    K -->|失败| M[收集错误信息]
    M --> N[返回验证失败]
    
    D --> O[验证完成]
    L --> O
    N --> O
```

## 9. 错误处理流程

```mermaid
flowchart TD
    A[配置操作] --> B{是否发生异常}
    B -->|否| C[操作成功]
    B -->|是| D[捕获异常]
    
    D --> E{异常类型}
    E -->|ConfigNotFoundError| F[配置文件不存在]
    E -->|ConfigFormatError| G[配置格式错误]
    E -->|ValidationError| H[配置验证失败]
    E -->|其他异常| I[未知错误]
    
    F --> J[记录错误日志]
    G --> J
    H --> J
    I --> J
    
    J --> K[抛出处理后的异常]
    K --> L[上层处理]
```

## 10. 配置系统架构层次图

```mermaid
graph TB
    subgraph "应用层"
        APP[应用程序]
    end
    
    subgraph "服务层"
        CS[配置服务]
    end
    
    subgraph "提供者层"
        BCP[BaseConfigProvider]
        LLMCP[LLMConfigProvider]
        WFCP[WorkflowConfigProvider]
        TCP[ToolsConfigProvider]
    end
    
    subgraph "实现层"
        BCI[BaseConfigImpl]
        LLMCI[LLMConfigImpl]
        WFCI[WorkflowConfigImpl]
        TCI[ToolsConfigImpl]
    end
    
    subgraph "处理层"
        PC[ProcessorChain]
        BP[BaseProcessor]
        EP[EnvironmentProcessor]
        IP[InheritanceProcessor]
        RP[ReferenceProcessor]
        TP[TransformationProcessor]
        VP[ValidationProcessor]
        DP[DiscoveryProcessor]
    end
    
    subgraph "工厂层"
        CF[ConfigFactory]
    end
    
    subgraph "注册中心层"
        CR[ConfigRegistry]
        SR[SchemaRegistry]
    end
    
    subgraph "基础设施层"
        CL[ConfigLoader]
        SL[SchemaLoader]
    end
    
    %% 层次关系
    APP --> CS
    CS --> BCP
    CS --> LLMCP
    CS --> WFCP
    CS --> TCP
    
    BCP --> BCI
    LLMCP --> LLMCI
    WFCP --> WFCI
    TCP --> TCI
    
    BCI --> PC
    LLMCI --> PC
    WFCI --> PC
    TCI --> PC
    
    PC --> BP
    PC --> EP
    PC --> IP
    PC --> RP
    PC --> TP
    PC --> VP
    PC --> DP
    
    CF --> CR
    CF --> CL
    CF --> SL
    CF --> PC
    
    CR --> SR
    VP --> SR
    DP --> CL
```

这些图表清晰地展示了配置系统的各个工作流程和模块关系，有助于理解系统的整体架构和运行机制。