"""
DuckDuckGo搜索工具使用示例

演示如何使用DuckDuckGo搜索工具进行实际搜索和获取网页内容。
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import json

# 添加项目根目录到sys.path，以便导入definition.tools.duckduckgo_search
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from definition.tools.duckduckgo_search import (
    duckduckgo_search,
    fetch_web_content,
    SearchResult,
    DuckDuckGoSearcher,
    WebContentFetcher
)


def print_search_results(results: Dict[str, Any]) -> None:
    """打印搜索结果"""
    print(f"\n搜索查询: {results['query']}")
    print(f"结果数量: {results['results_count']}")
    print("\n格式化结果:")
    print("-" * 80)
    print(results['formatted_results'])
    print("-" * 80)


def print_web_content(content_result: Dict[str, Any]) -> None:
    """打印网页内容"""
    print(f"\n网页URL: {content_result['url']}")
    print(f"内容长度: {content_result['content_length']}")
    print(f"是否截断: {content_result['truncated']}")
    print("\n内容预览:")
    print("-" * 80)
    preview = content_result['content'][:500] + "..." if len(content_result['content']) > 500 else content_result['content']
    print(preview)
    print("-" * 80)


def example_basic_search() -> None:
    """基本搜索示例"""
    print("\n" + "=" * 80)
    print("基本搜索示例")
    print("=" * 80)
    
    query = "Python编程语言"
    max_results = 5
    
    try:
        results = duckduckgo_search(query, max_results)
        print_search_results(results)
        
        # 如果有结果，获取第一个结果的网页内容
        if results['raw_results']:
            first_result = results['raw_results'][0]
            print(f"\n获取第一个结果的网页内容: {first_result['title']}")
            content_result = fetch_web_content(first_result['link'])
            print_web_content(content_result)
            
    except ValueError as e:
        print(f"搜索错误: {e}")


def example_multiple_searches() -> None:
    """多次搜索示例"""
    print("\n" + "=" * 80)
    print("多次搜索示例")
    print("=" * 80)
    
    queries = [
        "人工智能最新发展",
        "机器学习算法比较",
        "深度学习框架"
    ]
    
    for query in queries:
        print(f"\n搜索: {query}")
        try:
            results = duckduckgo_search(query, max_results=3)
            print(f"找到 {results['results_count']} 个结果")
            
            # 显示每个结果的标题和链接
            for result in results['raw_results']:
                print(f"  - {result['title']}")
                print(f"    {result['link']}")
                
        except ValueError as e:
            print(f"搜索错误: {e}")


def example_search_with_content_fetch() -> None:
    """搜索并获取内容示例"""
    print("\n" + "=" * 80)
    print("搜索并获取内容示例")
    print("=" * 80)
    
    query = "Python异步编程"
    
    try:
        # 执行搜索
        results = duckduckgo_search(query, max_results=3)
        print_search_results(results)
        
        # 获取前两个结果的网页内容
        if results['raw_results']:
            print("\n获取网页内容:")
            for i, result in enumerate(results['raw_results'][:2]):
                print(f"\n{i+1}. {result['title']}")
                try:
                    content_result = fetch_web_content(result['link'])
                    print(f"   内容长度: {content_result['content_length']} 字符")
                    print(f"   是否截断: {content_result['truncated']}")
                    
                    # 显示内容的前200个字符
                    preview = content_result['content'][:200] + "..." if len(content_result['content']) > 200 else content_result['content']
                    print(f"   内容预览: {preview}")
                    
                except ValueError as e:
                    print(f"   获取内容错误: {e}")
                    
    except ValueError as e:
        print(f"搜索错误: {e}")


def example_error_handling() -> None:
    """错误处理示例"""
    print("\n" + "=" * 80)
    print("错误处理示例")
    print("=" * 80)
    
    # 测试空查询
    print("\n测试空查询:")
    try:
        duckduckgo_search("", max_results=5)
    except ValueError as e:
        print(f"捕获到预期错误: {e}")
    
    # 测试无效的最大结果数
    print("\n测试无效的最大结果数:")
    try:
        duckduckgo_search("Python", max_results=0)
    except ValueError as e:
        print(f"捕获到预期错误: {e}")
    
    # 测试空URL
    print("\n测试空URL:")
    try:
        fetch_web_content("")
    except ValueError as e:
        print(f"捕获到预期错误: {e}")
    
    # 测试无效的URL格式
    print("\n测试无效的URL格式:")
    try:
        fetch_web_content("example.com")
    except ValueError as e:
        print(f"捕获到预期错误: {e}")


def example_save_results_to_file() -> None:
    """保存结果到文件示例"""
    print("\n" + "=" * 80)
    print("保存结果到文件示例")
    print("=" * 80)
    
    query = "Docker容器技术"
    
    try:
        # 执行搜索
        results = duckduckgo_search(query, max_results=5)
        
        # 保存结果到JSON文件
        output_file = Path(__file__).parent / "search_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"搜索结果已保存到: {output_file}")
        print(f"查询: {results['query']}")
        print(f"结果数量: {results['results_count']}")
        
        # 获取第一个结果的网页内容并保存
        if results['raw_results']:
            first_result = results['raw_results'][0]
            content_result = fetch_web_content(first_result['link'])
            
            content_file = Path(__file__).parent / "web_content.txt"
            with open(content_file, "w", encoding="utf-8") as f:
                f.write(f"URL: {content_result['url']}\n")
                f.write(f"内容长度: {content_result['content_length']}\n")
                f.write(f"是否截断: {content_result['truncated']}\n")
                f.write("\n内容:\n")
                f.write(content_result['content'])
            
            print(f"网页内容已保存到: {content_file}")
            
    except ValueError as e:
        print(f"错误: {e}")


def example_custom_searcher() -> None:
    """自定义搜索器示例"""
    print("\n" + "=" * 80)
    print("自定义搜索器示例")
    print("=" * 80)
    
    # 创建自定义搜索器
    searcher = DuckDuckGoSearcher()
    
    # 使用异步方法搜索
    import asyncio
    
    async def async_search():
        query = "异步编程Python"
        results = await searcher.search(query, max_results=3)
        
        # 格式化结果
        formatted = searcher.format_results_for_llm(results)
        print(f"查询: {query}")
        print(formatted)
        
        # 创建内容获取器
        fetcher = WebContentFetcher()
        
        # 获取第一个结果的内容
        if results:
            content = await fetcher.fetch_and_parse(results[0].link)
            print(f"\n内容预览 ({results[0].link}):")
            preview = content[:300] + "..." if len(content) > 300 else content
            print(preview)
    
    # 运行异步搜索
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_search())
    loop.close()


def main():
    """主函数，运行所有示例"""
    print("DuckDuckGo搜索工具使用示例")
    print("=" * 80)
    
    # 运行各种示例
    example_basic_search()
    example_multiple_searches()
    example_search_with_content_fetch()
    example_error_handling()
    example_save_results_to_file()
    example_custom_searcher()
    
    print("\n" + "=" * 80)
    print("所有示例运行完成")
    print("=" * 80)


if __name__ == "__main__":
    main()