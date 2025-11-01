#!/usr/bin/env python3
"""测试Alt键和ESC键的处理"""

from blessed import Terminal
import time

def test_alt_esc_keys():
    """测试Alt键和ESC键"""
    terminal = Terminal()
    
    print("测试Alt键和ESC键处理...")
    print("请依次按下以下按键，每次按键后观察输出：")
    print("1. Alt+1")
    print("2. Alt+2")
    print("3. ESC键")
    print("4. 再次按下ESC键退出")
    print("=" * 50)
    
    with terminal.cbreak():
        esc_count = 0
        while True:
            try:
                # 使用blessed的inkey()方法，设置更长的超时时间
                val = terminal.inkey(timeout=1.0)
                if val:
                    print(f"按键原始值: {repr(val)}")
                    print(f"  - is_sequence: {val.is_sequence}")
                    print(f"  - name: {val.name}")
                    print(f"  - code: {val.code}")
                    print(f"  - str: {repr(str(val))}")
                    if str(val):
                        print(f"  - ord: {ord(str(val))}")
                        print(f"  - len: {len(str(val))}")
                    print("-" * 30)
                    
                    # 如果是ESC键，计数并检查是否需要退出
                    if str(val) == '\x1b':
                        esc_count += 1
                        if esc_count >= 2:
                            break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
                break
    
    print("测试结束")

if __name__ == "__main__":
    test_alt_esc_keys()