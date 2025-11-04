# TUI界面特殊按键输入处理机制分析

## 概述

本项目采用分层架构处理TUI界面中的特殊按键输入，支持多种键盘协议，确保在不同终端环境下都能正确识别和处理特殊按键。

## 核心架构组件

### 1. KeypressContext - 核心按键处理引擎
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx`

主要功能：
- 监听stdin输入流
- 解析各种按键协议序列
- 分发标准化按键事件给订阅者
- 处理粘贴模式和拖拽输入

关键方法：
- `parseKittyPrefix()`: 解析Kitty键盘协议序列
- `handleKeypress()`: 处理单个按键事件
- `handleRawKeypress()`: 处理原始输入数据
- `broadcast()`: 向所有订阅者分发按键事件

### 2. useKeypress Hook - 简化接口
**文件位置**: `packages/cli/src/ui/hooks/useKeypress.ts`

提供简化的按键监听接口，供React组件使用。

## 支持的按键协议

### Kitty键盘协议 (主要协议)
**支持格式**:
- `ESC[<keycode>;<modifiers>u` - CSI-u格式
- `ESC[<keycode>~` - 波浪号编码格式
- `ESC[<letter>` - 传统功能键格式

**特殊按键映射**:

| 按键 | Kitty序列 | 说明 |
|-----|-----------|------|
| Enter | `ESC[13u` | 普通Enter键 |
| Numpad Enter | `ESC[57414u` | 数字键盘Enter |
| Escape | `ESC[27u` | Escape键 |
| Tab | `ESC[9u` | Tab键 |
| Shift+Tab | `ESC[9;2u` | Shift+Tab组合 |
| Backspace | `ESC[127u` | 退格键 |
| Alt+Backspace | `ESC[127;3u` | Alt+退格组合 |
| Ctrl+Backspace | `ESC[127;5u` | Ctrl+退格组合 |

**方向键和功能键**:
- 方向键: `ESC[<code>;modifier(A|B|C|D)`
- F1-F4: `ESC[1;modifier(P|Q|R|S)`
- Home/End: `ESC[1;modifier(H|F)` 或 `ESC[1~`/`ESC[4~`
- Delete/Insert: `ESC[3~`/`ESC[2~`
- PageUp/PageDown: `ESC[5~`/`ESC[6~`

### 传统Escape序列 (向后兼容)
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (200-400行)

支持传统终端序列：
- 方向键: `ESC[A`/`ESC[B`/`ESC[C`/`ESC[D`
- Home/End: `ESC[H`/`ESC[F]`
- 反向Tab: `ESC[Z` (映射为Shift+Tab)

### Alt键字符映射
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (50-70行)

对于不支持Kitty协议的终端，维护Alt键字符映射表：
```typescript
const ALT_KEY_CHARACTER_MAP: Record<string, string> = {
  '\u00E5': 'a',  // å -> Alt+a
  '\u222B': 'b',  // ∫ -> Alt+b
  '\u00E7': 'c',  // ç -> Alt+c
  // ... 完整映射表包含a-z所有字母
};
```

## 特殊按键处理逻辑

### Enter键处理
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (350-450行)

- 支持普通Enter和数字键盘Enter的区分
- 处理各种修饰符组合 (Ctrl/Shift/Alt)
- 特殊处理Shift+Enter模式 (反斜杠+Enter检测)
- 5ms时间窗口检测反斜杠+Enter组合

### Escape键处理
**文件位置**: `packages/cli/src/ui/components/InputPrompt.tsx` (430-500行)

- 双重ESC清除输入功能
- 模式切换 (退出shell模式、搜索模式等)
- 状态重置功能
- 500ms超时检测双重ESC

### 粘贴模式处理
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (600-700行)

- 支持终端粘贴模式: `ESC[200~` ... `ESC[201~`
- 多行文本作为单个粘贴事件处理
- 粘贴保护机制防止意外提交
- 40ms保护窗口防止误触发

### 拖拽输入处理
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (150-200行)

- 引号字符触发拖拽模式
- 100ms超时后广播完整输入
- 防止碎片化输入处理

## 按键分发机制

### 事件订阅系统
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (120-150行)

```typescript
const broadcast = (key: Key) => {
  for (const handler of subscribers) {
    handler(key);
  }
};
```

- 支持多个处理器同时监听
- 按键事件的标准化格式
- 修饰符状态的正确传递

### 标准化按键格式
```typescript
interface Key {
  name: string;        // 按键名称
  ctrl: boolean;       // Ctrl修饰符
  meta: boolean;       // Alt/Option修饰符
  shift: boolean;      // Shift修饰符
  paste: boolean;      // 是否为粘贴内容
  sequence: string;    // 原始序列
  kittyProtocol?: boolean; // 是否来自Kitty协议
}
```

## Vim模式集成

### Vim按键处理
**文件位置**: `packages/cli/src/ui/hooks/vim.ts`

**普通模式** (NORMAL):
- h/j/k/l导航
- 各种删除命令 (x, dw, dd, D)
- 各种修改命令 (i, a, cw, cc, C)
- 数字前缀支持重复操作

**插入模式** (INSERT):
- 正常字符输入
- Escape键返回普通模式
- 光标位置管理

**命令重复**:
- `.` 命令重复上次操作
- 支持复杂操作的重复执行

### Vim模式切换
**文件位置**: `packages/cli/src/ui/hooks/vim.ts` (200-300行)

关键方法：
- `handleNormalModeInput()`: 处理普通模式按键
- `handleInsertModeInput()`: 处理插入模式按键
- `executeCommand()`: 执行具体Vim命令
- `normalizeKey()`: 按键输入标准化

## 错误处理和容错机制

### 序列超时处理
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (550-650行)

- 50ms超时处理不完整的Kitty序列
- 自动刷新不完整序列
- 防止输入阻塞

### 缓冲区溢出保护
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (480-520行)

- 最大32字符限制防止恶意输入
- 溢出时记录日志并清空缓冲区
- 保持系统稳定性

### 协议降级处理
- 不支持Kitty协议时自动降级到传统序列
- 混合协议环境下的兼容性处理
- 终端能力自动检测

### 调试支持
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.tsx` (调试模式)

- 详细的按键日志记录功能
- 序列解析过程跟踪
- 错误情况详细报告

## 平台相关常量

**文件位置**: `packages/cli/src/ui/utils/platformConstants.ts`

定义了所有按键处理相关的常量：
- Kitty协议按键码定义
- 修饰符位标志
- 超时时间常量
- 缓冲区大小限制

## 实际应用示例

### InputPrompt组件中的处理
**文件位置**: `packages/cli/src/ui/components/InputPrompt.tsx` (350-550行)

特殊按键处理：
- **Enter**: 命令提交
- **Ctrl+R**: 反向搜索历史
- **Tab**: 自动补全
- **Escape**: 双重ESC清除输入或退出模式
- **Ctrl+C/Ctrl+L**: 重置当前设置到默认值

### 设置对话框中的处理
**文件位置**: `packages/cli/src/ui/components/SettingsDialog.test.tsx` (1090-1140行)

- **Ctrl+C**: 重置当前设置为默认值
- **Ctrl+L**: 重置当前设置为默认值
- 方向键导航
- Escape键退出

## 测试覆盖

### 按键处理测试
**文件位置**: `packages/cli/src/ui/contexts/KeypressContext.test.tsx`

测试覆盖：
- Kitty协议序列解析测试
- 传统Escape序列测试
- Alt键字符映射测试
- 粘贴模式测试
- 各种终端兼容性测试

### Vim模式测试
**文件位置**: `packages/cli/src/ui/hooks/vim.ts` (测试用例)

测试覆盖：
- 普通模式命令测试
- 插入模式切换测试
- 命令重复功能测试
- 数字前缀功能测试

## 总结

本项目实现了完整的TUI特殊按键处理机制，通过支持多种键盘协议、完善的错误处理和广泛的测试覆盖，确保了在各种终端环境下都能提供一致的用户体验。架构设计清晰，分层合理，既保证了功能的完整性，又保持了代码的可维护性。