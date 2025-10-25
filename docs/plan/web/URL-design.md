## URL设计方案

### 1. 整体URL结构设计

采用**RESTful设计风格**，层次清晰，易于理解和维护：

```
http://localhost:8080/maaf/web/
├── dashboard/          # 仪表板
├── workflows/          # 工作流管理
├── analytics/          # 性能分析
├── errors/             # 错误管理
├── history/            # 历史数据
├── config/             # 配置管理
├── api/                # API接口
└── ws/                 # WebSocket端点
```

### 2. 详细URL设计方案

#### 仪表板模块
```
GET  /dashboard/                    # 主仪表板
GET  /dashboard/overview            # 概览数据
GET  /dashboard/metrics             # 核心指标
GET  /dashboard/status              # 系统状态
GET  /dashboard/quick-actions       # 快速操作
```

#### 工作流可视化模块
```
GET  /workflows/                    # 工作流列表
GET  /workflows/{id}                # 特定工作流详情
GET  /workflows/{id}/visualize      # 工作流可视化
GET  /workflows/{id}/debug          # 工作流调试
GET  /workflows/{id}/execution-path # 执行路径
POST /workflows/{id}/nodes/{nodeId}/debug  # 节点调试
```

#### 性能分析模块
```
GET  /analytics/                    # 分析主页
GET  /analytics/performance         # 性能分析
GET  /analytics/trends              # 趋势分析
GET  /analytics/costs               # 成本分析
GET  /analytics/sessions/{id}       # 会话分析
GET  /analytics/export              # 数据导出
```

#### 错误管理模块
```
GET  /errors/                       # 错误列表
GET  /errors/{id}                   # 错误详情
GET  /errors/stats                   # 错误统计
GET  /errors/categories             # 错误分类
POST /errors/{id}/resolve           # 标记错误已解决
POST /errors/{id}/feedback          # 提交错误反馈
```

#### 历史数据模块
```
GET  /history/                      # 历史数据主页
GET  /history/sessions              # 会话历史
GET  /history/sessions/{id}         # 特定会话
GET  /history/messages              # 消息历史
GET  /history/search                # 搜索功能
GET  /history/export                # 导出功能
GET  /history/bookmarks             # 书签管理
```

#### 配置管理模块
```
GET  /config/                       # 配置主页
GET  /config/current                # 当前配置
GET  /config/edit                   # 配置编辑器
POST /config/save                   # 保存配置
GET  /config/validate               # 配置验证
GET  /config/history                # 配置历史
GET  /config/export                 # 配置导出
POST /config/import                 # 配置导入
```

### 3. API接口设计

#### 数据获取API
```
GET  /api/v1/sessions                # 获取会话列表
GET  /api/v1/sessions/{id}           # 获取特定会话
GET  /api/v1/analytics/performance   # 获取性能数据
GET  /api/v1/analytics/errors        # 获取错误统计
GET  /api/v1/workflows/{id}/status    # 获取工作流状态
```

#### 实时数据API
```
WS   /ws/v1/realtime                 # 实时数据推送
WS   /ws/v1/sessions/{id}/updates    # 会话实时更新
WS   /ws/v1/metrics                  # 指标实时推送
```

### 4. TUI集成URL

在TUI中提供快速访问网页功能的URL：

```python
# TUI配置中添加网页访问URL
WEB_URLS = {
    "dashboard": "http://localhost:8080/maaf/web/dashboard/",
    "workflows": "http://localhost:8080/maaf/web/workflows/",
    "analytics": "http://localhost:8080/maaf/web/analytics/",
    "errors": "http://localhost:8080/maaf/web/errors/",
    "history": "http://localhost:8080/maaf/web/history/",
    "config": "http://localhost:8080/maaf/web/config/"
}
```

### 5. 导航集成方案

在TUI界面中添加网页访问入口：

1. **侧边栏添加快捷链接**
   - 在现有侧边栏中添加"网页视图"部分
   - 提供主要功能的快速访问链接

2. **命令系统集成**
   - 添加 `/web` 命令，打开网页界面
   - 支持 `/web analytics` 直接打开分析页面
   - 支持 `/web workflow {id}` 打开特定工作流

3. **快捷键支持**
   - `Ctrl+W`：打开网页仪表板
   - `Ctrl+Shift+A`：打开网页分析页面
   - `Ctrl+Shift+E`：打开网页错误管理

### 6. 响应式设计

确保URL在不同设备上的兼容性：

```
# 桌面端完整URL
http://localhost:8080/maaf/web/dashboard/

# 移动端优化URL
http://localhost:8080/maaf/web/m/dashboard/

# API调用
http://localhost:8080/maaf/web/api/v1/sessions/
```