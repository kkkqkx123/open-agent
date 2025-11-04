# TUI键盘输入开发指南

## 快速开始

### 1. 理解架构
TUI键盘处理采用分层架构：
```
stdin输入 → KeypressContext → 标准化Key对象 → 组件处理
```

### 2. 基本使用
使用 `useKeypress` Hook 监听按键：
```typescript
import { useKeypress } from '../hooks/useKeypress';

function MyComponent() {
  useKeypress((key) => {
    if (key.name === 'enter' && !key.ctrl) {
      console.log('Enter pressed!');
    }
  }, true);
  
  return <Text>Listening for keys...</Text>;
}
```

### 3. 处理特殊按键
```typescript
useKeypress((key) => {
  // Ctrl+Enter
  if (key.name === 'enter' && key.ctrl) {
    handleSubmit();
  }
  
  // 双重ESC
  if (key.name === 'escape') {
    if (lastEscapeTime && Date.now() - lastEscapeTime < 500) {
      handleDoubleEscape();
    }
    setLastEscapeTime(Date.now());
  }
  
  // Tab补全
  if (key.name === 'tab' && !key.shift) {
    handleAutocomplete();
  } else if (key.name === 'tab' && key.shift) {
    handleReverseAutocomplete();
  }
}, true);
```

## 添加新按键支持

### 步骤1: 更新平台常量
在 `platformConstants.ts` 中添加新按键码：
```typescript
// 添加新的功能键
export const KEYCODE_F13 = 25;
export const KEYCODE_F14 = 26;

// 添加新的修饰符组合
export const MODIFIER_SUPER = 8; // Windows键/Cmd键
```

### 步骤2: 实现解析逻辑
在 `KeypressContext.tsx` 的 `parseKittyPrefix()` 中添加新序列模式：
```typescript
// 添加F13-F24支持
const f13Match = sequence.match(/^\x1b\[25(~|;(.*?)u)/);
if (f13Match) {
  const modifiers = f13Match[1] ? parseInt(f13Match[2]) || 0 : 0;
  return {
    key: {
      name: 'f13',
      ctrl: !!(modifiers & MODIFIER_CTRL_BIT),
      meta: !!(modifiers & MODIFIER_ALT_BIT),
      shift: !!(modifiers & MODIFIER_SHIFT_BIT),
      sequence: sequence.slice(0, f13Match[0].length),
      kittyProtocol: true
    },
    length: f13Match[0].length
  };
}
```

### 步骤3: 添加测试用例
在 `KeypressContext.test.tsx` 中添加测试：
```typescript
test('should parse F13 key with modifiers', () => {
  const result = parseKittyPrefix('\x1b[25;5u'); // Ctrl+F13
  expect(result).toEqual({
    key: {
      name: 'f13',
      ctrl: true,
      meta: false,
      shift: false,
      sequence: '\x1b[25;5u',
      kittyProtocol: true
    },
    length: 9
  });
});
```

### 步骤4: 更新文档
更新 `tui-keyboard-mapping-reference.md` 添加新按键映射表。

## 自定义按键处理

### 创建自定义Hook
```typescript
import { useKeypress } from './useKeypress';
import { useState, useCallback } from 'react';

export function useCustomKeyHandler() {
  const [mode, setMode] = useState<'normal' | 'insert'>('normal');
  
  const handleKey = useCallback((key) => {
    if (mode === 'normal') {
      switch (key.name) {
        case 'i':
          setMode('insert');
          break;
        case 'escape':
          // 自定义ESC处理
          break;
        default:
          // 其他普通模式处理
      }
    } else {
      if (key.name === 'escape') {
        setMode('normal');
      } else {
        // 插入模式处理
      }
    }
  }, [mode]);
  
  useKeypress(handleKey, true);
  
  return { mode };
}
```

### 集成到现有组件
```typescript
function CustomEditor() {
  const { mode } = useCustomKeyHandler();
  
  return (
    <Box>
      <Text color="green">Mode: {mode}</Text>
      {/* 编辑器内容 */}
    </Box>
  );
}
```

## 调试技巧

### 1. 启用详细日志
在 `KeypressContext.tsx` 顶部启用调试模式：
```typescript
const debugKeystrokeLogging = true;
```

### 2. 监控按键序列
```typescript
useKeypress((key) => {
  console.log('Raw sequence:', JSON.stringify(key.sequence));
  console.log('Parsed key:', key);
}, true);
```

### 3. 测试特定终端
```bash
# 测试Kitty协议支持
echo -e "\033[>1u" && read -rsn1 -t1

# 查看按键序列
showkey -a

# 使用xxd查看十六进制输出
xxd -p
```

### 4. 模拟按键事件
在测试中模拟复杂按键序列：
```typescript
import { renderHook } from '@testing-library/react-hooks';
import { KeypressProvider } from '../contexts/KeypressContext';
import { useKeypress } from '../hooks/useKeypress';

test('handles complex key sequence', () => {
  const keys = [];
  
  const wrapper = ({ children }) => (
    <KeypressProvider>{children}</KeypressProvider>
  );
  
  const { result } = renderHook(
    () => useKeypress((key) => keys.push(key), true),
    { wrapper }
  );
  
  // 模拟按键序列
  process.stdin.emit('data', Buffer.from('\x1b[13;5u')); // Ctrl+Enter
  
  expect(keys).toHaveLength(1);
  expect(keys[0]).toMatchObject({
    name: 'enter',
    ctrl: true,
    meta: false,
    shift: false
  });
});
```

