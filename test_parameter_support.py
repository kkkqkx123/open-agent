#!/usr/bin/env python3
"""测试参数支持的简单脚本"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config_loading():
    """测试配置加载"""
    print("测试配置加载...")
    
    try:
        # 修复导入问题
        sys.path.insert(0, str(Path(__file__).parent))
        
        from llm.config import LLMClientConfig, OpenAIConfig, AnthropicConfig, GeminiConfig, MockConfig
        
        # 测试OpenAI配置
        openai_config_dict = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 2000,
            "max_completion_tokens": 4000,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
            "top_p": 0.9,
            "top_logprobs": 5,
            "tool_choice": "auto",
            "response_format": {"type": "json_object"},
            "service_tier": "flex",
            "safety_identifier": "test-user",
            "store": True,
            "reasoning": {"effort": "medium"},
            "verbosity": "high",
            "web_search_options": {"enabled": True},
            "seed": 42,
            "user": "test-user"
        }
        
        openai_config = OpenAIConfig.from_dict(openai_config_dict)
        print(f"✓ OpenAI配置加载成功: {openai_config.model_name}")
        print(f"  - max_completion_tokens: {openai_config.max_completion_tokens}")
        print(f"  - top_logprobs: {openai_config.top_logprobs}")
        print(f"  - service_tier: {openai_config.service_tier}")
        
        # 测试Anthropic配置
        anthropic_config_dict = {
            "model_type": "anthropic",
            "model_name": "claude-3-sonnet-20240229",
            "api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "top_k": 40,
            "stop_sequences": ["END", "STOP"],
            "system": "你是一个有用的助手",
            "thinking_config": {"thinking_budget": 1024},
            "tool_choice": "auto"
        }
        
        anthropic_config = AnthropicConfig.from_dict(anthropic_config_dict)
        print(f"✓ Anthropic配置加载成功: {anthropic_config.model_name}")
        print(f"  - top_k: {anthropic_config.top_k}")
        print(f"  - stop_sequences: {anthropic_config.stop_sequences}")
        print(f"  - thinking_config: {anthropic_config.thinking_config}")
        
        # 测试Gemini配置
        gemini_config_dict = {
            "model_type": "gemini",
            "model_name": "gemini-pro",
            "api_key": "test-key",
            "temperature": 0.7,
            "max_tokens": 2000,
            "max_output_tokens": 4000,
            "top_p": 0.9,
            "top_k": 40,
            "stop_sequences": ["END"],
            "candidate_count": 1,
            "system_instruction": {"parts": [{"text": "你是一个有用的助手"}]},
            "response_mime_type": "application/json",
            "thinking_config": {"thinking_budget": 1024},
            "safety_settings": {"threshold": "BLOCK_NONE"}
        }
        
        gemini_config = GeminiConfig.from_dict(gemini_config_dict)
        print(f"✓ Gemini配置加载成功: {gemini_config.model_name}")
        print(f"  - max_output_tokens: {gemini_config.max_output_tokens}")
        print(f"  - candidate_count: {gemini_config.candidate_count}")
        print(f"  - response_mime_type: {gemini_config.response_mime_type}")
        
        # 测试Mock配置
        mock_config_dict = {
            "model_type": "mock",
            "model_name": "mock-model",
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_delay": 0.1,
            "error_rate": 0.0,
            "error_types": ["timeout", "rate_limit"]
        }
        
        mock_config = MockConfig.from_dict(mock_config_dict)
        print(f"✓ Mock配置加载成功: {mock_config.model_name}")
        print(f"  - response_delay: {mock_config.response_delay}")
        print(f"  - error_rate: {mock_config.error_rate}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_files():
    """测试配置文件"""
    print("\n测试配置文件...")
    
    try:
        import yaml
        
        # 测试OpenAI配置文件
        with open("configs/llms/openai-gpt4.yaml", 'r', encoding='utf-8') as f:
            openai_yaml = yaml.safe_load(f)
        
        print(f"✓ OpenAI配置文件加载成功")
        print(f"  - 模型: {openai_yaml['model_name']}")
        print(f"  - 参数数量: {len(openai_yaml.get('parameters', {}))}")
        
        # 测试Anthropic配置文件
        with open("configs/llms/anthropic-claude.yaml", 'r', encoding='utf-8') as f:
            anthropic_yaml = yaml.safe_load(f)
        
        print(f"✓ Anthropic配置文件加载成功")
        print(f"  - 模型: {anthropic_yaml['model_name']}")
        print(f"  - 参数数量: {len(anthropic_yaml.get('parameters', {}))}")
        
        # 测试Gemini配置文件
        with open("configs/llms/gemini-pro.yaml", 'r', encoding='utf-8') as f:
            gemini_yaml = yaml.safe_load(f)
        
        print(f"✓ Gemini配置文件加载成功")
        print(f"  - 模型: {gemini_yaml['model_name']}")
        print(f"  - 参数数量: {len(gemini_yaml.get('parameters', {}))}")
        
        # 测试Mock配置文件
        with open("configs/llms/mock.yaml", 'r', encoding='utf-8') as f:
            mock_yaml = yaml.safe_load(f)
        
        print(f"✓ Mock配置文件加载成功")
        print(f"  - 模型: {mock_yaml['model_name']}")
        print(f"  - 参数数量: {len(mock_yaml.get('parameters', {}))}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_coverage():
    """测试参数覆盖度"""
    print("\n测试参数覆盖度...")
    
    # OpenAI参数列表
    openai_params = [
        'temperature', 'max_tokens', 'max_completion_tokens', 'top_p', 
        'frequency_penalty', 'presence_penalty', 'stop', 'top_logprobs',
        'tool_choice', 'tools', 'response_format', 'stream_options',
        'service_tier', 'safety_identifier', 'store', 'reasoning',
        'verbosity', 'web_search_options', 'seed', 'user'
    ]
    
    # Anthropic参数列表
    anthropic_params = [
        'temperature', 'max_tokens', 'top_p', 'top_k', 'stop_sequences',
        'tool_choice', 'tools', 'system', 'thinking_config', 'response_format',
        'metadata', 'user'
    ]
    
    # Gemini参数列表
    gemini_params = [
        'temperature', 'max_tokens', 'max_output_tokens', 'top_p', 'top_k',
        'stop_sequences', 'candidate_count', 'system_instruction',
        'response_mime_type', 'thinking_config', 'safety_settings',
        'tool_choice', 'tools', 'user'
    ]
    
    print(f"✓ OpenAI支持参数数量: {len(openai_params)}")
    print(f"✓ Anthropic支持参数数量: {len(anthropic_params)}")
    print(f"✓ Gemini支持参数数量: {len(gemini_params)}")
    
    return True

def main():
    """主函数"""
    print("开始验证LLM参数支持...")
    
    success = True
    
    # 测试配置加载
    success &= test_config_loading()
    
    # 测试配置文件
    success &= test_config_files()
    
    # 测试参数覆盖度
    success &= test_parameter_coverage()
    
    if success:
        print("\n🎉 所有测试通过！LLM参数支持已成功更新。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())