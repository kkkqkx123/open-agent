#!/usr/bin/env python3
"""测试Windows环境下Alt键和ESC键处理的脚本"""

import sys
import os
import time
from pathlib import Path

# 将项目根目录添加到Python路径中
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from blessed import Terminal


def test_windows_alt_esc_keys():
    """测试Windows环境下Alt键和ESC键的处理"""
    print("Windows环境下Alt键和ESC键处理测试")
    print("请按以下键进行测试:")
    print("1. Alt+1, Alt+2, Alt+3, Alt+4 (测试Alt键)")
    print("2. ESC (测试ESC键)")
    print("3. 按ESC后等待几秒再按1 (应分别处理为ESC键和数字键)")
    print("4. 按 'q' 退出测试")
    print()

    term = Terminal()
    
    with term.cbreak():
        print(f"{term.home}{term.clear}")
        print("开始测试 (按 'q' 退出):")
        
        # 记录上次按键时间
        last_key_time = time.time()
        
        while True:
            # 非阻塞读取按键，超时0.1秒
            val = term.inkey(timeout=0.1)
            
            current_time = time.time()
            
            if not val:
                # 每5秒显示一次提示
                if current_time - last_key_time > 5:
                    print("等待按键输入... (按 'q' 退出)")
                    last_key_time = current_time
                continue
                
            last_key_time = current_time
            
            if val.lower() == 'q':
                print("退出测试")
                break
            elif val == '\x1b':  # ESC键
                print(f"[{time.strftime('%H:%M:%S')}] 检测到ESC键")
            elif val.is_sequence:
                # 特殊键序列
                print(f"[{time.strftime('%H:%M:%S')}] 检测到序列键: {val.name} (code: {val.code})")
            else:
                # 普通字符
                if len(val) == 1 and 128 <= ord(val) <= 255:
                    # 可能是Alt+字符组合
                    original_char = chr(ord(val) - 128)
                    print(f"[{time.strftime('%H:%M:%S')}] 检测到Alt+字符: Alt+{original_char}")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] 检测到字符: {repr(val)}")


if __name__ == "__main__":
    test_windows_alt_esc_keys()