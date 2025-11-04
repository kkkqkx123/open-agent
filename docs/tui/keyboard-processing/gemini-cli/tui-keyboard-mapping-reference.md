# TUI键盘按键映射参考表

## Kitty键盘协议映射

### 基础按键
| 按键 | Kitty序列 | 标准化Key对象 |
|-----|-----------|---------------|
| Enter | `ESC[13u` | `{name: 'enter', ctrl: false, meta: false, shift: false}` |
| Numpad Enter | `ESC[57414u` | `{name: 'enter', ctrl: false, meta: false, shift: false}` |
| Escape | `ESC[27u` | `{name: 'escape', ctrl: false, meta: false, shift: false}` |
| Tab | `ESC[9u` | `{name: 'tab', ctrl: false, meta: false, shift: false}` |
| Backspace | `ESC[127u` | `{name: 'backspace', ctrl: false, meta: false, shift: false}` |
| Space | `ESC[32u` | `{name: 'space', ctrl: false, meta: false, shift: false}` |
| Delete | `ESC[3~` | `{name: 'delete', ctrl: false, meta: false, shift: false}` |
| Insert | `ESC[2~` | `{name: 'insert', ctrl: false, meta: false, shift: false}` |

### 修饰符组合
| 按键组合 | Kitty序列 | 标准化Key对象 |
|----------|-----------|---------------|
| Shift+Tab | `ESC[9;2u` | `{name: 'tab', ctrl: false, meta: false, shift: true}` |
| Ctrl+Enter | `ESC[13;5u` | `{name: 'enter', ctrl: true, meta: false, shift: false}` |
| Alt+Enter | `ESC[13;3u` | `{name: 'enter', ctrl: false, meta: true, shift: false}` |
| Ctrl+Backspace | `ESC[127;5u` | `{name: 'backspace', ctrl: true, meta: false, shift: false}` |
| Alt+Backspace | `ESC[127;3u` | `{name: 'backspace', ctrl: false, meta: true, shift: false}` |
| Ctrl+C | `ESC[99;5u` | `{name: 'c', ctrl: true, meta: false, shift: false}` |
| Ctrl+D | `ESC[100;5u` | `{name: 'd', ctrl: true, meta: false, shift: false}` |
| Ctrl+L | `ESC[108;5u` | `{name: 'l', ctrl: true, meta: false, shift: false}` |
| Ctrl+R | `ESC[114;5u` | `{name: 'r', ctrl: true, meta: false, shift: false}` |

### 方向键
| 按键 | Kitty序列 | 标准化Key对象 |
|-----|-----------|---------------|
| Up Arrow | `ESC[A` 或 `ESC[1;A` | `{name: 'up', ctrl: false, meta: false, shift: false}` |
| Down Arrow | `ESC[B` 或 `ESC[1;B` | `{name: 'down', ctrl: false, meta: false, shift: false}` |
| Right Arrow | `ESC[C` 或 `ESC[1;C` | `{name: 'right', ctrl: false, meta: false, shift: false}` |
| Left Arrow | `ESC[D` 或 `ESC[1;D` | `{name: 'left', ctrl: false, meta: false, shift: false}` |
| Shift+Up | `ESC[1;2A` | `{name: 'up', ctrl: false, meta: false, shift: true}` |
| Ctrl+Up | `ESC[1;5A` | `{name: 'up', ctrl: true, meta: false, shift: false}` |
| Alt+Up | `ESC[1;3A` | `{name: 'up', ctrl: false, meta: true, shift: false}` |

