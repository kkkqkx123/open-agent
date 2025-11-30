# 模块关系图和架构图

## 概述

本文档包含日志模块的架构图和组件关系图，帮助理解系统的整体设计和组件间的交互关系。

## 整体架构图

### 系统架构层次

```mermaid
graph TB
    subgraph "应用层"
        APP[应用程序]
        API[API接口]
        CLI[命令行工具]
    end
    
    subgraph "服务层 (src/services/logger/)"
        LOGGER[Logger]
        REDACTOR[LogRedactor]
        ERROR_HANDLER[ErrorHandler]
        METRICS[MetricsCollector]
        STRUCTURED_LOGGER[StructuredFileLogger]
    end
    
    subgraph "核心层 (src/core/logger/)"
        LEVEL[LogLevel]
        
        subgraph "格式化器"
            BASE_FORMATTER[BaseFormatter]
            TEXT_FORMATTER[TextFormatter]
            JSON_FORMATTER[JsonFormatter]
            COLOR_FORMATTER[ColorFormatter]
        end
        
        subgraph "处理器"
            BASE_HANDLER[BaseHandler]
            CONSOLE_HANDLER[ConsoleHandler]
            FILE_HANDLER[FileHandler]
            JSON_HANDLER[JsonHandler]
        end
    end
    
    subgraph "输出目标"
        CONSOLE[控制台]
        FILES[文件系统]
        JSON_FILES[JSON文件]
        WEBHOOK[Webhook]
    end
    
    subgraph "外部系统"
        CONFIG[配置系统]
        MONITORING[监控系统]
        ALERTING[告警系统]
    end
    
    APP --> LOGGER
    API --> LOGGER
    CLI --> LOGGER
    
    LOGGER --> LEVEL
    LOGGER --> REDACTOR
    LOGGER --> ERROR_HANDLER
    LOGGER --> METRICS
    
    LOGGER --> BASE_HANDLER
    REDACTOR --> LOGGER
    ERROR_HANDLER --> LOGGER
    METRICS --> LOGGER
    
    BASE_HANDLER --> BASE_FORMATTER
    BASE_HANDLER --> CONSOLE
    BASE_HANDLER --> FILES
    
    TEXT_FORMATTER --> BASE_FORMATTER
    JSON_FORMATTER --> BASE_FORMATTER
    COLOR_FORMATTER --> TEXT_FORMATTER
    
    CONSOLE_HANDLER --> BASE_HANDLER
    FILE_HANDLER --> BASE_HANDLER
    JSON_HANDLER --> BASE_HANDLER
    
    CONSOLE_HANDLER --> CONSOLE
    FILE_HANDLER --> FILES
    JSON_HANDLER --> JSON_FILES
    
    STRUCTURED_LOGGER --> FILES
    
    ERROR_HANDLER --> ALERTING
    METRICS --> MONITORING
    
    CONFIG --> LOGGER
    CONFIG --> REDACTOR
    CONFIG --> ERROR_HANDLER
    CONFIG --> METRICS
```

### 组件依赖关系

```mermaid
graph LR
    subgraph "核心依赖"
        LEVEL[LogLevel]
        BASE_FORMATTER[BaseFormatter]
        BASE_HANDLER[BaseHandler]
    end
    
    subgraph "格式化器实现"
        TEXT_FORMATTER[TextFormatter]
        JSON_FORMATTER[JsonFormatter]
        COLOR_FORMATTER[ColorFormatter]
    end
    
    subgraph "处理器实现"
        CONSOLE_HANDLER[ConsoleHandler]
        FILE_HANDLER[FileHandler]
        JSON_HANDLER[JsonHandler]
    end
    
    subgraph "服务层组件"
        LOGGER[Logger]
        REDACTOR[LogRedactor]
        ERROR_HANDLER[ErrorHandler]
        METRICS[MetricsCollector]
        STRUCTURED_LOGGER[StructuredFileLogger]
    end
    
    TEXT_FORMATTER --> BASE_FORMATTER
    JSON_FORMATTER --> BASE_FORMATTER
    COLOR_FORMATTER --> TEXT_FORMATTER
    
    CONSOLE_HANDLER --> BASE_HANDLER
    FILE_HANDLER --> BASE_HANDLER
    JSON_HANDLER --> BASE_HANDLER
    
    LOGGER --> LEVEL
    LOGGER --> BASE_HANDLER
    LOGGER --> BASE_FORMATTER
    LOGGER --> REDACTOR
    
    REDACTOR --> LEVEL
    ERROR_HANDLER --> LOGGER
    METRICS --> LEVEL
    STRUCTURED_LOGGER --> LEVEL
    STRUCTURED_LOGGER --> REDACTOR
```

