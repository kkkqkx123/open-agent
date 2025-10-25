# FastAPI后端API

这是模块化代理框架的FastAPI后端实现，提供RESTful API和WebSocket实时通信功能。

## 功能特性

- **会话管理**: 创建、查询、更新和删除会话
- **工作流管理**: 加载、运行和管理工作流
- **历史数据**: 查询和导出会话历史记录
- **分析统计**: 性能指标、Token使用和成本统计
- **WebSocket实时通信**: 实时推送会话和工作流状态更新
- **缓存系统**: 内存缓存提高响应速度
- **安全中间件**: CORS、限流和安全头设置

## 项目结构

```
src/presentation/api/
├── main.py                    # FastAPI应用入口
├── run_api.py                 # 启动脚本
├── test_api.py                # 测试脚本
├── config.py                  # 配置管理
├── dependencies.py            # 依赖注入配置
├── middleware.py              # 中间件配置
├── routers/                   # API路由
│   ├── sessions.py           # 会话管理API
│   ├── workflows.py          # 工作流管理API
│   ├── analytics.py          # 分析统计API
│   ├── history.py            # 历史数据API
│   └── websocket.py          # WebSocket API
├── models/                    # Pydantic模型
│   ├── requests.py           # 请求模型
│   ├── responses.py          # 响应模型
│   └── websocket.py          # WebSocket消息模型
├── services/                  # 服务层
│   ├── session_service.py    # 会话服务
│   ├── workflow_service.py   # 工作流服务
│   ├── analytics_service.py  # 分析服务
│   ├── history_service.py    # 历史服务
│   └── websocket_service.py  # WebSocket服务
├── data_access/               # 数据访问层
│   ├── session_dao.py        # 会话数据访问
│   ├── workflow_dao.py       # 工作流数据访问
│   └── history_dao.py        # 历史数据访问
├── cache/                     # 缓存系统
│   └── memory_cache.py       # 内存缓存实现
└── utils/                     # 工具函数
    ├── pagination.py         # 分页工具
    ├── serialization.py      # 序列化工具
    └── validation.py         # 验证工具
```

## 安装依赖

```bash
# 安装项目依赖
uv sync

# 或者安装特定依赖
uv add fastapi uvicorn aiosqlite websockets
```

## 启动服务

### 开发模式

```bash
# 使用启动脚本
python -m src.presentation.api.run_api

# 或者直接运行
python -m src.presentation.api.main
```

### 生产模式

```bash
# 设置环境变量
export ENVIRONMENT=production
export DEBUG=false

# 启动服务
uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000
```

## API文档

启动服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要API端点

### 会话管理

- `GET /sessions/` - 获取会话列表
- `POST /sessions/` - 创建新会话
- `GET /sessions/{session_id}` - 获取会话详情
- `PUT /sessions/{session_id}` - 更新会话
- `DELETE /sessions/{session_id}` - 删除会话
- `GET /sessions/{session_id}/history` - 获取会话历史

### 工作流管理

- `GET /workflows/` - 获取工作流列表
- `POST /workflows/load` - 加载工作流配置
- `POST /workflows/{workflow_id}/run` - 运行工作流
- `GET /workflows/{workflow_id}/visualization` - 获取工作流可视化

### 分析统计

- `GET /analytics/performance` - 获取性能指标
- `GET /analytics/tokens/{session_id}` - 获取Token统计
- `GET /analytics/cost/{session_id}` - 获取成本统计
- `GET /analytics/errors` - 获取错误统计

### 历史数据

- `GET /history/sessions/{session_id}/messages` - 获取会话消息
- `GET /history/sessions/{session_id}/search` - 搜索会话消息
- `GET /history/sessions/{session_id}/export` - 导出会话数据

### WebSocket

- `WS /ws/{client_id}` - WebSocket连接端点

## 测试

运行测试脚本验证API功能：

```bash
python -m src.presentation.api.test_api
```

## 配置

可以通过环境变量或`.env`文件配置API：

```env
# 应用设置
APP_NAME=Modular Agent API
APP_VERSION=0.1.0
DEBUG=true
ENVIRONMENT=development

# 服务器设置
HOST=0.0.0.0
PORT=8000

# 数据库设置
DATA_PATH=data

# 缓存设置
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# 日志设置
LOG_LEVEL=INFO
LOG_FILE=logs/api.log

# 安全设置
SECRET_KEY=your-secret-key-here

# CORS设置
CORS_ORIGINS=["*"]
```

## 数据存储

### SQLite数据库

- 会话元数据存储在 `data/sessions/metadata.db`
- 工作流元数据存储在 `data/workflows/metadata.db`

### JSON Lines文件

- 历史记录存储在 `data/history/YYYYMM/session_id.jsonl`
- 按月分目录存储，支持高效的时间范围查询

## 性能优化

- **内存缓存**: 缓存频繁查询的数据
- **分页查询**: 大数据集分页返回
- **异步处理**: 所有I/O操作使用异步方式
- **连接池**: 数据库连接复用

## 安全特性

- **CORS支持**: 跨域资源共享配置
- **请求限流**: 防止API滥用
- **安全头**: XSS、CSRF等安全防护
- **错误处理**: 统一的错误响应格式

## 监控和日志

- **结构化日志**: JSON格式日志输出
- **请求追踪**: 每个请求分配唯一ID
- **性能监控**: 记录请求处理时间
- **错误追踪**: 详细的错误堆栈信息

## 扩展开发

### 添加新的API端点

1. 在 `models/requests.py` 中定义请求模型
2. 在 `models/responses.py` 中定义响应模型
3. 在 `services/` 中实现业务逻辑
4. 在 `routers/` 中添加路由

### 添加新的中间件

1. 在 `middleware.py` 中实现中间件类
2. 在 `setup_middleware()` 函数中注册中间件

### 添加新的数据访问

1. 在 `data_access/` 中实现DAO类
2. 在 `dependencies.py` 中注册依赖

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据目录权限
   - 确保SQLite文件路径正确

2. **WebSocket连接失败**
   - 检查防火墙设置
   - 确认WebSocket端点URL正确

3. **缓存问题**
   - 重启服务清理缓存
   - 检查缓存TTL设置

### 调试模式

启用调试模式获取更详细的日志：

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m src.presentation.api.run_api