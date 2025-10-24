"""TUI布局管理器优化效果测试"""

import time
from typing import Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..layout import LayoutManager, LayoutRegion, LayoutConfig, RegionConfig


class LayoutOptimizationTester:
    """布局优化测试器"""
    
    def __init__(self) -> None:
        """初始化测试器"""
        self.console = Console()
        self.test_results = []
    
    def test_content_preservation(self) -> bool:
        """测试内容保持功能"""
        print("🧪 测试内容保持功能...")
        
        try:
            # 创建布局管理器
            manager = LayoutManager()
            manager.create_layout((100, 30))
            
            # 设置测试内容
            test_content = Panel(
                Text("这是测试内容，应该在布局调整后保持不变", style="bold green"),
                title="测试面板",
                border_style="green"
            )
            manager.update_region_content(LayoutRegion.MAIN, test_content)
            
            # 调整尺寸（断点不变）
            manager.resize_layout((110, 35))
            
            # 验证内容是否保持
            preserved_content = manager.region_contents.get(LayoutRegion.MAIN)
            if preserved_content == test_content:
                print("✅ 内容保持测试通过")
                self.test_results.append(("内容保持", True, "相同断点下调整尺寸"))
                return True
            else:
                print("❌ 内容保持测试失败")
                self.test_results.append(("内容保持", False, "内容丢失"))
                return False
                
        except Exception as e:
            print(f"❌ 内容保持测试异常: {e}")
            self.test_results.append(("内容保持", False, f"异常: {e}"))
            return False
    
    def test_breakpoint_transition(self) -> bool:
        """测试断点过渡功能"""
        print("🧪 测试断点过渡功能...")
        
        try:
            # 创建布局管理器
            manager = LayoutManager()
            manager.create_layout((80, 24))  # small断点
            
            # 设置测试内容
            test_content = Panel(
                Text("断点过渡测试内容", style="bold blue"),
                title="断点测试",
                border_style="blue"
            )
            manager.update_region_content(LayoutRegion.HEADER, test_content)
            
            # 记录回调触发次数
            callback_count = 0
            def test_callback(breakpoint: str, terminal_size: Tuple[int, int]) -> None:
                nonlocal callback_count
                callback_count += 1
                print(f"  📞 回调触发: 断点={breakpoint}, 尺寸={terminal_size}")
            
            manager.register_layout_changed_callback(test_callback)
            
            # 调整尺寸触发断点变化
            manager.resize_layout((120, 40))  # large断点
            
            # 验证断点是否正确变化
            if manager.current_breakpoint == "large" and callback_count > 0:
                print("✅ 断点过渡测试通过")
                self.test_results.append(("断点过渡", True, f"回调触发{callback_count}次"))
                return True
            else:
                print("❌ 断点过渡测试失败")
                self.test_results.append(("断点过渡", False, "断点未变化或回调未触发"))
                return False
                
        except Exception as e:
            print(f"❌ 断点过渡测试异常: {e}")
            self.test_results.append(("断点过渡", False, f"异常: {e}"))
            return False
    
    def test_debounce_mechanism(self) -> bool:
        """测试防抖机制"""
        print("🧪 测试防抖机制...")
        
        try:
            # 创建布局管理器
            manager = LayoutManager()
            manager.create_layout((100, 30))
            
            # 记录调整次数
            resize_count = 0
            original_resize = manager.resize_layout
            
            def counting_resize(terminal_size: Tuple[int, int]) -> None:
                nonlocal resize_count
                resize_count += 1
                original_resize(terminal_size)
            
            manager.resize_layout = counting_resize  # type: ignore
            
            # 快速连续调整尺寸
            start_time = time.time()
            for i in range(5):
                manager.resize_layout((100 + i, 30 + i))
                time.sleep(0.02)  # 20ms间隔，小于防抖延迟
            
            # 等待防抖延迟
            time.sleep(0.15)
            
            # 验证防抖效果
            if resize_count < 5:  # 应该少于实际调用次数
                print(f"✅ 防抖机制测试通过 (实际调整{resize_count}次，预期<5次)")
                self.test_results.append(("防抖机制", True, f"防抖有效，{resize_count}次调整"))
                return True
            else:
                print(f"❌ 防抖机制测试失败 (调整{resize_count}次，预期<5次)")
                self.test_results.append(("防抖机制", False, "防抖无效"))
                return False
                
        except Exception as e:
            print(f"❌ 防抖机制测试异常: {e}")
            self.test_results.append(("防抖机制", False, f"异常: {e}"))
            return False
    
    def test_optimal_size_calculation(self) -> bool:
        """测试最优尺寸计算"""
        print("🧪 测试最优尺寸计算...")
        
        try:
            # 创建布局管理器
            manager = LayoutManager()
            
            # 测试不同断点的尺寸计算
            test_cases = [
                ((80, 24), "small"),
                ((100, 30), "medium"),
                ((120, 40), "large"),
                ((140, 50), "xlarge")
            ]
            
            all_passed = True
            for terminal_size, expected_breakpoint in test_cases:
                manager.create_layout(terminal_size)
                actual_breakpoint = manager.get_current_breakpoint()
                
                if actual_breakpoint == expected_breakpoint:
                    print(f"  ✅ {terminal_size} -> {actual_breakpoint}")
                else:
                    print(f"  ❌ {terminal_size} -> {actual_breakpoint} (预期: {expected_breakpoint})")
                    all_passed = False
            
            if all_passed:
                print("✅ 最优尺寸计算测试通过")
                self.test_results.append(("最优尺寸计算", True, "所有断点正确"))
                return True
            else:
                print("❌ 最优尺寸计算测试失败")
                self.test_results.append(("最优尺寸计算", False, "断点计算错误"))
                return False
                
        except Exception as e:
            print(f"❌ 最优尺寸计算测试异常: {e}")
            self.test_results.append(("最优尺寸计算", False, f"异常: {e}"))
            return False
    
    def test_callback_mechanism(self) -> bool:
        """测试回调机制"""
        print("🧪 测试回调机制...")
        
        try:
            # 创建布局管理器
            manager = LayoutManager()
            manager.create_layout((100, 30))
            
            # 测试回调注册和触发
            callback_data = []
            
            def test_callback(breakpoint: str, terminal_size: Tuple[int, int]) -> None:
                callback_data.append((breakpoint, terminal_size))
            
            # 注册回调
            manager.register_layout_changed_callback(test_callback)
            
            # 触发布局变化
            manager.resize_layout((120, 40))
            
            # 验证回调是否被正确触发
            if len(callback_data) > 0:
                breakpoint, terminal_size = callback_data[0]
                if breakpoint == "large" and terminal_size == (120, 40):
                    print("✅ 回调机制测试通过")
                    self.test_results.append(("回调机制", True, "回调正确触发"))
                    return True
            
            print("❌ 回调机制测试失败")
            self.test_results.append(("回调机制", False, "回调未正确触发"))
            return False
                
        except Exception as e:
            print(f"❌ 回调机制测试异常: {e}")
            self.test_results.append(("回调机制", False, f"异常: {e}"))
            return False
    
    def run_all_tests(self) -> None:
        """运行所有测试"""
        print("🚀 开始TUI布局管理器优化效果测试")
        print("=" * 60)
        
        # 运行各项测试
        tests = [
            self.test_content_preservation,
            self.test_breakpoint_transition,
            self.test_debounce_mechanism,
            self.test_optimal_size_calculation,
            self.test_callback_mechanism
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()
        
        # 显示测试结果摘要
        print("=" * 60)
        print(f"📊 测试结果摘要: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！布局管理器优化成功！")
        else:
            print("⚠️  部分测试失败，需要进一步优化")
        
        # 详细结果
        print("\n📋 详细测试结果:")
        for test_name, success, detail in self.test_results:
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}: {detail}")


def main() -> None:
    """主函数"""
    tester = LayoutOptimizationTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()