## 数据流图

### 日志处理流程

```mermaid
sequenceDiagram
    participant App as 应用程序
    participant Logger as 日志记录器
    participant Redactor as 脱敏器
    participant Handler as 处理器
    participant Formatter as 格式化器
    participant Output as 输出目标
    participant Metrics as 指标收集器
    participant ErrorHandler as 错误处理器

    App->>Logger: 记录日志(message, level, **kwargs)
    Logger->>Logger: 检查日志级别
    Logger->>Logger: 创建LogRecord
    Logger->>Redactor: 脱敏处理(record)
    Redactor-->>Logger: 脱敏后记录
    
    Logger->>Metrics: 更新指标
    Logger->>Handler: 处理日志记录
    
    Handler->>Handler: 检查处理器级别
    Handler->>Formatter: 格式化记录
    Formatter-->>Handler: 格式化文本
    Handler->>Output: 输出日志
    
    alt 处理异常
        Handler->>ErrorHandler: 处理错误
        ErrorHandler->>ErrorHandler: 记录错误日志
        ErrorHandler->>ErrorHandler: 执行错误处理程序
    end
```

### 配置加载流程

```mermaid
sequenceDiagram
    participant App as 应用程序
    participant Config as 配置加载器
    participant Validator as 配置验证器
    participant Logger as 日志记录器
    participant Handler as 处理器
    participant Redactor as 脱敏器

    App->>Config: 加载配置文件
    Config->>Config: 解析YAML/JSON
    Config->>Validator: 验证配置
    Validator-->>Config: 验证结果
    
    alt 验证成功
        Config->>Logger: 设置全局配置
        Logger->>Logger: 更新日志级别
        Logger->>Handler: 创建处理器
        Logger->>Redactor: 创建脱敏器
        
        Handler->>Handler: 设置格式化器
        Redactor->>Redactor: 加载脱敏规则
    else 验证失败
        Validator->>App: 抛出验证错误
    end
```

## 组件详细图

### 日志记录器内部结构

```mermaid
graph TB
    subgraph "Logger类"
        LOGGER[Logger实例]
        REGISTRY[日志记录器注册表]
        CONFIG[配置]
        HANDLERS[处理器列表]
        REDACTOR[脱敏器]
        LEVEL[日志级别]
        LOCK[线程锁]
    end
    
    subgraph "核心方法"
        DEBUG[debug()]
        INFO[info()]
        WARNING[warning()]
        ERROR[error()]
        CRITICAL[critical()]
        SET_LEVEL[set_level()]
        ADD_HANDLER[add_handler()]
        REMOVE_HANDLER[remove_handler()]
    end
    
    subgraph "内部方法"
        LOG[_log()]
        SHOULD_LOG[_should_log()]
        CREATE_RECORD[_create_log_record()]
        REDACT_RECORD[_redact_log_record()]
        SETUP_HANDLERS[_setup_handlers_from_config()]
    end
    
    LOGGER --> REGISTRY
    LOGGER --> CONFIG
    LOGGER --> HANDLERS
    LOGGER --> REDACTOR
    LOGGER --> LEVEL
    LOGGER --> LOCK
    
    DEBUG --> LOG
    INFO --> LOG
    WARNING --> LOG
    ERROR --> LOG
    CRITICAL --> LOG
    
    LOG --> SHOULD_LOG
    LOG --> CREATE_RECORD
    LOG --> REDACT_RECORD
    LOG --> HANDLERS
    
    CREATE_RECORD --> LEVEL
    REDACT_RECORD --> REDACTOR
    SETUP_HANDLERS --> CONFIG
```

### 脱敏器处理流程

```mermaid
flowchart TD
    START[开始脱敏] --> CHECK_LEVEL{检查日志级别}
    CHECK_LEVEL -->|DEBUG| RETURN_DEBUG[返回原始文本]
    CHECK_LEVEL -->|其他级别| CHECK_CACHE{检查缓存}
    
    CHECK_CACHE -->|命中| RETURN_CACHE[返回缓存结果]
    CHECK_CACHE -->|未命中| APPLY_PATTERNS[应用所有模式]
    
    APPLY_PATTERNS --> FOR_EACH_PATTERN{遍历模式}
    FOR_EACH_PATTERN --> CHECK_HASH{是否哈希脱敏}
    
    CHECK_HASH -->|是| HASH_REPLACE[哈希替换]
    CHECK_HASH -->|否| FIXED_REPLACE[固定替换]
    
    HASH_REPLACE --> UPDATE_CACHE[更新缓存]
    FIXED_REPLACE --> UPDATE_CACHE
    
    UPDATE_CACHE --> RETURN_RESULT[返回结果]
    RETURN_DEBUG --> END[结束]
    RETURN_CACHE --> END
    RETURN_RESULT --> END
```

