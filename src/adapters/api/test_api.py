"""API测试脚本"""
import asyncio
import json
import aiohttp
from datetime import datetime


async def test_api():
    """测试API功能"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("开始测试API...")
        
        # 测试根路径
        print("\n1. 测试根路径")
        async with session.get(f"{base_url}/") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ 根路径测试成功: {data['message']}")
            else:
                print(f"✗ 根路径测试失败: {response.status}")
        
        # 测试健康检查
        print("\n2. 测试健康检查")
        async with session.get(f"{base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ 健康检查成功: {data['message']}")
            else:
                print(f"✗ 健康检查失败: {response.status}")
        
        # 测试会话列表
        print("\n3. 测试会话列表")
        async with session.get(f"{base_url}/sessions/") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ 会话列表测试成功: 找到 {data['total']} 个会话")
            else:
                print(f"✗ 会话列表测试失败: {response.status}")
        
        # 测试工作流列表
        print("\n4. 测试工作流列表")
        async with session.get(f"{base_url}/workflows/") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ 工作流列表测试成功: 找到 {data['total']} 个工作流")
            else:
                print(f"✗ 工作流列表测试失败: {response.status}")
        
        # 测试创建会话
        print("\n5. 测试创建会话")
        session_data = {
            "workflow_config_path": "configs/workflows/react.yaml",
            "agent_config": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7
            },
            "initial_state": {
                "messages": [],
                "tool_results": []
            }
        }
        
        async with session.post(
            f"{base_url}/sessions/",
            json=session_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                session_id = data["session_id"]
                print(f"✓ 创建会话成功: {session_id}")
                
                # 测试获取会话详情
                print("\n6. 测试获取会话详情")
                async with session.get(f"{base_url}/sessions/{session_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✓ 获取会话详情成功: {data['status']}")
                    else:
                        print(f"✗ 获取会话详情失败: {response.status}")
                
                # 测试更新会话
                print("\n7. 测试更新会话")
                update_data = {
                    "status": "paused",
                    "metadata": {
                        "notes": "测试暂停"
                    }
                }
                
                async with session.put(
                    f"{base_url}/sessions/{session_id}",
                    json=update_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✓ 更新会话成功: {data['status']}")
                    else:
                        print(f"✗ 更新会话失败: {response.status}")
                
                # 测试删除会话
                print("\n8. 测试删除会话")
                async with session.delete(f"{base_url}/sessions/{session_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✓ 删除会话成功: {data['message']}")
                    else:
                        print(f"✗ 删除会话失败: {response.status}")
            else:
                error_data = await response.json()
                print(f"✗ 创建会话失败: {response.status} - {error_data.get('detail', '未知错误')}")
        
        # 测试分析统计
        print("\n9. 测试分析统计")
        async with session.get(f"{base_url}/analytics/performance") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ 性能指标测试成功: 平均响应时间 {data['avg_response_time']:.2f}ms")
            else:
                print(f"✗ 性能指标测试失败: {response.status}")
        
        # 测试WebSocket连接
        print("\n10. 测试WebSocket连接")
        try:
            async with session.ws_connect(f"{base_url}/ws/test_client") as ws:
                # 发送ping消息
                await ws.send_str(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }))
                
                # 接收响应
                response = await ws.receive_str()
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    print("✓ WebSocket连接测试成功")
                else:
                    print(f"✗ WebSocket响应异常: {data}")
        except Exception as e:
            print(f"✗ WebSocket连接测试失败: {e}")
        
        print("\nAPI测试完成!")


if __name__ == "__main__":
    print("请确保API服务器正在运行 (python -m src.presentation.api.run_api)")
    print("等待3秒后开始测试...")
    
    import time
    time.sleep(3)
    
    asyncio.run(test_api())