### 功能键 (F1-F12)
| 功能键 | Kitty序列 | 标准化Key对象 |
|--------|-----------|---------------|
| F1 | `ESC[1;P` 或 `ESC[11~` | `{name: 'f1', ctrl: false, meta: false, shift: false}` |
| F2 | `ESC[1;Q` 或 `ESC[12~` | `{name: 'f2', ctrl: false, meta: false, shift: false}` |
| F3 | `ESC[1;R` 或 `ESC[13~` | `{name: 'f3', ctrl: false, meta: false, shift: false}` |
| F4 | `ESC[1;S` 或 `ESC[14~` | `{name: 'f4', ctrl: false, meta: false, shift: false}` |
| F5 | `ESC[15~` | `{name: 'f5', ctrl: false, meta: false, shift: false}` |
| F6 | `ESC[17~` | `{name: 'f6', ctrl: false, meta: false, shift: false}` |
| F7 | `ESC[18~` | `{name: 'f7', ctrl: false, meta: false, shift: false}` |
| F8 | `ESC[19~` | `{name: 'f8', ctrl: false, meta: false, shift: false}` |
| F9 | `ESC[20~` | `{name: 'f9', ctrl: false, meta: false, shift: false}` |
| F10 | `ESC[21~` | `{name: 'f10', ctrl: false, meta: false, shift: false}` |
| F11 | `ESC[23~` | `{name: 'f11', ctrl: false, meta: false, shift: false}` |
| F12 | `ESC[24~` | `{name: 'f12', ctrl: false, meta: false, shift: false}` |

### 导航键
| 按键 | Kitty序列 | 标准化Key对象 |
|-----|-----------|---------------|
| Home | `ESC[H` 或 `ESC[1~` 或 `ESC[1;H` | `{name: 'home', ctrl: false, meta: false, shift: false}` |
| End | `ESC[F` 或 `ESC[4~` 或 `ESC[1;F` | `{name: 'end', ctrl: false, meta: false, shift: false}` |
| Page Up | `ESC[5~` | `{name: 'pageup', ctrl: false, meta: false, shift: false}` |
| Page Down | `ESC[6~` | `{name: 'pagedown', ctrl: false, meta: false, shift: false}` |

## 传统Escape序列映射 (向后兼容)

### 基础序列
| 按键 | 传统序列 | 标准化Key对象 |
|-----|----------|---------------|
| Up Arrow | `ESC[A` | `{name: 'up', ctrl: false, meta: false, shift: false}` |
| Down Arrow | `ESC[B` | `{name: 'down', ctrl: false, meta: false, shift: false}` |
| Right Arrow | `ESC[C` | `{name: 'right', ctrl: false, meta: false, shift: false}` |
| Left Arrow | `ESC[D` | `{name: 'left', ctrl: false, meta: false, shift: false}` |
| Shift+Tab | `ESC[Z` | `{name: 'tab', ctrl: false, meta: false, shift: true}` |
| Home | `ESC[H` | `{name: 'home', ctrl: false, meta: false, shift: false}` |
| End | `ESC[F` | `{name: 'end', ctrl: false, meta: false, shift: false}` |

### 功能键传统序列
| 功能键 | 传统序列 | 标准化Key对象 |
|--------|----------|---------------|
| F1 | `ESCOP` | `{name: 'f1', ctrl: false, meta: false, shift: false}` |
| F2 | `ESCOQ` | `{name: 'f2', ctrl: false, meta: false, shift: false}` |
| F3 | `ESCOR` | `{name: 'f3', ctrl: false, meta: false, shift: false}` |
| F4 | `ESCOS` | `{name: 'f4', ctrl: false, meta: false, shift: false}` |

## Alt键字符映射

