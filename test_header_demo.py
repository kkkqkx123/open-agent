"""HTTP标头验证功能演示"""

import sys
import os
sys.path.insert(0, 'src/llm')

from header_validator import HeaderValidator, HeaderProcessor

def main():
    print("=== HTTP标头白名单控制和敏感标头脱敏功能演示 ===\n")
    
    # 设置环境变量
    os.environ['TEST_API_KEY'] = 'test-secret-key'
    os.environ['TEST_TOKEN'] = 'test-bearer-token'
    
    validator = HeaderValidator()
    processor = HeaderProcessor()
    
    # 测试1: 允许的标头
    print("1. 测试允许的标头:")
    allowed_headers = {
        'X-API-Key': '${TEST_API_KEY}',
        'User-Agent': 'ModularAgent/1.0',
        'Authorization': 'Bearer ${TEST_TOKEN}',
        'X-Custom-Header': 'custom-value'
    }
    
    is_valid, errors = validator.validate_headers(allowed_headers)
    resolved, sanitized, is_valid2, errors2 = processor.process_headers(allowed_headers)
    
    print(f"   原始标头: {allowed_headers}")
    print(f"   验证结果: {is_valid}, 错误: {errors}")
    print(f"   解析后标头: {resolved}")
    print(f"   脱敏后标头: {sanitized}")
    print()
    
    # 测试2: 不允许的标头
    print("2. 测试不允许的标头:")
    disallowed_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Forbidden': 'value'
    }
    
    is_valid, errors = validator.validate_headers(disallowed_headers)
    resolved, sanitized, is_valid2, errors2 = processor.process_headers(disallowed_headers)
    
    print(f"   原始标头: {disallowed_headers}")
    print(f"   验证结果: {is_valid}, 错误: {errors}")
    print(f"   脱敏后标头: {sanitized}")
    print()
    
    # 测试3: 敏感标头未使用环境变量
    print("3. 测试敏感标头未使用环境变量:")
    sensitive_headers = {
        'Authorization': 'Bearer hardcoded-token',
        'X-API-Key': 'hardcoded-key'
    }
    
    is_valid, errors = validator.validate_headers(sensitive_headers)
    resolved, sanitized, is_valid2, errors2 = processor.process_headers(sensitive_headers)
    
    print(f"   原始标头: {sensitive_headers}")
    print(f"   验证结果: {is_valid}, 错误: {errors}")
    print(f"   脱敏后标头: {sanitized}")
    print()
    
    # 测试4: 环境变量解析
    print("4. 测试环境变量解析:")
    env_headers = {
        'X-API-Key': '${TEST_API_KEY}',
        'Authorization': 'Bearer ${TEST_TOKEN}',
        'User-Agent': 'ModularAgent/1.0'
    }
    
    is_valid, errors = validator.validate_headers(env_headers)
    resolved, sanitized, is_valid2, errors2 = processor.process_headers(env_headers)
    
    print(f"   原始标头: {env_headers}")
    print(f"   验证结果: {is_valid}, 错误: {errors}")
    print(f"   解析后标头: {resolved}")
    print(f"   脱敏后标头: {sanitized}")
    print()
    
    # 测试5: 获取允许和敏感标头列表
    print("5. 允许的标头列表:")
    allowed = processor.get_allowed_headers()
    print(f"   {allowed}")
    
    print("   敏感的标头列表:")
    sensitive = processor.get_sensitive_headers()
    print(f"   {sensitive}")
    print()
    
    print("=== 演示完成 ===")

if __name__ == "__main__":
    main()