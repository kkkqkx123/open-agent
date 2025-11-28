#!/usr/bin/env python3
"""测试HeaderValidator的功能"""

from src.core.llm.utils.header_validator import HeaderValidator

def test_header_validator():
    """测试标头验证器"""
    validator = HeaderValidator()
    
    print("=== 测试当前的ALLOWED_HEADERS和SENSITIVE_HEADERS ===")
    print(f"ALLOWED_HEADERS: {sorted(validator.ALLOWED_HEADERS)}")
    print(f"SENSITIVE_HEADERS: {sorted(validator.SENSITIVE_HEADERS)}")
    
    print("\n=== 测试1: 验证有效的非敏感标头 ===")
    headers1 = {
        "user-agent": "Test Agent",
        "content-type": "application/json",
        "x-custom-header": "custom-value"
    }
    is_valid1, errors1 = validator.validate_headers(headers1)
    print(f"Headers: {headers1}")
    print(f"Valid: {is_valid1}, Errors: {errors1}")
    
    print("\n=== 测试2: 验证敏感标头使用环境变量格式 ===")
    headers2 = {
        "authorization": "Bearer ${TEST_BEARER_TOKEN}",
        "x-api-key": "${TEST_API_KEY}"
    }
    is_valid2, errors2 = validator.validate_headers(headers2)
    print(f"Headers: {headers2}")
    print(f"Valid: {is_valid2}, Errors: {errors2}")
    
    print("\n=== 测试3: 验证敏感标头未使用环境变量格式（应该失败） ===")
    headers3 = {
        "authorization": "Bearer actual_token_here",
        "x-api-key": "actual_api_key_here"
    }
    is_valid3, errors3 = validator.validate_headers(headers3)
    print(f"Headers: {headers3}")
    print(f"Valid: {is_valid3}, Errors: {errors3}")
    
    print("\n=== 测试4: 验证不在白名单中的标头（应该失败） ===")
    headers4 = {
        "x-forbidden-header": "forbidden-value"
    }
    is_valid4, errors4 = validator.validate_headers(headers4)
    print(f"Headers: {headers4}")
    print(f"Valid: {is_valid4}, Errors: {errors4}")
    
    print("\n=== 测试5: 混合有效和无效标头 ===")
    headers5 = {
        "user-agent": "Test Agent",
        "content-type": "application/json",
        "authorization": "Bearer ${TEST_BEARER_TOKEN}",
        "x-forbidden-header": "forbidden-value"
    }
    is_valid5, errors5 = validator.validate_headers(headers5)
    print(f"Headers: {headers5}")
    print(f"Valid: {is_valid5}, Errors: {errors5}")
    
    print("\n=== 测试6: 标头脱敏功能 ===")
    headers6 = {
        "user-agent": "Test Agent",
        "authorization": "Bearer ${TEST_BEARER_TOKEN}",
        "x-api-key": "${TEST_API_KEY}",
        "content-type": "application/json"
    }
    sanitized = validator.sanitize_headers_for_logging(headers6)
    print(f"Original headers: {headers6}")
    print(f"Sanitized headers: {sanitized}")

if __name__ == "__main__":
    test_header_validator()