### Alt+字母映射表
| Alt组合 | 字符 | 标准化Key对象 |
|---------|------|---------------|
| Alt+a | `å` (\u00E5) | `{name: 'a', ctrl: false, meta: true, shift: false}` |
| Alt+b | `∫` (\u222B) | `{name: 'b', ctrl: false, meta: true, shift: false}` |
| Alt+c | `ç` (\u00E7) | `{name: 'c', ctrl: false, meta: true, shift: false}` |
| Alt+d | `∂` (\u2202) | `{name: 'd', ctrl: false, meta: true, shift: false}` |
| Alt+e | `´` (\u00B4) | `{name: 'e', ctrl: false, meta: true, shift: false}` |
| Alt+f | `ƒ` (\u0192) | `{name: 'f', ctrl: false, meta: true, shift: false}` |
| Alt+g | `©` (\u00A9) | `{name: 'g', ctrl: false, meta: true, shift: false}` |
| Alt+h | `˙` (\u02D9) | `{name: 'h', ctrl: false, meta: true, shift: false}` |
| Alt+i | `ˆ` (\u02C6) | `{name: 'i', ctrl: false, meta: true, shift: false}` |
| Alt+j | `∆` (\u2206) | `{name: 'j', ctrl: false, meta: true, shift: false}` |
| Alt+k | `˚` (\u02DA) | `{name: 'k', ctrl: false, meta: true, shift: false}` |
| Alt+l | `¬` (\u00AC) | `{name: 'l', ctrl: false, meta: true, shift: false}` |
| Alt+m | `µ` (\u00B5) | `{name: 'm', ctrl: false, meta: true, shift: false}` |
| Alt+n | `˜` (\u02DC) | `{name: 'n', ctrl: false, meta: true, shift: false}` |
| Alt+o | `ø` (\u00F8) | `{name: 'o', ctrl: false, meta: true, shift: false}` |
| Alt+p | `π` (\u03C0) | `{name: 'p', ctrl: false, meta: true, shift: false}` |
| Alt+q | `œ` (\u0153) | `{name: 'q', ctrl: false, meta: true, shift: false}` |
| Alt+r | `®` (\u00AE) | `{name: 'r', ctrl: false, meta: true, shift: false}` |
| Alt+s | `ß` (\u00DF) | `{name: 's', ctrl: false, meta: true, shift: false}` |
| Alt+t | `†` (\u2020) | `{name: 't', ctrl: false, meta: true, shift: false}` |
| Alt+u | `¨` (\u00A8) | `{name: 'u', ctrl: false, meta: true, shift: false}` |
| Alt+v | `√` (\u221A) | `{name: 'v', ctrl: false, meta: true, shift: false}` |
| Alt+w | `∑` (\u2211) | `{name: 'w', ctrl: false, meta: true, shift: false}` |
| Alt+x | `≈` (\u2248) | `{name: 'x', ctrl: false, meta: true, shift: false}` |
| Alt+y | `¥` (\u00A5) | `{name: 'y', ctrl: false, meta: true, shift: false}` |
| Alt+z | `Ω` (\u03A9) | `{name: 'z', ctrl: false, meta: true, shift: false}` |

## 特殊模式序列

### 粘贴模式
| 模式 | 序列 | 说明 |
|------|------|------|
| 粘贴开始 | `ESC[200~` | 标记粘贴内容开始 |
| 粘贴结束 | `ESC[201~` | 标记粘贴内容结束 |
| 粘贴内容 | 多行文本 | `key.paste = true` |

### 拖拽模式
| 模式 | 序列 | 说明 |
|------|------|------|
| 拖拽触发 | `"` 或 `'` | 引号字符触发100ms超时 |
| 拖拽内容 | 后续字符 | 等待完整输入后广播 |

### 特殊处理序列
| 按键 | 序列 | 特殊处理 |
|-----|------|----------|
| Ctrl+C | `ESC[3;5~` 或 `\u0003` | 特殊退出处理 |
| VS Code Shift+Enter | `ESC[27;2;13~` | VS Code集成支持 |

## Vim模式按键映射

### 普通模式 (NORMAL)
| 按键 | Vim命令 | 功能 |
|-----|---------|------|
| `h` | 左移 | 光标左移 |
| `j` | 下移 | 光标下移 |
| `k` | 上移 | 光标上移 |
| `l` | 右移 | 光标右移 |
| `w` | 下一个单词 | 移动到下一个单词 |
| `b` | 上一个单词 | 移动到上一个单词 |
| `e` | 单词结尾 | 移动到单词结尾 |
| `0` | 行首 | 移动到行首 |
| `$` | 行尾 | 移动到行尾 |
| `x` | 删除字符 | 删除当前字符 |
| `dw` | 删除单词 | 删除到单词结尾 |
| `dd` | 删除行 | 删除整行 |
| `D` | 删除到行尾 | 删除到行尾 |
| `cw` | 修改单词 | 修改单词 |
| `cc` | 修改行 | 修改整行 |
| `C` | 修改到行尾 | 修改到行尾 |
| `i` | 插入模式 | 进入插入模式 |
| `a` | 追加模式 | 进入追加模式 |
| `u` | 撤销 | 撤销上次操作 |
| `Ctrl+r` | 重做 | 重做上次撤销 |
| `.` | 重复 | 重复上次操作 |

