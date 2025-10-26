#!/usr/bin/env python3
"""调试历史存储问题"""

import sys
import tempfile
import traceback
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.domain.history.models import MessageRecord, ToolCallRecord, MessageType
from src.infrastructure.history.storage.file_storage import FileHistoryStorage

def main():
    """主函数"""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        
        # 使用模拟日期来确保一致性
        with patch('src.infrastructure.history.storage.file_storage.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "202310"
            storage = FileHistoryStorage(base_path)
            
            # 测试消息记录
            print("=== 测试消息记录存储 ===")
            record = MessageRecord(
                record_id="msg-1",
                session_id="test-session",
                timestamp=datetime(2023, 10, 25, 12, 0, 0),
                message_type=MessageType.USER,
                content="测试消息",
                metadata={"source": "test"}
            )
            
            # 直接调用存储方法内部的逻辑来查看异常
            try:
                session_file = storage._get_session_file("test-session")
                print(f"会话文件路径: {session_file}")
                
                # 尝试手动序列化
                def custom_serializer(obj):
                    if hasattr(obj, 'value'):  # 枚举类型
                        return obj.value
                    elif isinstance(obj, datetime):  # datetime类型
                        return obj.isoformat()
                    return str(obj)
                
                serialized = json.dumps(record.__dict__, ensure_ascii=False, default=custom_serializer)
                print(f"序列化结果: {serialized}")
                
                # 尝试写入文件
                with open(session_file, 'a', encoding='utf-8') as f:
                    f.write(serialized)
                    f.write('\n')
                print("手动写入成功")
                
                # 现在尝试使用原始方法
                result = storage.store_record(record)
                print(f"存储结果: {result}")
                
                # 检查文件是否存在
                print(f"文件是否存在: {session_file.exists()}")
                
                if session_file.exists():
                    with open(session_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"文件内容: {content}")
            except Exception as e:
                print(f"异常: {e}")
                traceback.print_exc()
            
            # 测试工具调用记录
            print("\n=== 测试工具调用记录存储 ===")
            tool_record = ToolCallRecord(
                record_id="tool-1",
                session_id="test-session",
                timestamp=datetime(2023, 10, 25, 12, 0, 0),
                tool_name="test_tool",
                tool_input={"param1": "value1", "param2": 123},
                tool_output={"result": "success"},
                metadata={"execution_time": 1.5}
            )
            
            try:
                result = storage.store_record(tool_record)
                print(f"存储结果: {result}")
            except Exception as e:
                print(f"异常: {e}")
                traceback.print_exc()

if __name__ == "__main__":
    main()