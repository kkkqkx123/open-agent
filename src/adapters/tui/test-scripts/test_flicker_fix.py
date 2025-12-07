"""测试TUI闪烁问题修复"""

import time
from typing import Tuple
from unittest.mock import Mock, MagicMock

from ..layout import LayoutManager, LayoutRegion
from ..render_controller import RenderController
from ..config import get_tui_config


class FlickerTestHelper:
    """闪烁测试辅助类"""
    
    def __init__(self):
        self.config = get_tui_config()
        self.refresh_count = 0
        self.layout_changes = 0
    
    def create_mock_components(self):
        """创建模拟组件"""
        return {
            "sidebar": Mock(),
            "workflow": Mock(),
            "main_content": Mock(),
            "input": Mock(),
            "session_dialog": Mock(),
            "agent_dialog": Mock()
        }
    
    def create_mock_subviews(self):
        """创建模拟子界面"""
        return {
            "analytics": Mock(),
            "visualization": Mock(),
            "system": Mock(),
            "errors": Mock()
        }
    
    def create_mock_live(self):
        """创建模拟Live对象"""
        mock_live = Mock()
        mock_live.refresh = Mock(side_effect=self._count_refresh)
        return mock_live
    
    def _count_refresh(self):
        """计数刷新次数"""
        self.refresh_count += 1
    
    def test_layout_change_refresh_behavior(self) -> bool:
        """测试布局变化时的刷新行为"""
        print("🧪 测试布局变化时的刷新行为...")
        
        # 创建布局管理器
        layout_manager = LayoutManager()
        
        # 创建渲染控制器
        components = self.create_mock_components()
        subviews = self.create_mock_subviews()
        render_controller = RenderController(layout_manager, components, subviews, self.config)
        
        # 设置模拟Live对象
        mock_live = self.create_mock_live()
        render_controller.set_live(mock_live)
        
        # 重置计数器
        self.refresh_count = 0
        self.layout_changes = 0
        
        # 注册布局变化回调来计数
        def count_layout_change(breakpoint: str, terminal_size: Tuple[int, int]):
            self.layout_changes += 1
        
        layout_manager.register_layout_changed_callback(count_layout_change)
        
        # 模拟多次布局调整
        print("  模拟布局调整...")
        for i in range(5):
            layout_manager.resize_layout((100 + i * 5, 30 + i * 2))
            time.sleep(0.01)  # 短暂延迟
        
        # 模拟主循环的UI更新
        print("  模拟主循环UI更新...")
        for i in range(10):
            mock_state_manager = Mock()
            mock_state_manager.current_subview = None
            mock_state_manager.show_session_dialog = False
            mock_state_manager.show_agent_dialog = False
            
            render_controller.update_ui(mock_state_manager)
            time.sleep(0.01)
        
        print(f"  布局变化次数: {self.layout_changes}")
        print(f"  刷新次数: {self.refresh_count}")
        
        # 验证刷新次数是否合理（应该远少于调用次数）
        if self.refresh_count <= 3:  # 期望刷新次数较少
            print("✅ 刷新行为正常，无过度刷新")
            return True
        else:
            print("❌ 存在过度刷新问题")
            return False
    
    def test_large_terminal_performance(self) -> bool:
        """测试大尺寸终端性能"""
        print("🧪 测试大尺寸终端性能...")
        
        # 创建布局管理器
        layout_manager = LayoutManager()
        
        # 创建渲染控制器
        components = self.create_mock_components()
        subviews = self.create_mock_subviews()
        render_controller = RenderController(layout_manager, components, subviews, self.config)
        
        # 设置模拟Live对象
        mock_live = self.create_mock_live()
        render_controller.set_live(mock_live)
        
        # 重置计数器
        self.refresh_count = 0
        
        # 测试大尺寸终端的布局调整
        large_sizes = [(140, 50), (160, 60), (180, 70)]
        
        start_time = time.time()
        
        for size in large_sizes:
            print(f"  测试尺寸: {size}")
            layout_manager.resize_layout(size)
            
            # 模拟几次UI更新
            for _ in range(3):
                mock_state_manager = Mock()
                mock_state_manager.current_subview = None
                mock_state_manager.show_session_dialog = False
                mock_state_manager.show_agent_dialog = False
                
                render_controller.update_ui(mock_state_manager)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"  总耗时: {duration:.3f}秒")
        print(f"  刷新次数: {self.refresh_count}")
        
        # 验证性能是否合理
        if duration < 0.5 and self.refresh_count <= 5:
            print("✅ 大尺寸终端性能正常")
            return True
        else:
            print("❌ 大尺寸终端性能存在问题")
            return False
    
    def test_refresh_flag_mechanism(self) -> bool:
        """测试刷新标记机制"""
        print("🧪 测试刷新标记机制...")
        
        # 创建布局管理器
        layout_manager = LayoutManager()
        
        # 创建渲染控制器
        components = self.create_mock_components()
        subviews = self.create_mock_subviews()
        render_controller = RenderController(layout_manager, components, subviews, self.config)
        
        # 设置模拟Live对象
        mock_live = self.create_mock_live()
        render_controller.set_live(mock_live)
        
        # 重置计数器
        self.refresh_count = 0
        
        # 测试刷新标记机制
        print("  测试布局变化触发刷新标记...")
        layout_manager.resize_layout((120, 40))  # 触发布局变化
        
        # 多次调用update_ui，应该只刷新一次
        print("  多次调用update_ui...")
        mock_state_manager = Mock()
        mock_state_manager.current_subview = None
        mock_state_manager.show_session_dialog = False
        mock_state_manager.show_agent_dialog = False
        
        for i in range(5):
            render_controller.update_ui(mock_state_manager)
            if render_controller._needs_refresh:
                print(f"    第{i+1}次调用: 需要刷新")
            else:
                print(f"    第{i+1}次调用: 无需刷新")
        
        print(f"  实际刷新次数: {self.refresh_count}")
        
        # 验证刷新标记机制是否有效
        if self.refresh_count == 1:
            print("✅ 刷新标记机制工作正常")
            return True
        else:
            print("❌ 刷新标记机制存在问题")
            return False
    
    def run_all_tests(self) -> None:
        """运行所有测试"""
        print("🚀 开始TUI闪烁问题修复测试")
        print("=" * 50)
        
        tests = [
            self.test_layout_change_refresh_behavior,
            self.test_large_terminal_performance,
            self.test_refresh_flag_mechanism
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                print()
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                print()
        
        # 显示测试结果摘要
        print("=" * 50)
        print(f"📊 测试结果摘要: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！闪烁问题已修复！")
        else:
            print("⚠️  部分测试失败，需要进一步调试")


def main() -> None:
    """主函数"""
    tester = FlickerTestHelper()
    tester.run_all_tests()


if __name__ == "__main__":
    main()