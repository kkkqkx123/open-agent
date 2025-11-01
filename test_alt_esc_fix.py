#!/usr/bin/env python3
"""测试Alt键和ESC键处理修复的脚本"""

import sys
import os
import time
from pathlib import Path

# 将项目根目录添加到Python路径中
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from blessed import Terminal


def test_alt_esc_keys():
    """测试Alt键和ESC键的处理"""
    print("测试Alt键和ESC键处理...")
    print("请按以下键进行测试:")
    print("1. Alt+1, Alt+2, Alt+3, Alt+4 (测试Alt键)")
    print("2. ESC (测试ESC键)")
    print("3. 按 'q' 退出测试")
    print()

    term = Terminal()
    
    with term.cbreak():
        print(f"{term.home}{term.clear}")
        print("开始测试 (按 'q' 退出):")
        
        while True:
            # 非阻塞读取按键，超时1秒
            val = term.inkey(timeout=1)
            
            if not val:
                continue
                
            if val.lower() == 'q':
                print("退出测试")
                break
            elif val == '\x1b':  # ESC键
                print("检测到ESC键")
            elif val.is_sequence:
                # 特殊键序列
                print(f"检测到序列键: {val.name} (code: {val.code})")
            else:
                # 普通字符
                if len(val) == 1 and 128 <= ord(val) <= 255:
                    # 可能是Alt+字符组合
                    original_char = chr(ord(val) - 128)
                    print(f"检测到Alt+字符: Alt+{original_char}")
                else:
                    print(f"检测到字符: {repr(val)}")


if __name__ == "__main__":
    test_alt_esc_keys()