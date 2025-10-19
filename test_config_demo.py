"""配置加载与验证功能演示"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_loading() -> None:
    print("=== 配置加载与验证功能演示 ===\n")
    
    # 设置环境变量
    os.environ['OPENAI_API_KEY'] = 'test-openai-key'
    os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
    os.environ['ANTHROPIC_API_KEY'] = 'test-anthropic-key'
    
    try:
        from src.config.config_system import ConfigSystem
        from src.infrastructure.config_loader import YamlConfigLoader
        from src.config.config_merger import ConfigMerger
        from src.config.config_validator import ConfigValidator
        
        # 创建配置系统组件
        config_loader = YamlConfigLoader("configs")
        config_merger = ConfigMerger()
        config_validator = ConfigValidator()
        
        # 创建配置系统
        config_system = ConfigSystem(
            config_loader=config_loader,
            config_merger=config_merger,
            config_validator=config_validator
        )
        
        # 测试1: 加载LLM配置（包含环境变量解析和配置继承）
        print("1. 测试LLM配置加载:")
        try:
            llm_config = config_system.load_llm_config("openai-gpt4")
            print(f"   模型类型: {llm_config.model_type}")
            print(f"   模型名称: {llm_config.model_name}")
            print(f"   API密钥: {llm_config.api_key}")
            print(f"   基础URL: {llm_config.base_url}")
            print(f"   标头: {llm_config.headers}")
            print(f"   参数: {llm_config.parameters}")
            print("   ✓ LLM配置加载成功")
        except Exception as e:
            print(f"   ✗ LLM配置加载失败: {e}")
        print()
        
        # 测试2: 测试配置继承
        print("2. 测试配置继承:")
        try:
            # 加载组配置
            group_config = config_loader.load("llms/_group.yaml")
            print(f"   组配置: {group_config}")
            
            # 加载个体配置
            individual_config = config_loader.load("llms/openai-gpt4.yaml")
            print(f"   个体配置: {individual_config}")
            
            # 合并配置
            merged_config = config_merger.merge_group_config(
                group_config.get("openai_group", {}),
                individual_config
            )
            print(f"   合并后配置: {merged_config}")
            print("   ✓ 配置继承测试成功")
        except Exception as e:
            print(f"   ✗ 配置继承测试失败: {e}")
        print()
        
        # 测试3: 测试环境变量解析
        print("3. 测试环境变量解析:")
        try:
            test_config = {
                "api_key": "${OPENAI_API_KEY}",
                "headers": {
                    "Authorization": "Bearer ${OPENAI_API_KEY}",
                    "User-Agent": "ModularAgent/1.0"
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": "${MAX_TOKENS:2000}"
                }
            }
            
            resolved_config = config_loader.resolve_env_vars(test_config)
            print(f"   原始配置: {test_config}")
            print(f"   解析后配置: {resolved_config}")
            print("   ✓ 环境变量解析测试成功")
        except Exception as e:
            print(f"   ✗ 环境变量解析测试失败: {e}")
        print()
        
        # 测试4: 测试配置验证
        print("4. 测试配置验证:")
        try:
            # 有效配置
            valid_config = {
                "model_type": "openai",
                "model_name": "gpt-4",
                "api_key": "${OPENAI_API_KEY}",
                "base_url": "https://api.openai.com/v1"
            }
            
            result = config_validator.validate_llm_config(valid_config)
            print(f"   有效配置验证结果: {result.is_valid}")
            if not result.is_valid:
                print(f"   错误: {result.errors}")
            
            # 无效配置
            invalid_config = {
                "model_type": "invalid_type",
                "model_name": "gpt-4"
                # 缺少必需字段
            }
            
            result = config_validator.validate_llm_config(invalid_config)
            print(f"   无效配置验证结果: {result.is_valid}")
            if not result.is_valid:
                print(f"   错误: {result.errors}")
            
            print("   ✓ 配置验证测试成功")
        except Exception as e:
            print(f"   ✗ 配置验证测试失败: {e}")
        print()
        
        print("=== 演示完成 ===")
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("可能是因为相对导入问题，让我们直接测试配置加载器...")
        
        # 直接测试配置加载器
        try:
            from src.infrastructure.config_loader import YamlConfigLoader
            
            config_loader = YamlConfigLoader("configs")
            
            # 测试加载配置文件
            print("直接测试配置加载器:")
            
            # 加载组配置
            try:
                group_config = config_loader.load("llms/_group.yaml")
                print(f"组配置加载成功: {list(group_config.keys())}")
            except Exception as e:
                print(f"组配置加载失败: {e}")
            
            # 加载个体配置
            try:
                individual_config = config_loader.load("llms/openai-gpt4.yaml")
                print(f"个体配置加载成功: {list(individual_config.keys())}")
                
                # 测试环境变量解析
                resolved_config = config_loader.resolve_env_vars(individual_config)
                print(f"环境变量解析成功，API密钥: {resolved_config.get('api_key', 'N/A')}")
                
            except Exception as e:
                print(f"个体配置加载失败: {e}")
                
        except Exception as e:
            print(f"直接测试也失败: {e}")

if __name__ == "__main__":
    test_config_loading()