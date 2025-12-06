"""pytest配置文件

配置测试环境，确保能够正确导入src模块。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 确保src目录可以被导入
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 设置环境变量
os.environ["PYTHONPATH"] = str(project_root) + os.pathsep + os.environ.get("PYTHONPATH", "")

print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径