### 插入模式 (INSERT)
| 按键 | 功能 | 说明 |
|-----|------|------|
| `Escape` | 返回普通模式 | 退出插入模式 |
| 普通字符 | 插入文本 | 正常字符输入 |
| `Backspace` | 删除字符 | 删除前一个字符 |
| `Delete` | 删除字符 | 删除后一个字符 |

## 组件特定按键映射

### InputPrompt组件
| 按键 | 功能 | 实现位置 |
|-----|------|----------|
| `Enter` | 提交命令 | `handleInput()` 行 380-420 |
| `Escape` | 双重ESC清除输入 | `handleInput()` 行 430-480 |
| `Tab` | 自动补全 | `handleInput()` 行 480-520 |
| `Ctrl+R` | 反向搜索历史 | `handleInput()` 行 520-560 |
| `Ctrl+C` | 重置设置 | `handleInput()` 行 560-600 |
| `Ctrl+L` | 重置设置 | `handleInput()` 行 560-600 |
| `Ctrl+E` | 移动光标到行尾 | `handleInput()` 行 600-650 |
| `Ctrl+A` | 移动光标到行首 | `handleInput()` 行 650-700 |

### SettingsDialog组件
| 按键 | 功能 | 实现位置 |
|-----|------|----------|
| `Up Arrow` | 上一个设置项 | 组件内部处理 |
| `Down Arrow` | 下一个设置项 | 组件内部处理 |
| `Left Arrow` | 减少值 | 组件内部处理 |
| `Right Arrow` | 增加值 | 组件内部处理 |
| `Enter` | 确认选择 | 组件内部处理 |
| `Escape` | 退出对话框 | 组件内部处理 |
| `Ctrl+C` | 重置当前设置 | 组件内部处理 |
| `Ctrl+L` | 重置当前设置 | 组件内部处理 |

## 平台相关常量参考

### Kitty协议常量
```typescript
// 基础按键码
const KEYCODE_ENTER = 13;
const KEYCODE_ESCAPE = 27;
const KEYCODE_TAB = 9;
const KEYCODE_BACKSPACE = 127;
const KEYCODE_DELETE = 3;
const KEYCODE_INSERT = 2;

// 修饰符基础值
const MODIFIER_SHIFT = 2;
const MODIFIER_ALT = 3;
const MODIFIER_CTRL = 5;

// 功能键基础值
const F1_BASE = 11;
const F2_BASE = 12;
const F3_BASE = 13;
const F4_BASE = 14;
```

### 超时常量
```typescript
const KITTY_SEQUENCE_TIMEOUT_MS = 50;
const PASTE_MODE_PROTECTION_WINDOW_MS = 40;
const DRAG_DETECTION_TIMEOUT_MS = 100;
const BACKSLASH_ENTER_DETECTION_WINDOW_MS = 5;
const DOUBLE_ESCAPE_TIMEOUT_MS = 500;
```

### 缓冲区限制
```typescript
const MAX_KITTY_SEQUENCE_LENGTH = 32;
const MAX_PASTE_CONTENT_LENGTH = 10000;
```

## 调试参考

### 启用调试日志
在 `KeypressContext.tsx` 中设置：
```typescript
const debugKeystrokeLogging = true;
```

### 常见调试输出
```
[KEYPRESS] Raw input: \u001b[13;5u
[KEYPRESS] Parsed as Kitty: {name: 'enter', ctrl: true, meta: false, shift: false}
[KEYPRESS] Broadcasting to 3 subscribers
```

### 序列解析状态
- ✅ 完整序列: 成功解析
- ⏳ 等待更多: 序列不完整，等待超时
- ❌ 解析失败: 无法识别的序列，降级处理