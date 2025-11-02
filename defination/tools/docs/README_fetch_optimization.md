# Fetch.py 请求头优化说明

## 概述

本文档说明了对 `fetch.py` 文件中请求头处理的优化，使其更接近真实浏览器的行为，提高网页抓取的成功率并降低被识别为爬虫的风险。

## 主要优化内容

### 1. User-Agent 轮换

- **新增功能**: 创建了包含 16 种主流浏览器 User-Agent 的轮换列表
- **支持的浏览器**: Chrome、Firefox、Safari、Edge
- **支持的操作系统**: Windows、macOS、Linux
- **随机选择**: 每次请求自动随机选择一个 User-Agent

```python
# 获取随机 User-Agent
from fetch import get_random_user_agent
user_agent = get_random_user_agent()

# 在请求中使用
headers = get_browser_headers()  # 自动使用随机 User-Agent
```

### 2. 现代浏览器 Sec-Fetch-* 头部

添加了现代浏览器发送的安全相关头部：

- `Sec-Fetch-Dest: document` - 表示请求的目标是文档
- `Sec-Fetch-Mode: navigate` - 表示请求模式为导航
- `Sec-Fetch-Site: none` - 表示请求来源站点
- `Sec-Fetch-User: ?1` - 表示请求由用户激活触发

这些头部使请求看起来更像来自真实浏览器，遵循现代浏览器的安全策略。

### 3. Referer 头部支持

新增了对 Referer 头部的支持，可以模拟从特定页面跳转的行为：

```python
# 设置 Referer
headers = get_browser_headers(referer_url="https://example.com")
```

### 4. 请求头随机化

实现了可选请求头的随机化功能，避免每次请求都发送完全相同的头部组合：

- `DNT` (Do Not Track) - 随机包含或不包含
- `Sec-GPC` (Global Privacy Control) - 随机包含或不包含
- `Save-Data` - 随机启用或禁用数据节省模式
- `Pragma` - 随机添加 no-cache 指令

```python
# 启用随机化（默认）
headers = get_browser_headers(randomize=True)

# 禁用随机化
headers = get_browser_headers(randomize=False)
```

### 5. 增强的基础请求头

更新了基础请求头配置，使其更符合现代浏览器标准：

- 更完整的 Accept 头部，支持更多内容类型
- 更新了 Accept-Language，包含中文语言支持
- 添加了 Cache-Control: max-age=0
- 更新了 Accept-Encoding，包含 br 压缩支持

## API 更新

### get_browser_headers() 函数

新增参数：

```python
def get_browser_headers(
    custom_user_agent: Optional[str] = None,    # 自定义 User-Agent
    referer_url: Optional[str] = None,          # Referer URL
    randomize: bool = True                      # 是否随机化请求头
) -> dict:
```

### fetch_url() 函数

新增参数：

```python
def fetch_url(
    url: str,
    # ... 原有参数 ...
    user_agent: Optional[str] = None,           # 可选的自定义 User-Agent
    referer_url: Optional[str] = None,          # 可选的 Referer URL
    randomize_headers: bool = True,             # 是否随机化请求头
) -> Dict[str, Any]:
```

### fetch_url_content() 函数

新增参数：

```python
async def fetch_url_content(
    url: str,
    # ... 原有参数 ...
    user_agent: Optional[str] = None,           # 可选的自定义 User-Agent
    referer_url: Optional[str] = None,          # 可选的 Referer URL
    randomize_headers: bool = True,             # 是否随机化请求头
) -> Tuple[str, str]:
```

## 使用示例

### 基本使用（自动随机化）

```python
from fetch import fetch_url

# 使用默认设置（随机 User-Agent 和随机化请求头）
result = fetch_url("https://example.com")
print(result['content'])
```

### 自定义 User-Agent

```python
# 使用自定义 User-Agent
result = fetch_url(
    "https://example.com",
    user_agent="Mozilla/5.0 (Custom Browser/1.0)"
)
```

### 设置 Referer

```python
# 设置 Referer
result = fetch_url(
    "https://example.com/page2",
    referer_url="https://example.com/page1"
)
```

### 禁用随机化

```python
# 禁用请求头随机化，使用一致的请求头
result = fetch_url(
    "https://example.com",
    randomize_headers=False
)
```

### 完整自定义

```python
# 完全自定义请求头
result = fetch_url(
    "https://example.com",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    referer_url="https://google.com",
    randomize_headers=False
)
```

## 测试

运行测试脚本验证功能：

```bash
cd defination/tools
python test_fetch_headers.py
```

测试脚本会验证：
- User-Agent 轮换功能
- 请求头生成功能
- Sec-Fetch-* 头部
- 请求头随机化差异

## 优势

1. **更真实的浏览器模拟**: 使用现代浏览器的完整请求头集合
2. **降低检测风险**: User-Agent 轮换和请求头随机化避免固定指纹
3. **更好的兼容性**: 支持更多网站的反爬虫机制
4. **灵活的配置**: 可以完全自定义或使用默认随机化设置
5. **向后兼容**: 保持原有 API 的兼容性，新参数都有默认值

## 注意事项

1. 随机化功能默认启用，如需一致的请求头请设置 `randomize_headers=False`
2. User-Agent 列表会定期更新以包含最新的浏览器版本
3. 某些网站可能对特定的请求头组合有特殊要求，可根据需要调整
4. 结合代理 IP 轮换使用效果更佳