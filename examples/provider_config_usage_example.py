"""Provider配置系统使用示例

展示如何使用新的Provider配置发现、继承处理和Token计算服务。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm.config_manager import LLMConfigManager
from src.core.llm.provider_config_discovery import ProviderConfigDiscovery
from src.services.llm.enhanced_token_calculation_service import EnhancedTokenCalculationService
from src.services.logger import get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    print("=== Provider配置系统使用示例 ===\n")
    
    # 1. 创建LLM配置管理器（启用Provider配置）
    print("1. 初始化LLM配置管理器...")
    config_manager = LLMConfigManager(
        enable_provider_configs=True,
        enable_hot_reload=False,  # 示例中禁用热重载
        validation_enabled=True
    )
    
    # 2. 获取配置状态
    print("\n2. 获取配置状态...")
    status = config_manager.get_config_status()
    print(f"Provider配置启用: {status['provider_configs_enabled']}")
    print(f"已加载客户端配置: {status['loaded_client_configs']}")
    print(f"可用模型: {status['available_models']}")
    
    if 'provider_discovery' in status:
        provider_status = status['provider_discovery']
        print(f"Provider目录存在: {provider_status['provider_directory_exists']}")
        print(f"发现的Provider数量: {provider_status['total_providers']}")
        print(f"启用的Provider数量: {provider_status['enabled_providers']}")
        
        print("\n发现的Provider:")
        for provider_name, info in provider_status['providers'].items():
            print(f"  - {provider_name}: {info['model_count']} 个模型")
            print(f"    模型: {', '.join(info['models'])}")
    
    # 3. 使用Provider配置发现器
    print("\n3. 使用Provider配置发现器...")
    if config_manager._provider_discovery:
        discovery = config_manager._provider_discovery
        
        # 列出所有Provider模型
        all_models = discovery.list_all_models()
        print("所有Provider模型:")
        for provider_name, models in all_models.items():
            print(f"  {provider_name}: {models}")
        
        # 获取特定Provider的模型
        if 'openai' in all_models:
            openai_models = discovery.list_provider_models('openai')
            print(f"\nOpenAI模型: {openai_models}")
    
    # 4. 验证配置
    print("\n4. 验证配置...")
    if 'openai:gpt-4' in status['available_models']:
        validation_result = config_manager.validate_client_config('openai', 'gpt-4')
        print(f"GPT-4配置验证: {validation_result.get_summary()}")
        
        if validation_result.warnings:
            print("警告:")
            for warning in validation_result.warnings:
                print(f"  - {warning}")
        
        if validation_result.info:
            print("信息:")
            for info in validation_result.info:
                print(f"  - {info}")
    
    # 5. 使用增强Token计算服务
    print("\n5. 使用增强Token计算服务...")
    token_service = EnhancedTokenCalculationService(
        default_provider="openai",
        llm_config_manager=config_manager,
        provider_discovery=config_manager._provider_discovery
    )
    
    # 计算Token数量
    test_text = "Hello, how are you today? I'd like to know about the weather."
    if 'openai:gpt-4' in status['available_models']:
        token_count = token_service.calculate_tokens(test_text, "openai", "gpt-4")
        print(f"文本: '{test_text}'")
        print(f"GPT-4 Token数量: {token_count}")
        
        # 计算成本
        cost_info = token_service.calculate_cost(token_count, 100, "openai", "gpt-4")
        print(f"成本信息: {cost_info}")
        
        # 获取定价信息
        pricing_info = token_service.get_model_pricing_info("openai", "gpt-4")
        print(f"定价信息: {pricing_info}")
    
    # 6. 获取服务状态
    print("\n6. 获取Token计算服务状态...")
    service_status = token_service.get_service_status()
    print(f"默认Provider: {service_status['default_provider']}")
    print(f"缓存的处理器: {service_status['cached_processors']}")
    print(f"缓存的Token配置: {service_status['cached_token_configs']}")
    print(f"支持的模型: {service_status['supported_models']}")
    
    # 7. 演示配置继承
    print("\n7. 演示配置继承...")
    if config_manager._provider_discovery:
        # 获取GPT-4的完整配置（包含继承的配置）
        gpt4_config = config_manager._provider_discovery.get_provider_config(
            "openai", "gpt-4"
        )
        
        if gpt4_config:
            print("GPT-4完整配置（包含继承）:")
            print(f"  模型类型: {gpt4_config.get('model_type')}")
            print(f"  模型名称: {gpt4_config.get('model_name')}")
            print(f"  超时时间: {gpt4_config.get('timeout')}")
            print(f"  最大重试: {gpt4_config.get('max_retries')}")
            print(f"  输入Token价格: ${gpt4_config.get('pricing', {}).get('input_token_cost', 0)}/1K")
            print(f"  输出Token价格: ${gpt4_config.get('pricing', {}).get('output_token_cost', 0)}/1K")
            print(f"  Token计算类型: {gpt4_config.get('token_calculation', {}).get('type')}")
            
            # 显示Provider元信息
            provider_meta = gpt4_config.get('_provider_meta', {})
            if provider_meta:
                print(f"  Provider元信息:")
                print(f"    Provider名称: {provider_meta.get('provider_name')}")
                print(f"    模型名称: {provider_meta.get('model_name')}")
                print(f"    通用配置路径: {provider_meta.get('common_config_path')}")
                print(f"    模型配置路径: {provider_meta.get('model_config_path')}")
    
    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        import traceback
        traceback.print_exc()