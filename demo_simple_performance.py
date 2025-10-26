"""简化的状态序列化性能演示

演示增强的状态序列化器的性能改进。
"""

import time
import json
import statistics
from typing import Dict, Any, List

# 直接导入我们实现的模块
from src.infrastructure.graph.states.serializer import StateSerializer


def create_test_states() -> List[Dict[str, Any]]:
    """创建测试状态数据"""
    states = []
    
    # 创建不同大小的状态
    for i in range(3):
        # 基础状态
        base_state = {
            "messages": [{"content": f"Test message {j}", "type": "human"} for j in range(10 * (i + 1))],
            "current_step": f"step_{i}",
            "metadata": {"test": True, "index": i}
        }
        
        # Agent状态
        agent_state = {
            "input": f"Test input {i}",
            "output": None,
            "agent_id": f"agent_{i}",
            "agent_config": {"max_iterations": 10},
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "execution_result": None
        }
        
        # Workflow状态
        workflow_state = {
            "workflow_id": f"workflow_{i}",
            "workflow_name": f"Test Workflow {i}",
            "input_text": f"Test workflow input {i}",
            "workflow_config": {"test": True},
            "current_graph": "",
            "current_step": None,
            "analysis": None,
            "decision": None,
            "context": {},
            "start_time": None,
            "end_time": None,
            "graph_states": {},
            "custom_fields": {}
        }
        
        states.extend([base_state, agent_state, workflow_state])
    
    return states


def test_serialization_performance():
    """测试序列化性能"""
    print("=== 状态序列化性能测试 ===")
    
    # 创建测试数据
    test_states = create_test_states()
    
    # 创建序列化器
    basic_serializer = StateSerializer(max_cache_size=0)  # 禁用缓存
    enhanced_serializer = StateSerializer(max_cache_size=1000)  # 启用缓存
    
    print(f"测试状态数量: {len(test_states)}")
    
    # 测试基本序列化器
    print("\n1. 基本序列化器性能测试")
    basic_times = []
    for i, state in enumerate(test_states):
        start_time = time.time()
        serialized = basic_serializer.serialize(state, enable_cache=False)
        end_time = time.time()
        basic_times.append(end_time - start_time)
        
        if i < 3:  # 只显示前几个
            print(f"  状态 {i+1} 序列化时间: {end_time - start_time:.6f}s")
    
    # 测试增强序列化器（无缓存）
    print("\n2. 增强序列化器（无缓存）性能测试")
    enhanced_no_cache_times = []
    for i, state in enumerate(test_states):
        start_time = time.time()
        serialized = enhanced_serializer.serialize(state, enable_cache=False)
        end_time = time.time()
        enhanced_no_cache_times.append(end_time - start_time)
        
        if i < 3:  # 只显示前几个
            print(f"  状态 {i+1} 序列化时间: {end_time - start_time:.6f}s")
    
    # 测试增强序列化器（有缓存）
    print("\n3. 增强序列化器（有缓存）性能测试")
    
    # 第一次（缓存未命中）
    enhanced_cache_times_1 = []
    for i, state in enumerate(test_states):
        start_time = time.time()
        serialized = enhanced_serializer.serialize(state, enable_cache=True)
        end_time = time.time()
        enhanced_cache_times_1.append(end_time - start_time)
    
    # 第二次（缓存命中）
    enhanced_cache_times_2 = []
    for i, state in enumerate(test_states):
        start_time = time.time()
        serialized = enhanced_serializer.serialize(state, enable_cache=True)
        end_time = time.time()
        enhanced_cache_times_2.append(end_time - start_time)
    
    print(f"  第一次平均时间（缓存未命中）: {statistics.mean(enhanced_cache_times_1):.6f}s")
    print(f"  第二次平均时间（缓存命中）: {statistics.mean(enhanced_cache_times_2):.6f}s")
    
    # 计算统计
    basic_avg = statistics.mean(basic_times)
    enhanced_no_cache_avg = statistics.mean(enhanced_no_cache_times)
    enhanced_cache_avg_2 = statistics.mean(enhanced_cache_times_2)
    
    print(f"\n性能统计:")
    print(f"  基本序列化器平均时间: {basic_avg:.6f}s")
    print(f"  增强序列化器（无缓存）平均时间: {enhanced_no_cache_avg:.6f}s")
    print(f"  增强序列化器（缓存命中）平均时间: {enhanced_cache_avg_2:.6f}s")
    
    # 计算性能提升
    if basic_avg > 0:
        improvement_no_cache = (basic_avg - enhanced_no_cache_avg) / basic_avg * 100
        improvement_cache_hit = (basic_avg - enhanced_cache_avg_2) / basic_avg * 100
        
        print(f"\n性能提升:")
        print(f"  无缓存性能提升: {improvement_no_cache:.2f}%")
        print(f"  缓存命中性能提升: {improvement_cache_hit:.2f}%")
    
    # 验证正确性
    print("\n4. 正确性验证")
    for state in test_states[:2]:  # 测试前2个状态
        basic_result = basic_serializer.serialize(state, enable_cache=False)
        enhanced_result = enhanced_serializer.serialize(state, enable_cache=False)
        
        # 反序列化后比较
        basic_restored = basic_serializer.deserialize(basic_result)
        enhanced_restored = enhanced_serializer.deserialize(enhanced_result)
        
        if basic_restored == enhanced_restored:
            print(f"  ✓ 状态正确性验证通过")
        else:
            print(f"  ✗ 状态正确性验证失败")
    
    return {
        "basic_avg": basic_avg,
        "enhanced_no_cache_avg": enhanced_no_cache_avg,
        "enhanced_cache_avg": enhanced_cache_avg_2,
        "improvement_no_cache": improvement_no_cache if basic_avg > 0 else 0,
        "improvement_cache_hit": improvement_cache_hit if basic_avg > 0 else 0
    }


