#!/usr/bin/env python3
"""LLM配置迁移脚本"""

import argparse
import logging
import sys
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('migration.log')
        ]
    )


def load_yaml_file(file_path: Path) -> dict:
    """加载YAML配置文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='LLM配置迁移工具')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--config-path', default='configs/llms', help='配置路径')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        config_path = Path(args.config_path)
        logger.info(f"加载配置文件来自: {config_path}")
        
        if not config_path.exists():
            logger.error(f"配置路径不存在: {config_path}")
            return 1
        
        # 统计配置文件
        task_group_files = list(config_path.glob('task_groups/*.yaml'))
        polling_pool_files = list(config_path.glob('polling_pools/*.yaml'))
        
        # 显示加载结果
        print("\n=== 配置加载结果 ===")
        print(f"任务组配置文件数: {len(task_group_files)}")
        print(f"轮询池配置文件数: {len(polling_pool_files)}")
        
        # 显示详细信息
        if args.verbose:
            print("\n任务组配置文件:")
            for f in task_group_files:
                print(f"  - {f.name}")
            
            print("\n轮询池配置文件:")
            for f in polling_pool_files:
                print(f"  - {f.name}")
        
        logger.info("配置扫描完成")
        return 0
            
    except Exception as e:
        logger.error(f"配置加载过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())