### 错误处理流程

```mermaid
flowchart TD
    START[错误发生] --> BUILD_INFO[构建错误信息]
    BUILD_INFO --> LOG_ERROR[记录错误日志]
    LOG_ERROR --> CHECK_HANDLER{检查错误处理程序}
    
    CHECK_HANDLER -->|存在| EXECUTE_HANDLER[执行处理程序]
    CHECK_HANDLER -->|不存在| END[结束]
    
    EXECUTE_HANDLER --> TRY_HANDLER{尝试执行}
    TRY_HANDLER -->|成功| END
    TRY_HANDLER -->|失败| LOG_HANDLER_ERROR[记录处理程序错误]
    LOG_HANDLER_ERROR --> END
```

### 指标收集流程

```mermaid
flowchart TD
    START[指标事件] --> DETERMINE_TYPE[确定指标类型]
    
    DETERMINE_TYPE --> COUNTER{计数器}
    DETERMINE_TYPE --> GAUGE{仪表盘}
    DETERMINE_TYPE --> HISTOGRAM{直方图}
    
    COUNTER --> INCREMENT[增加计数]
    GAUGE --> SET_VALUE[设置值]
    HISTOGRAM --> OBSERVE[观察值]
    
    INCREMENT --> CREATE_KEY[创建指标键]
    SET_VALUE --> CREATE_KEY
    OBSERVE --> CREATE_KEY
    
    CREATE_KEY --> UPDATE_METRICS[更新指标存储]
    UPDATE_METRICS --> END[结束]
```

## 部署架构图

### 单机部署架构

```mermaid
graph TB
    subgraph "应用服务器"
        APP1[应用实例1]
        APP2[应用实例2]
        APP3[应用实例3]
    end
    
    subgraph "日志系统"
        LOGGER[日志模块]
        FILES[本地文件]
    end
    
    subgraph "监控系统"
        METRICS_COLLECTOR[指标收集器]
        PROMETHEUS[Prometheus]
    end
    
    subgraph "告警系统"
        ALERTMANAGER[AlertManager]
        EMAIL[邮件通知]
        SLACK[Slack通知]
    end
    
    APP1 --> LOGGER
    APP2 --> LOGGER
    APP3 --> LOGGER
    
    LOGGER --> FILES
    LOGGER --> METRICS_COLLECTOR
    
    METRICS_COLLECTOR --> PROMETHEUS
    PROMETHEUS --> ALERTMANAGER
    
    ALERTMANAGER --> EMAIL
    ALERTMANAGER --> SLACK
```

### 分布式部署架构

```mermaid
graph TB
    subgraph "应用层"
        APP1[应用服务器1]
        APP2[应用服务器2]
        APP3[应用服务器3]
        LB[负载均衡器]
    end
    
    subgraph "日志收集层"
        FLUENTD[Fluentd]
        LOGSTASH[Logstash]
    end
    
    subgraph "日志存储层"
        ELASTICSEARCH[Elasticsearch]
        KIBANA[Kibana]
    end
    
    subgraph "监控层"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
    end
    
    subgraph "告警层"
        ALERTMANAGER[AlertManager]
        PAGERDUTY[PagerDuty]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    APP1 --> FLUENTD
    APP2 --> LOGSTASH
    APP3 --> FLUENTD
    
    FLUENTD --> ELASTICSEARCH
    LOGSTASH --> ELASTICSEARCH
    
    ELASTICSEARCH --> KIBANA
    
    APP1 --> PROMETHEUS
    APP2 --> PROMETHEUS
    APP3 --> PROMETHEUS
    
    PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERTMANAGER
    
    ALERTMANAGER --> PAGERDUTY
```

## 性能架构图

### 高性能日志处理

```mermaid
graph TB
    subgraph "应用层"
        APP[应用程序]
        BUFFER[日志缓冲区]
    end
    
    subgraph "异步处理层"
        QUEUE[消息队列]
        WORKER[工作线程]
        BATCH_PROCESSOR[批处理器]
    end
    
    subgraph "存储层"
        FAST_STORAGE[高速存储]
        SLOW_STORAGE[慢速存储]
        ARCHIVE[归档存储]
    end
    
    subgraph "索引层"
        INDEX[日志索引]
        SEARCH[搜索引擎]
    end
    
    APP --> BUFFER
    BUFFER --> QUEUE
    
    QUEUE --> WORKER
    WORKER --> BATCH_PROCESSOR
    
    BATCH_PROCESSOR --> FAST_STORAGE
    BATCH_PROCESSOR --> SLOW_STORAGE
    
    FAST_STORAGE --> INDEX
    SLOW_STORAGE --> ARCHIVE
    
    INDEX --> SEARCH
```