def test_diff_serialization_performance():
    """测试差异序列化性能"""
    print("\n=== 差异序列化性能测试 ===")
    
    # 创建状态序列
    base_state = {
        "workflow_id": "diff_test",
        "workflow_name": "Diff Test Workflow",
        "input_text": "Test input",
        "messages": [{"content": "Initial message", "type": "human"}],
        "current_step": "start",
        "iteration_count": 0
    }
    
    state_sequence = [base_state.copy()]
    
    # 创建一系列状态更新
    for i in range(5):
        new_state = state_sequence[-1].copy()
        # 添加消息
        new_state["messages"].append({"content": f"New message {i}", "type": "ai"})
        # 更新其他字段
        new_state["current_step"] = f"step_{i}"
        new_state["iteration_count"] = i
        
        state_sequence.append(new_state)
    
    print(f"创建了 {len(state_sequence)} 个状态")
    
    # 测试完整序列化
    print("\n1. 完整序列化性能")
    full_times = []
    full_sizes = []
    for state in state_sequence[1:]:
        start_time = time.time()
        serialized = enhanced_serializer.serialize(state, enable_cache=False)
        end_time = time.time()
        full_times.append(end_time - start_time)
        full_sizes.append(len(serialized) if isinstance(serialized, str) else len(serialized))
    
    # 测试差异序列化
    print("\n2. 差异序列化性能")
    diff_times = []
    diff_sizes = []
    for i in range(1, len(state_sequence)):
        old_state = state_sequence[i-1]
        new_state = state_sequence[i]
        
        start_time = time.time()
        diff_serialized = enhanced_serializer.serialize_diff(old_state, new_state)
        end_time = time.time()
        diff_times.append(end_time - start_time)
        diff_sizes.append(len(diff_serialized) if isinstance(diff_serialized, str) else len(diff_serialized))
    
    # 计算统计
    full_avg_time = statistics.mean(full_times)
    diff_avg_time = statistics.mean(diff_times)
    full_avg_size = statistics.mean(full_sizes)
    diff_avg_size = statistics.mean(diff_sizes)
    
    print(f"\n差异序列化统计:")
    print(f"  完整序列化平均时间: {full_avg_time:.6f}s")
    print(f"  差异序列化平均时间: {diff_avg_time:.6f}s")
    print(f"  完整序列化平均大小: {full_avg_size:.0f} bytes")
    print(f"  差异序列化平均大小: {diff_avg_size:.0f} bytes")
    
    if full_avg_time > 0:
        time_improvement = (full_avg_time - diff_avg_time) / full_avg_time * 100
        size_improvement = (full_avg_size - diff_avg_size) / full_avg_size * 100
        
        print(f"  差异序列化时间提升: {time_improvement:.2f}%")
        print(f"  差异序列化大小提升: {size_improvement:.2f}%")
    
    # 验证差异序列化的正确性
    print("\n3. 差异序列化正确性验证")
    for i in range(1, len(state_sequence)):
        old_state = state_sequence[i-1]
        new_state = state_sequence[i]
        
        # 序列化差异
        diff_serialized = enhanced_serializer.serialize_diff(old_state, new_state)
        
        # 应用差异
        restored_state = enhanced_serializer.apply_diff(old_state, diff_serialized)
        
        if restored_state == new_state:
            print(f"  ✓ 差异序列化验证通过 (步骤 {i})")
        else:
            print(f"  ✗ 差异序列化验证失败 (步骤 {i})")
    
    return {
        "full_avg_time": full_avg_time,
        "diff_avg_time": diff_avg_time,
        "full_avg_size": full_avg_size,
        "diff_avg_size": diff_avg_size,
        "time_improvement": time_improvement if full_avg_time > 0 else 0,
        "size_improvement": size_improvement if full_avg_size > 0 else 0
    }


