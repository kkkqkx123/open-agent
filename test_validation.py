from src.infrastructure.container import get_global_container
from src.infrastructure.di_config import DIConfig

container = get_global_container()
di_config = DIConfig(container)
di_config.configure_core_services()

from infrastructure.config.loader.yaml_loader import IConfigLoader
from src.infrastructure.logger.logger import Logger
from src.infrastructure.tools.validation.manager import ToolValidationManager
from src.infrastructure.tools.interfaces import IToolManager

config_loader = container.get(IConfigLoader)
logger = Logger('Test')
tool_manager = container.get(IToolManager)
validation_manager = ToolValidationManager(config_loader, logger, tool_manager)

results = validation_manager.validate_all_tools('tools')
print(f'Validated {len(results)} tools')

success_count = 0
for tool_name, tool_results in results.items():
    config_result = tool_results.get('config', None)
    loading_result = tool_results.get('loading', None)
    type_result = tool_results.get('type', None)
    
    config_success = config_result.is_successful() if config_result else False
    loading_success = loading_result.is_successful() if loading_result else False
    type_success = type_result.is_successful() if type_result else True
    
    if config_success and loading_success and type_success:
        success_count += 1
    
    print(f'{tool_name}: config={config_success}, loading={loading_success}, type={type_success}')

print(f'Total successful: {success_count}/{len(results)}')