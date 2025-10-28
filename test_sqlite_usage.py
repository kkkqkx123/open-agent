"""测试LangGraph的SqliteSaver用法"""

from langgraph.checkpoint.sqlite import SqliteSaver
import asyncio

async def test_sqlite_usage():
    """测试SqliteSaver的正确用法"""
    print("=== 测试LangGraph的SqliteSaver用法 ===")
    
    # 创建SqliteSaver实例
    checkpointer = SqliteSaver.from_conn_string(":memory:")
    
    # 测试配置
    config = {"configurable": {"thread_id": "test_thread", "checkpoint_ns": ""}}
    
    # 创建一个简单的checkpoint
    checkpoint = {
        "v": 4,
        "ts": "2025-10-28T01:26:44.670Z",
        "id": "test_checkpoint_id",
        "channel_values": {
            "__root__": {"history": [0, 1, 2], "step": 1}
        },
        "channel_versions": {
            "__root__": 1
        },
        "versions_seen": {
            "__root__": {"__start__": 1}
        }
    }
    
    metadata = {"test": True, "step": 1}
    
    print("1. 测试上下文管理器用法...")
    try:
        # 尝试使用上下文管理器
        with checkpointer as checkpointer_ctx:
            print(f"Context manager type: {type(checkpointer_ctx)}")
            print(f"Context manager attributes: {dir(checkpointer_ctx)}")
            
            # 检查可用方法
            if hasattr(checkpointer_ctx, 'put'):
                print("Has put method")
            else:
                print("No put method")
                
            if hasattr(checkpointer_ctx, 'get'):
                print("Has get method")
            else:
                print("No get method")
                
            if hasattr(checkpointer_ctx, 'list'):
                print("Has list method")
            else:
                print("No list method")
                
            # 尝试保存
            try:
                result = checkpointer_ctx.put(config, checkpoint, metadata, {})
                print(f"put result: {result}")
                print("put操作成功")
            except Exception as e:
                print(f"put操作失败: {e}")
                
            # 尝试列出
            try:
                list_result = list(checkpointer_ctx.list(config))
                print(f"list result: {list_result}")
                print(f"list result type: {type(list_result)}")
                if list_result:
                    print(f"first item type: {type(list_result[0])}")
                    if hasattr(list_result[0], '__dict__'):
                        print(f"first item dict: {list_result[0].__dict__}")
                print("list操作成功")
            except Exception as e:
                print(f"list操作失败: {e}")
                
    except Exception as e:
        print(f"上下文管理器使用失败: {e}")
    
    print("\n2. 测试直接使用checkpointer...")
    try:
        # 直接使用checkpointer
        print(f"Direct checkpointer type: {type(checkpointer)}")
        print(f"Direct checkpointer attributes: {dir(checkpointer)}")
        
        # 尝试保存
        try:
            result = checkpointer.put(config, checkpoint, metadata, {})
            print(f"Direct put result: {result}")
            print("直接put操作成功")
        except Exception as e:
            print(f"直接put操作失败: {e}")
            
        # 尝试列出
        try:
            list_result = list(checkpointer.list(config))
            print(f"Direct list result: {list_result}")
            print(f"Direct list result type: {type(list_result)}")
            if list_result:
                print(f"first item type: {type(list_result[0])}")
                if hasattr(list_result[0], '__dict__'):
                    print(f"first item dict: {list_result[0].__dict__}")
                elif hasattr(list_result[0], 'checkpoint'):
                    print(f"first item has checkpoint attr: {hasattr(list_result[0], 'checkpoint')}")
                    print(f"first item has metadata attr: {hasattr(list_result[0], 'metadata')}")
                    if hasattr(list_result[0], 'checkpoint'):
                        print(f"checkpoint type: {type(list_result[0].checkpoint)}")
                        print(f"metadata type: {type(list_result[0].metadata)}")
            print("直接list操作成功")
        except Exception as e:
            print(f"直接list操作失败: {e}")
            
    except Exception as e:
        print(f"直接使用checkpointer失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_sqlite_usage())