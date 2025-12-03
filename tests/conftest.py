"""Pytest配置文件，用于设置测试环境"""

import sys
import os
from unittest.mock import Mock

# 添加项目根目录到Python路径，使src模块可以被导入
project_root = os.path.dirname(os.path.dirname(__file__))  # 获取项目根目录
sys.path.insert(0, project_root)

# 确保src目录在路径中
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# 测试时使用标准库的logging，避免循环导入问题
import logging

# 配置测试日志
logging.basicConfig(level=logging.INFO)

# 使用Mock模拟logger模块
mock_logger = Mock()
mock_logger.get_logger = Mock(side_effect=lambda name=None: logging.getLogger(name or 'test'))

sys.modules['src.services.logger'] = mock_logger
sys.modules['src.core.logger'] = mock_logger

# 添加调试日志
print(f"使用标准库logging进行测试，避免循环导入")