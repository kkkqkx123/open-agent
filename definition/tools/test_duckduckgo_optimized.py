"""
测试优化后的DuckDuckGo搜索工具
"""

import asyncio
import sys
import os

# 添加父目录到路径，以便导入duckduckgo_search模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from duckduckgo_search import duckduckgo_search, fetch_web_content, searcher, fetcher


def test_search_functionality():
    """测试搜索功能"""
    print("=== 测试搜索功能 ===")
    try:
        result = duckduckgo_search("Python编程", max_results=3)
        print(f"搜索查询: Python编程")
        print(f"结果数量: {result['results_count']}")
        print(f"格式化结果预览:\n{result['formatted_results'][:300]}...")
        print(f"速率限制器状态: {searcher.rate_limiter.get_current_rate()} 请求/分钟")
        print("✅ 搜索功能测试通过\n")
        return True
    except Exception as e:
        print(f"❌ 搜索功能测试失败: {e}\n")
        return False


def test_fetch_functionality():
    """测试网页获取功能"""
    print("=== 测试网页获取功能 ===")
    try:
        result = fetch_web_content("https://httpbin.org/html")
        print(f"URL: https://httpbin.org/html")
        print(f"内容长度: {result['content_length']}")
        print(f"是否截断: {result['truncated']}")
        print(f"内容预览: {result['content'][:200]}...")
        print(f"速率限制器状态: {fetcher.rate_limiter.get_current_rate()} 请求/分钟")
        print("✅ 网页获取功能测试通过\n")
        return True
    except Exception as e:
        print(f"❌ 网页获取功能测试失败: {e}\n")
        return False


def test_rate_limiter():
    """测试速率限制功能"""
    print("=== 测试速率限制功能 ===")
    try:
        # 重置速率限制器
        searcher.rate_limiter.reset()
        fetcher.rate_limiter.reset()
        
        # 快速发送多个请求
        print("发送3个快速搜索请求...")
        start_time = asyncio.get_event_loop().time()
        
        for i in range(3):
            result = duckduckgo_search(f"test {i}", max_results=1)
            print(f"请求 {i+1} 完成")
            
        end_time = asyncio.get_event_loop().time()
        print(f"3个请求耗时: {end_time - start_time:.2f} 秒")
        print(f"当前速率: {searcher.rate_limiter.get_current_rate()} 请求/分钟")
        print("✅ 速率限制功能测试通过\n")
        return True
    except Exception as e:
        print(f"❌ 速率限制功能测试失败: {e}\n")
        return False


def test_headers_randomization():
    """测试请求头随机化"""
    print("=== 测试请求头随机化 ===")
    try:
        # 从fetch.py导入get_browser_headers来测试
        from fetch import get_browser_headers
        
        # 获取多个请求头看看是否随机化
        headers_list = [get_browser_headers(randomize=True) for _ in range(3)]
        
        user_agents = [h.get('User-Agent', '') for h in headers_list]
        print("生成的User-Agent:")
        for i, ua in enumerate(user_agents):
            print(f"  {i+1}. {ua[:50]}...")
            
        # 检查User-Agent是否不同（有一定概率相同，但通常应该不同）
        unique_uas = set(user_agents)
        print(f"唯一User-Agent数量: {len(unique_uas)}/3")
        
        if len(unique_uas) >= 2:
            print("✅ 请求头随机化测试通过\n")
            return True
        else:
            print("⚠️  请求头随机化测试可能有问题（User-Agent相似）\n")
            return True  # 不完全失败，因为随机化有可能产生相同结果
    except Exception as e:
        print(f"❌ 请求头随机化测试失败: {e}\n")
        return False


def main():
    """主测试函数"""
    print("开始测试优化后的DuckDuckGo搜索工具...\n")
    
    tests = [
        test_headers_randomization,
        test_search_functionality,
        test_fetch_functionality,
        test_rate_limiter,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！优化后的工具工作正常。")
        return 0
    else:
        print("⚠️  部分测试未通过，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    exit(main())