### 缓存架构

```mermaid
graph TB
    subgraph "缓存层"
        L1_CACHE[L1缓存 - 内存]
        L2_CACHE[L2缓存 - Redis]
        L3_CACHE[L3缓存 - 磁盘]
    end
    
    subgraph "数据源"
        CONFIG_SOURCE[配置源]
        PATTERN_SOURCE[模式源]
        METADATA_SOURCE[元数据源]
    end
    
    subgraph "应用层"
        LOGGER[日志记录器]
        REDACTOR[脱敏器]
        FORMATTER[格式化器]
    end
    
    LOGGER --> L1_CACHE
    REDACTOR --> L1_CACHE
    FORMATTER --> L1_CACHE
    
    L1_CACHE --> L2_CACHE
    L2_CACHE --> L3_CACHE
    
    L3_CACHE --> CONFIG_SOURCE
    L3_CACHE --> PATTERN_SOURCE
    L3_CACHE --> METADATA_SOURCE
```

## 安全架构图

### 安全日志处理

```mermaid
graph TB
    subgraph "应用层"
        APP[应用程序]
        SENSITIVE_DATA[敏感数据]
    end
    
    subgraph "安全处理层"
        REDACTOR[脱敏器]
        ENCRYPTOR[加密器]
        ACCESS_CONTROL[访问控制]
    end
    
    subgraph "传输层"
        TLS[TLS传输]
        VPN[VPN通道]
    end
    
    subgraph "存储层"
        ENCRYPTED_STORAGE[加密存储]
        ACCESS_LOG[访问日志]
        AUDIT_LOG[审计日志]
    end
    
    subgraph "监控层"
        SECURITY_MONITOR[安全监控]
        ANOMALY_DETECTION[异常检测]
    end
    
    APP --> SENSITIVE_DATA
    SENSITIVE_DATA --> REDACTOR
    
    REDACTOR --> ENCRYPTOR
    ENCRYPTOR --> ACCESS_CONTROL
    
    ACCESS_CONTROL --> TLS
    TLS --> ENCRYPTED_STORAGE
    
    ACCESS_CONTROL --> VPN
    VPN --> AUDIT_LOG
    
    ENCRYPTED_STORAGE --> ACCESS_LOG
    ACCESS_LOG --> SECURITY_MONITOR
    AUDIT_LOG --> ANOMALY_DETECTION
```

## 扩展架构图

### 插件化架构

```mermaid
graph TB
    subgraph "核心系统"
        LOGGER_CORE[日志核心]
        PLUGIN_MANAGER[插件管理器]
        REGISTRY[插件注册表]
    end
    
    subgraph "插件接口"
        HANDLER_PLUGIN[处理器插件接口]
        FORMATTER_PLUGIN[格式化器插件接口]
        REDACTOR_PLUGIN[脱敏器插件接口]
        OUTPUT_PLUGIN[输出插件接口]
    end
    
    subgraph "插件实现"
        CUSTOM_HANDLER[自定义处理器]
        CUSTOM_FORMATTER[自定义格式化器]
        CUSTOM_REDACTOR[自定义脱敏器]
        CUSTOM_OUTPUT[自定义输出]
    end
    
    subgraph "第三方集成"
        SPLUNK[Splunk插件]
        ELASTIC[Elasticsearch插件]
        KAFKA[Kafka插件]
        SYSLOG[Syslog插件]
    end
    
    LOGGER_CORE --> PLUGIN_MANAGER
    PLUGIN_MANAGER --> REGISTRY
    
    REGISTRY --> HANDLER_PLUGIN
    REGISTRY --> FORMATTER_PLUGIN
    REGISTRY --> REDACTOR_PLUGIN
    REGISTRY --> OUTPUT_PLUGIN
    
    HANDLER_PLUGIN --> CUSTOM_HANDLER
    FORMATTER_PLUGIN --> CUSTOM_FORMATTER
    REDACTOR_PLUGIN --> CUSTOM_REDACTOR
    OUTPUT_PLUGIN --> CUSTOM_OUTPUT
    
    HANDLER_PLUGIN --> SPLUNK
    OUTPUT_PLUGIN --> ELASTIC
    OUTPUT_PLUGIN --> KAFKA
    OUTPUT_PLUGIN --> SYSLOG
```

这些架构图展示了日志模块的各个方面，从整体系统架构到具体的组件实现，帮助开发者全面理解日志系统的设计和实现。