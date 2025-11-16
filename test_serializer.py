"""测试序列化器功能"""

from src.infrastructure.common.serialization.serializer import Serializer

def test_serializer():
    """测试序列化器"""
    serializer = Serializer()
    
    # 测试数据
    test_data = {'message': 'Hello, World!', 'step': 1}
    
    print(f"原始数据: {test_data}")
    
    # 序列化
    serialized = serializer.serialize(test_data, "compact_json")
    print(f"序列化后: {serialized}")
    print(f"序列化类型: {type(serialized)}")
    
    # 反序列化
    deserialized = serializer.deserialize(serialized, "compact_json")
    print(f"反序列化后: {deserialized}")
    print(f"反序列化类型: {type(deserialized)}")
    
    # 验证数据
    assert deserialized == test_data, f"数据不匹配: {deserialized} != {test_data}"
    print("序列化/反序列化测试通过！")

if __name__ == "__main__":
    test_serializer()