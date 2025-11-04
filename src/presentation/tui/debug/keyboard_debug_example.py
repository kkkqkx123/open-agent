#!/usr/bin/env python3
"""
键盘调试示例

演示如何使用新的键盘调试功能，包括SequenceMonitor和增强配置。
"""

import sys
import os
import time
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.presentation.tui.event_engine import EventEngine
from src.presentation.tui.config import TUIConfig, KeyboardConfig
from src.presentation.tui.key import Key


class KeyboardDebugDemo:
    """键盘调试演示类"""
    
    def __init__(self):
        self.engine: Optional[EventEngine] = None
        self.config = self._create_debug_config()
        
    def _create_debug_config(self) -> TUIConfig:
        """创建调试配置"""
        # 创建基础配置
        config = TUIConfig()
        
        # 配置键盘调试选项
        config.keyboard = KeyboardConfig(
            enhanced_key_support=True,          # 启用增强按键支持
            debug_key_sequences=True,         # 启用按键序列调试
            kitty_keyboard_protocol=False,    # 禁用Kitty协议（可选）
            key_mappings={                    # 自定义按键映射
                'ctrl+q': 'quit',
                'ctrl+d': 'debug_info',
                'ctrl+s': 'save_sequences'
            }
        )
        
        return config
    
    def setup_engine(self) -> bool:
        """设置事件引擎"""
        try:
            self.engine = EventEngine(self.config.to_dict())
            
            # 注册调试处理器
            self.engine.register_handler('debug_info', self._show_debug_info)
            self.engine.register_handler('save_sequences', self._save_sequences)
            
            return True
        except Exception as e:
            print(f"设置事件引擎失败: {e}")
            return False
    
    def _show_debug_info(self, key: Key) -> None:
        """显示调试信息"""
        print("\n" + "="*50)
        print("键盘调试信息:")
        print("="*50)
        
        # 显示基本统计
        stats = self.engine.get_statistics()
        print(f"总按键数: {stats['total_keys']}")
        print(f"序列检测: {stats['sequence_detected']}")
        print(f"Alt组合: {stats['alt_combinations']}")
        print(f"错误数: {stats['errors']}")
        
        # 显示序列统计
        if 'sequence_stats' in stats:
            seq_stats = stats['sequence_stats']
            print(f"\n序列统计:")
            print(f"  总序列数: {seq_stats['total_sequences']}")
            print(f"  唯一序列数: {seq_stats['unique_sequences']}")
            print(f"  最近序列数: {len(seq_stats['recent_sequences'])}")
        
        print("="*50)
    
    def _save_sequences(self, key: Key) -> None:
        """保存按键序列"""
        if self.engine and self.engine.sequence_monitor:
            filename = f"key_sequences_{int(time.time())}.json"
            self.engine.sequence_monitor.save_to_file(filename)
            print(f"按键序列已保存到: {filename}")
    
    def run_demo(self) -> None:
        """运行调试演示"""
        if not self.setup_engine():
            return
        
        print("键盘调试演示")
        print("="*50)
        print("使用方法:")
        print("  Ctrl+D - 显示调试信息")
        print("  Ctrl+S - 保存按键序列")
        print("  Ctrl+Q - 退出")
        print("  其他按键 - 正常输入，会被记录")
        print("="*50)
        print("开始输入按键...")
        
        try:
            # 启动事件引擎
            self.engine.start()
            
            # 等待用户操作
            while self.engine.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n用户中断")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        if self.engine:
            self.engine.stop()
            print("\n调试演示结束")


def create_simple_debug_script():
    """创建简单的调试脚本"""
    script_content = '''#!/usr/bin/env python3
"""
简单的键盘调试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_engine import EventEngine
from config import TUIConfig

def main():
    """主函数"""
    # 创建配置
    config = TUIConfig()
    config.keyboard.debug_key_sequences = True
    
    # 创建事件引擎
    engine = EventEngine(config.to_dict())
    
    print("简单键盘调试")
    print("按键将被记录，按Ctrl+C退出")
    
    try:
        engine.start()
        
        # 简单的按键统计
        import time
        while True:
            stats = engine.get_statistics()
            print(f"按键: {stats['total_keys']}, 序列: {stats['sequence_detected']}", end='\r')
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        print("\\n调试结束")

if __name__ == "__main__":
    main()
'''
    
    return script_content


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--simple':
        # 创建简单调试脚本
        script = create_simple_debug_script()
        with open('simple_keyboard_debug.py', 'w', encoding='utf-8') as f:
            f.write(script)
        print("已创建简单调试脚本: simple_keyboard_debug.py")
        print("运行: python simple_keyboard_debug.py")
    else:
        # 运行完整演示
        demo = KeyboardDebugDemo()
        demo.run_demo()


if __name__ == "__main__":
    main()