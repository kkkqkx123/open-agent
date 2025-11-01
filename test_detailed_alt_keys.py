#!/usr/bin/env python3
"""详细测试Alt键组合的处理"""

from blessed import Terminal
import time

def test_detailed_alt_keys():
    """详细测试Alt键组合"""
    terminal = Terminal()
    
    print("详细测试Alt键组合处理...")
    print("请依次按下以下按键，每次按键后观察输出：")
    print("1. Alt+1")
    print("2. Alt+2") 
    print("3. Alt+3")
    print("4. ESC键退出")
    print("=" * 50)
    
    with terminal.cbreak():
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
                    
                    # 如果是ESC键，退出
                    if str(val) == '\x1b':
                        break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
                break
    
    print("测试结束")

if __name__ == "__main__":
    test_detailed_alt_keys()