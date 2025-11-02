#!/usr/bin/env python3
"""
测试优化后的 fetch.py 请求头功能
"""

import json
from fetch import get_browser_headers, get_random_user_agent, USER_AGENTS

def test_user_agent_rotation():
    """测试 User-Agent 轮换功能"""
    print("=== 测试 User-Agent 轮换功能 ===")
    
    # 测试获取随机 User-Agent
    ua1 = get_random_user_agent()
    ua2 = get_random_user_agent()
    ua3 = get_random_user_agent()
    
    print(f"随机 User-Agent 1: {ua1}")
    print(f"随机 User-Agent 2: {ua2}")
    print(f"随机 User-Agent 3: {ua3}")
    
    # 验证 User-Agent 列表不为空
    print(f"User-Agent 列表长度: {len(USER_AGENTS)}")
    
    # 验证随机性（多次调用应该有不同的结果）
    unique_uas = set()
    for _ in range(10):
        unique_uas.add(get_random_user_agent())
    
    print(f"10次调用中获取到的唯一 User-Agent 数量: {len(unique_uas)}")
    print()

def test_browser_headers():
    """测试浏览器请求头生成功能"""
    print("=== 测试浏览器请求头生成功能 ===")
    
    # 测试默认请求头
    headers1 = get_browser_headers()
    print("默认请求头:")
    print(json.dumps(headers1, indent=2))
    print()
    
    # 测试自定义 User-Agent
    custom_ua = "Mozilla/5.0 (Custom Browser/1.0)"
    headers2 = get_browser_headers(custom_user_agent=custom_ua)
    print("自定义 User-Agent 请求头:")
    print(json.dumps(headers2, indent=2))
    print()
    
    # 测试带 Referer 的请求头
    headers3 = get_browser_headers(referer_url="https://example.com")
    print("带 Referer 的请求头:")
    print(json.dumps(headers3, indent=2))
    print()
    
    # 测试不随机化的请求头
    headers4 = get_browser_headers(randomize=False)
    print("不随机化的请求头:")
    print(json.dumps(headers4, indent=2))
    print()
    
    # 测试多次生成的请求头差异
    print("=== 测试请求头随机化差异 ===")
    headers_list = []
    for i in range(3):
        headers = get_browser_headers()
        headers_list.append(headers)
        print(f"请求头 {i+1}:")
        print(f"  User-Agent: {headers['User-Agent']}")
        print(f"  DNT: {headers.get('DNT', 'Not present')}")
        print(f"  Sec-GPC: {headers.get('Sec-GPC', 'Not present')}")
        print(f"  Save-Data: {headers.get('Save-Data', 'Not present')}")
        print()

def test_sec_fetch_headers():
    """测试 Sec-Fetch-* 头部"""
    print("=== 测试 Sec-Fetch-* 头部 ===")
    headers = get_browser_headers()
    
    sec_fetch_headers = {k: v for k, v in headers.items() if k.startswith('Sec-Fetch-')}
    print("Sec-Fetch-* 头部:")
    for header, value in sec_fetch_headers.items():
        print(f"  {header}: {value}")
    print()

if __name__ == "__main__":
    print("开始测试优化后的 fetch.py 请求头功能\n")
    
    test_user_agent_rotation()
    test_browser_headers()
    test_sec_fetch_headers()
    
    print("测试完成！")