def test_cache_performance():
    """测试缓存性能"""
    print("\n=== 缓存性能测试 ===")
    
    # 创建测试状态
    test_state = {
        "workflow_id": "cache_test",
        "workflow_name": "Cache Test Workflow",
        "input_text": "Test input",
        "messages": [{"content": "Test message", "type": "human"}],
        "current_step": "start"
    }
    
    # 测试缓存命中率
    print("1. 缓存命中率测试")
    
    # 第一次序列化（缓存未命中）
    start_time = time.time()
    result1 = enhanced_serializer.serialize(test_state, enable_cache=True)
    time1 = time.time() - start_time
    
    # 第二次序列化（缓存命中）
    start_time = time.time()
    result2 = enhanced_serializer.serialize(test_state, enable_cache=True)
    time2 = time.time() - start_time
    
    # 第三次序列化（缓存命中）
    start_time = time.time()
    result3 = enhanced_serializer.serialize(test_state, enable_cache=True)
    time3 = time.time() - start_time
    
    print(f"  第一次序列化时间（缓存未命中）: {time1:.6f}s")
    print(f"  第二次序列化时间（缓存命中）: {time2:.6f}s")
    print(f"  第三次序列化时间（缓存命中）: {time3:.6f}s")
    
    # 验证结果一致性
    if result1 == result2 == result3:
        print("  ✓ 缓存一致性验证通过")
    else:
        print("  ✗ 缓存一致性验证失败")
    
    # 获取缓存统计
    print("\n2. 缓存统计")
    stats = enhanced_serializer.get_performance_stats()
    cache_stats = stats['cache_stats']
    
    print(f"  缓存命中次数: {cache_stats['hits']}")
    print(f"  缓存未命中次数: {cache_stats['misses']}")
    print(f"  缓存命中率: {cache_stats['hit_rate']}")
    print(f"  缓存大小: {cache_stats['cache_size']}")
    
    return {
        "first_time": time1,
        "second_time": time2,
        "third_time": time3,
        "cache_hit_rate": cache_stats['hit_rate'],
        "cache_size": cache_stats['cache_size']
    }


def main():
    """主函数"""
    print("状态序列化性能优化演示")
    print("=" * 50)
    
    global enhanced_serializer
    enhanced_serializer = StateSerializer(max_cache_size=1000)
    
    # 运行所有测试
    results = {}
    
    results["serialization"] = test_serialization_performance()
    results["diff"] = test_diff_serialization_performance()
    results["cache"] = test_cache_performance()
    
    # 总结
    print("\n" + "=" * 50)
    print("性能优化总结")
    print("=" * 50)
    
    print(f"\n1. 序列化性能:")
    print(f"   缓存命中性能提升: {results['serialization']['improvement_cache_hit']:.2f}%")
    
    print(f"\n2. 差异序列化性能:")
    print(f"   时间提升: {results['diff']['time_improvement']:.2f}%")
    print(f"   大小提升: {results['diff']['size_improvement']:.2f}%")
    
    print(f"\n3. 缓存性能:")
    print(f"   缓存命中率: {results['cache']['cache_hit_rate']}")
    print(f"   缓存大小: {results['cache']['cache_size']}")
    
    print("\n性能优化演示完成！")


if __name__ == "__main__":
    main()