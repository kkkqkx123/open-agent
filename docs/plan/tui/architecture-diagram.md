# TUI界面架构图

## 新的界面架构设计

```mermaid
graph TB
    %% 主界面组件
    subgraph "主界面 (Main View)"
        Header[标题栏]
        Sidebar[精简侧边栏]
        Content[合并内容区]
        Input[输入面板]
        StatusBar[状态栏]
    end

    %% 子界面系统
    subgraph "子界面系统 (Subviews)"
        Analytics[分析监控子界面<br/>Alt+1]
        Visualization[可视化调试子界面<br/>Alt+2]
        System[系统管理子界面<br/>Alt+3]
        Errors[错误反馈子界面<br/>Alt+4]
    end

    %% 导航关系
    Header --> Analytics
    Header --> Visualization
    Header --> System
    Header --> Errors
    
    Analytics --> ESC[ESC返回]
    Visualization --> ESC
    System --> ESC
    Errors --> ESC
    
    ESC --> Header

    %% 样式定义
    classDef main fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef subview fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef nav fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class Header,Sidebar,Content,Input,StatusBar main
    class Analytics,Visualization,System,Errors subview
    class ESC nav
```

## 组件详细说明

### 主界面组件
- **标题栏**: 显示应用名称和当前会话状态
- **精简侧边栏**: Agent基本信息 + 工作流状态 + 核心指标
- **合并内容区**: 会话历史和流式输出合并显示
- **输入面板**: 多行输入支持和命令处理
- **状态栏**: 显示快捷键提示和当前模式

### 子界面组件
- **分析监控子界面 (Alt+1)**: 性能分析、详细指标、执行历史
- **可视化调试子界面 (Alt+2)**: 工作流可视化、节点调试
- **系统管理子界面 (Alt+3)**: Studio管理、端口配置、配置重载
- **错误反馈子界面 (Alt+4)**: 错误信息查看和反馈

## 导航流程

```mermaid
sequenceDiagram
    participant User
    participant TUIApp
    participant MainView
    participant Subview
    
    User->>TUIApp: 按 Alt+1/2/3/4
    TUIApp->>TUIApp: 设置 current_subview
    TUIApp->>Subview: 渲染对应子界面
    Subview-->>User: 显示子界面内容
    
    User->>TUIApp: 按 ESC键
    TUIApp->>TUIApp: 设置 current_subview = None
    TUIApp->>MainView: 渲染主界面
    MainView-->>User: 显示主界面内容
```

## 界面布局变化

### 当前布局
```
+---------------------------------------+
|               标题栏                  |
+-------------------+-------------------+
|    侧边栏         |     主内容区       |
| (Agent信息)       | (会话历史)        |
| (工作流状态)       +-------------------+
| (指标统计)        |     流式输出       |
+-------------------+-------------------+
|     LangGraph面板  |     输入面板       |
+-------------------+-------------------+
```

### 优化后布局
```
+---------------------------------------+
|               标题栏                  |
+-------------------+-------------------+
|  精简侧边栏       |    合并内容区       |
| (基本信息)        | (会话+输出)        |
| (核心状态)        |                   |
| (关键指标)        |                   |
+-------------------+-------------------+
|               输入面板                |
+---------------------------------------+
|               状态栏                  |
+---------------------------------------+
```

## 快捷键映射表

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| Alt+1 | 分析监控子界面 | 性能分析、指标统计、历史数据 |
| Alt+2 | 可视化调试子界面 | 工作流可视化、节点调试 |
| Alt+3 | 系统管理子界面 | Studio管理、端口配置 |
| Alt+4 | 错误反馈子界面 | 错误信息查看和反馈 |
| ESC | 返回主界面 | 从任何子界面返回 |

## 实施优先级

1. **高优先级**: 主界面精简 + 子界面导航框架
2. **中优先级**: 分析监控子界面实现
3. **中优先级**: 可视化调试子界面实现  
4. **低优先级**: 系统管理和错误反馈子界面

---

*架构图版本: V1.0*
*更新时间: 2025-10-21*