## 性能优化

### 1. 减少重渲染
```typescript
const handleKey = useCallback((key) => {
  // 按键处理逻辑
}, [dependencies]);

// 只在需要时激活监听
useKeypress(handleKey, isActive);
```

### 2. 批量处理
```typescript
const keyBuffer = useRef([]);
const timeoutRef = useRef();

const handleKey = useCallback((key) => {
  keyBuffer.current.push(key);
  
  clearTimeout(timeoutRef.current);
  timeoutRef.current = setTimeout(() => {
    processKeyBuffer(keyBuffer.current);
    keyBuffer.current = [];
  }, 16); // ~60fps
}, []);
```

### 3. 条件监听
```typescript
// 只在特定条件下监听
useKeypress((key) => {
  if (isEditing) {
    handleEditKey(key);
  }
}, isEditing);
```

## 错误处理

### 1. 序列解析错误
```typescript
// 在parseKittyPrefix中添加错误处理
try {
  const result = parseComplexSequence(sequence);
  return result;
} catch (error) {
  console.error('Failed to parse sequence:', sequence, error);
  // 降级到传统解析
  return parseTraditionalSequence(sequence);
}
```

### 2. 缓冲区溢出保护
```typescript
// 防止恶意输入
if (buffer.length > MAX_KITTY_SEQUENCE_LENGTH) {
  console.warn('Sequence buffer overflow, flushing...');
  buffer = '';
  return null;
}
```

### 3. 超时处理
```typescript
// 设置合理的超时时间
const timeout = setTimeout(() => {
  if (buffer.length > 0) {
    console.warn('Sequence timeout, flushing buffer:', buffer);
    buffer = '';
  }
}, KITTY_SEQUENCE_TIMEOUT_MS);
```

## 兼容性考虑

### 1. 终端能力检测
```typescript
// 检测终端支持的协议
function detectTerminalCapabilities() {
  const supportsKitty = checkKittyProtocolSupport();
  const supportsFocus = checkFocusEventSupport();
  
  return {
    kittyProtocol: supportsKitty,
    focusEvents: supportsFocus,
    trueColor: checkTrueColorSupport()
  };
}
```

### 2. 协议降级
```typescript
// 自动降级到传统序列
function parseSequence(sequence) {
  // 首先尝试Kitty协议
  const kittyResult = parseKittyPrefix(sequence);
  if (kittyResult) return kittyResult;
  
  // 降级到传统序列
  const traditionalResult = parseTraditionalSequence(sequence);
  if (traditionalResult) return traditionalResult;
  
  // 最后尝试Alt键映射
  return parseAltKeySequence(sequence);
}
```

### 3. 跨平台支持
```typescript
// 处理平台差异
const isWindows = process.platform === 'win32';
const isMacOS = process.platform === 'darwin';

// Windows终端可能需要特殊处理
if (isWindows) {
  // Windows特定的按键映射
}

// macOS终端行为
if (isMacOS) {
  // macOS特定的处理
}
```

## 最佳实践

### 1. 清晰的按键处理逻辑
```typescript
// 好的做法：单一职责
function handleNavigationKey(key) {
  switch (key.name) {
    case 'up':
      moveUp();
      break;
    case 'down':
      moveDown();
      break;
    case 'left':
      moveLeft();
      break;
    case 'right':
      moveRight();
      break;
  }
}

function handleEditKey(key) {
  switch (key.name) {
    case 'backspace':
      deleteChar();
      break;
    case 'delete':
      deleteForward();
      break;
    case 'enter':
      insertNewline();
      break;
  }
}
```

### 2. 使用常量
```typescript
// 定义按键常量
const KEY_ENTER = 'enter';
const KEY_ESCAPE = 'escape';
const KEY_TAB = 'tab';

// 使用常量而不是硬编码字符串
if (key.name === KEY_ENTER) {
  // 处理Enter键
}
```

### 3. 完整的测试覆盖
```typescript
describe('Custom Key Handler', () => {
  test('handles all navigation keys', () => {
    const navigationKeys = ['up', 'down', 'left', 'right'];
    
    navigationKeys.forEach(keyName => {
      const key = { name: keyName, ctrl: false, meta: false, shift: false };
      expect(() => handleNavigationKey(key)).not.toThrow();
    });
  });
  
  test('handles modifier combinations', () => {
    const combinations = [
      { name: 'enter', ctrl: true },
      { name: 'tab', shift: true },
      { name: 'c', ctrl: true, meta: true }
    ];
    
    combinations.forEach(key => {
      expect(() => handleKey(key)).not.toThrow();
    });
  });
});
```

## 故障排除

### 常见问题1: 按键无响应
1. 检查 `useKeypress` 的第二个参数是否为 `true`
2. 确认组件在 `KeypressProvider` 内
3. 检查是否有其他组件拦截了按键
4. 启用调试日志查看是否接收到按键

### 常见问题2: 序列解析错误
1. 检查终端是否支持Kitty协议
2. 查看原始序列格式是否正确
3. 确认 `parseKittyPrefix` 中的正则表达式
4. 测试传统序列作为后备方案

### 常见问题3: 性能问题
1. 检查是否有昂贵的同步操作
2. 使用 `useCallback` 缓存处理函数
3. 考虑批量处理或防抖
4. 分析组件重渲染频率

### 常见问题4: 跨平台兼容性
1. 测试不同操作系统下的行为
2. 检查终端模拟器的差异
3. 验证特殊按键的序列格式
4. 考虑协议降级策略