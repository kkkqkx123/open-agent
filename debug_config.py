import tempfile
import os
import yaml
from pathlib import Path
from src.infrastructure.config.config_system import ConfigSystem
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.config.config_merger import ConfigMerger
from src.infrastructure.config.config_validator import ConfigValidator

# 创建临时目录和配置文件
temp_dir = tempfile.mkdtemp()
configs_dir = Path(temp_dir) / 'configs'
configs_dir.mkdir()

# 创建全局配置文件
global_config = {
    'log_level': 'INFO',
    'env': 'development',
    'env_prefix': 'AGENT_',
}

with open(configs_dir / 'global.yaml', 'w') as f:
    yaml.dump(global_config, f)

# 创建LLM组配置文件
llm_group_config = {
    'openai_group': {
        'base_url': 'https://api.openai.com/v1',
        'headers': {'User-Agent': 'ModularAgent/1.0'},
        'parameters': {'temperature': 0.7, 'max_tokens': 200},
    }
}

llm_dir = configs_dir / 'llms'
llm_dir.mkdir()

with open(llm_dir / '_group.yaml', 'w') as f:
    yaml.dump(llm_group_config, f)

# 创建provider目录结构
anthropic_provider_dir = llm_dir / 'provider' / 'anthropic'
anthropic_provider_dir.mkdir(parents=True)

# 创建provider common配置文件
anthropic_common_config = {
    'model_type': 'anthropic',
    'provider': 'anthropic',
    'supports_caching': True,
    'default_parameters': {
        'temperature': 0.5,
        'max_tokens': 4000,
        'timeout': 60
    },
    'cache_config': {
        'ttl_seconds': 3600,
        'max_size': 1000
    },
    'fallback_config': {
        'enabled': True,
        'max_attempts': 5
    }
}

with open(anthropic_provider_dir / 'common.yaml', 'w') as f:
    yaml.dump(anthropic_common_config, f)

# 创建具体的provider配置文件
anthropic_claude_config = {
    'model_name': 'claude-3-sonnet-20240229',
    'api_key': '${AGENT_ANTHROPIC_KEY}',
    'parameters': {
        'temperature': 0.4,  # 覆盖common配置
    },
    'supports_caching': True,  # 保持common配置
    'fallback_models': ['claude-3-opus-20240229']
}

with open(anthropic_provider_dir / 'claude-sonnet.yaml', 'w') as f:
    yaml.dump(anthropic_claude_config, f)

# 初始化配置系统
config_loader = YamlConfigLoader(str(configs_dir))
config_merger = ConfigMerger()
config_validator = ConfigValidator()

config_system = ConfigSystem(
    config_loader=config_loader,
    config_merger=config_merger,
    config_validator=config_validator,
    base_path=str(configs_dir),
)

# 设置环境变量
os.environ['AGENT_ANTHROPIC_KEY'] = 'test_anthropic_key'

# 加载配置
llm_config = config_system.load_llm_config('claude-sonnet')

# 检查配置
print('parameters:', llm_config.parameters)
print('timeout parameter:', llm_config.get_parameter('timeout'))
print('temperature parameter:', llm_config.get_parameter('temperature'))
print('max_tokens parameter:', llm_config.get_parameter('max_tokens'))

# 清理环境变量
del os.environ['AGENT_ANTHROPIC_KEY']

# 清理临时目录
import shutil
shutil.rmtree(temp_dir)