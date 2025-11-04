# TUI键盘输入处理文件位置映射

## 核心处理文件

### 1. KeypressContext - 核心按键处理引擎
**文件路径**: `packages/cli/src/ui/contexts/KeypressContext.tsx`

**主要方法位置**:
- `parseKittyPrefix()`: 行 200-400 - 解析Kitty协议序列
- `handleKeypress()`: 行 400-600 - 处理单个按键事件
- `handleRawKeypress()`: 行 600-800 - 处理原始输入数据
- `broadcast()`: 行 120-150 - 分发按键事件给订阅者
- `handlePasteMode()`: 行 700-750 - 处理粘贴模式
- `handleDragMode()`: 行 150-200 - 处理拖拽输入

**关键数据结构**:
- `Key`接口: 行 20-30 - 标准化按键格式
- `KeypressHandler`类型: 行 32 - 按键处理器类型
- `ALT_KEY_CHARACTER_MAP`: 行 50-70 - Alt键字符映射表

### 2. useKeypress Hook - 简化接口
**文件路径**: `packages/cli/src/ui/hooks/useKeypress.ts`

**主要方法**:
- `useKeypress()`: 行 1-36 - 主Hook函数
- 参数: `onKeypress`回调函数和`isActive`选项

### 3. 平台常量定义
**文件路径**: `packages/cli/src/ui/utils/platformConstants.ts`

**关键常量**:
- Kitty协议按键码: 行 1-50
- 修饰符位标志: 行 52-55
- 超时时间常量: 行 57-60
- 最大序列长度: 行 62

## Vim模式处理

### Vim模式核心实现
**文件路径**: `packages/cli/src/ui/hooks/vim.ts`

**主要方法位置**:
- `useVim()`: 行 1-50 - 主Vim Hook
- `vimReducer()`: 行 50-150 - Vim状态管理
- `handleNormalModeInput()`: 行 150-250 - 普通模式处理
- `handleInsertModeInput()`: 行 250-350 - 插入模式处理
- `executeCommand()`: 行 350-450 - 执行Vim命令
- `normalizeKey()`: 行 450-500 - 按键标准化

**关键数据结构**:
- `VimMode`类型: 行 10-15 - NORMAL/INSERT模式
- `VimState`接口: 行 20-40 - Vim状态结构
- `VimAction`类型: 行 45-60 - Vim操作类型

### Vim模式上下文
**文件路径**: `packages/cli/src/ui/contexts/UIActionsContext.tsx`

**关键方法**:
- `vimHandleInput()`: 行 200-300 - Vim输入处理
- 集成到UIActionsContext中的Vim功能

## 实际应用组件

### 输入提示组件
**文件路径**: `packages/cli/src/ui/components/InputPrompt.tsx`

**按键处理方法位置**:
- `handleInput()`: 行 350-550 - 主要按键处理逻辑
- **Enter处理**: 行 380-420 - 命令提交
- **Escape处理**: 行 430-480 - 双重ESC清除输入
- **Tab处理**: 行 480-520 - 自动补全
- **Ctrl+R处理**: 行 520-560 - 反向搜索历史
- **Ctrl+C/Ctrl+L处理**: 行 560-600 - 重置设置

### 设置对话框组件
**文件路径**: `packages/cli/src/ui/components/SettingsDialog.tsx`

**按键处理方法**:
- 方向键导航: 行 200-250
- Escape键退出: 行 250-300
- Ctrl+C/Ctrl+L重置: 行 300-350

## 测试文件

### KeypressContext测试
**文件路径**: `packages/cli/src/ui/contexts/KeypressContext.test.tsx`

**测试覆盖**:
- Kitty协议序列解析测试: 行 1-100
- 传统Escape序列测试: 行 100-200
- Alt键字符映射测试: 行 200-300
- 粘贴模式测试: 行 300-400
- 终端兼容性测试: 行 400-500

### 输入提示测试
**文件路径**: `packages/cli/src/ui/components/InputPrompt.test.tsx`

**按键交互测试**:
- Enter键提交测试: 行 200-250
- Escape键清除测试: 行 250-300
- Tab键补全测试: 行 300-350
- Ctrl+R搜索测试: 行 350-400
- Ctrl+C/Ctrl+L重置测试: 行 400-450

### 设置对话框测试
**文件路径**: `packages/cli/src/ui/components/SettingsDialog.test.tsx`

**按键测试**:
- Ctrl+C重置测试: 行 1090-1140
- 方向键导航测试: 行 800-850
- Escape键退出测试: 行 850-900

## 辅助文件

### 文本缓冲区测试
**文件路径**: `packages/cli/src/ui/utils/text-buffer.test.ts`

**按键处理相关测试**:
- 输入缓冲区按键处理: 行 100-200
- 光标移动测试: 行 200-300

### 平台相关工具
**文件路径**: `packages/cli/src/ui/utils/platform.ts`

**终端检测相关**:
- 终端能力检测: 行 1-50
- Kitty协议支持检测: 行 50-100

## 文件依赖关系图

```
KeypressContext.tsx (核心)
    ├── useKeypress.ts (Hook接口)
    ├── vim.ts (Vim模式)
    ├── platformConstants.ts (常量)
    └── InputPrompt.tsx (实际应用)
        ├── SettingsDialog.tsx (设置对话框)
        └── 其他UI组件

测试文件依赖:
├── KeypressContext.test.tsx
├── InputPrompt.test.tsx
├── SettingsDialog.test.tsx
└── text-buffer.test.tsx
```

## 关键方法调用链

### 按键输入处理流程
```
stdin输入 → handleRawKeypress() → parseKittyPrefix() → broadcast() → 订阅者回调
                ↓
            传统序列解析 → Alt键映射 → 标准化Key对象
```

### Vim模式处理流程
```
按键输入 → vimHandleInput() → handleNormalModeInput()/handleInsertModeInput() → executeCommand() → 状态更新
```

### 组件级别处理流程
```
useKeypress() → onKeypress回调 → 组件特定逻辑 → UI更新
```

## 调试和开发建议

### 调试按键处理
1. **启用调试日志**: 在KeypressContext中设置`debugKeystrokeLogging = true`
2. **查看按键序列**: 使用`console.log`输出`key.sequence`
3. **测试特定按键**: 在KeypressContext.test.tsx中添加测试用例

### 添加新按键支持
1. **更新平台常量**: 在platformConstants.ts中添加新按键码
2. **实现解析逻辑**: 在parseKittyPrefix()中添加新序列模式
3. **添加测试用例**: 在KeypressContext.test.tsx中添加测试
4. **更新文档**: 在本文档中更新按键映射表

### 排查按键问题
1. **检查终端支持**: 确认终端是否支持Kitty协议
2. **验证序列格式**: 使用调试日志查看实际接收到的序列
3. **测试传统序列**: 禁用Kitty协议测试传统序列处理
4. **检查缓冲区**: 确认没有序列超时或缓冲区溢出问题