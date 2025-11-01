#!/usr/bin/env python3
"""测试Alt键组合的处理"""

from blessed import Terminal

def test_alt_keys():
    """测试Alt键组合"""
    terminal = Terminal()
    
    print("测试Alt键组合处理...")
    print("请按下Alt+1, Alt+2, Alt+3等组合键，按ESC退出")
    print("=" * 50)
    
    with terminal.cbreak():
        while True:
            try:
                # 使用blessed的inkey()方法
                val = terminal.inkey(timeout=0.1)
                if val:
                    print(f"按键: {repr(val)}")
                    print(f"  - is_sequence: {val.is_sequence}")
                    print(f"  - name: {val.name}")
                    print(f"  - code: {val.code}")
                    print(f"  - str: {repr(str(val))}")
                    print(f"  - ord: {ord(str(val)) if str(val) else 'N/A'}")
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
    test_alt_keys()