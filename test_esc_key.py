#!/usr/bin/env python3
"""测试ESC键的处理"""

from blessed import Terminal

def test_esc_key():
    """测试ESC键"""
    terminal = Terminal()
    
    print("测试ESC键处理...")
    print("请按下ESC键退出")
    print("=" * 30)
    
    with terminal.cbreak():
        while True:
            try:
                # 使用blessed的inkey()方法
                val = terminal.inkey(timeout=0.5)
                if val:
                    print(f"按键: {repr(val)}")
                    print(f"  - is_sequence: {val.is_sequence}")
                    print(f"  - name: {val.name}")
                    print(f"  - code: {val.code}")
                    print(f"  - str: {repr(str(val))}")
                    if str(val):
                        print(f"  - ord: {ord(str(val))}")
                    print("-" * 30)
                    
                    # 如果是ESC键，退出
                    if str(val) == '\x1b':
                        print("检测到ESC键，退出测试")
                        break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
                break
    
    print("测试结束")

if __name__ == "__main__":
    test_esc_key()