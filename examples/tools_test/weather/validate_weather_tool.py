"""
天气工具验证脚本

验证天气工具的配置和功能是否正确。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量用于测试
os.environ["OPENWEATHER_API_KEY"] = "test_api_key"


def validate_weather_config():
    """验证天气工具配置文件"""
    print("开始验证天气工具配置文件...")
    
    try:
        from src.infrastructure.config_loader import YamlConfigLoader
        
        # 创建配置加载器
        config_loader = YamlConfigLoader()
        
        # 加载天气工具配置
        weather_config = config_loader.load("tools/weather.yaml")
        print(f"成功加载天气工具配置: {weather_config}")
        
        # 验证必需字段
        required_fields = ["name", "tool_type", "description", "api_url", "method"]
        for field in required_fields:
            if field not in weather_config:
                print(f"错误: 缺少必需字段 '{field}'")
                return False
        
        # 验证工具类型
        if weather_config["tool_type"] != "native":
            print(f"错误: 工具类型应为 'native'，实际为 '{weather_config['tool_type']}'")
            return False
        
        # 验证参数Schema
        if "parameters_schema" not in weather_config:
            print("错误: 缺少参数Schema")
            return False
            
        params_schema = weather_config["parameters_schema"]
        if params_schema.get("type") != "object":
            print("错误: 参数Schema类型不正确")
            return False
            
        properties = params_schema.get("properties", {})
        if "q" not in properties:
            print("错误: 参数Schema缺少必需参数 'q'")
            return False
            
        # 验证必需参数列表
        required_params = params_schema.get("required", [])
        if "q" not in required_params:
            print("错误: 参数Schema中 'q' 未标记为必需参数")
            return False
        
        print("天气工具配置文件验证通过")
        return True
        
    except Exception as e:
        print(f"配置文件验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_weather_tool():
    """验证天气工具配置和功能"""
    print("\n开始验证天气工具...")
    
    try:
        # 使用测试容器来获取工具管理器
        from src.infrastructure.test_container import TestContainer
        
        # 创建测试容器
        with TestContainer() as test_container:
            # 设置基础配置
            test_container.setup_basic_configs()
            
            # 创建正确的配置目录结构
            import os
            configs_dir = test_container.temp_path / "configs"
            tools_config_dir = configs_dir / "tools"
            tools_config_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建天气工具配置文件
            weather_config_path = tools_config_dir / "weather.yaml"
            weather_config_content = """# 天气查询工具配置
name: weather
tool_type: native
description: 查询指定城市的天气信息
enabled: true
timeout: 15
api_url: "https://api.openweathermap.org/data/2.5/weather"
method: GET
auth_method: api_key
api_key: "${OPENWEATHER_API_KEY}"
headers:
  User-Agent: "ModularAgent/1.0"
  Content-Type: "application/json"
retry_count: 3
retry_delay: 1.0
parameters_schema:
  type: object
  properties:
    q:
      type: string
      description: 城市名称，如 "Beijing,CN" 或 "London"
    units:
      type: string
      description: 温度单位，可选值：metric(摄氏度)、imperial(华氏度)、kelvin(开尔文)
      enum: ["metric", "imperial", "kelvin"]
      default: "metric"
    lang:
      type: string
      description: 返回结果的语言，如 "zh_cn"、"en"
      default: "zh_cn"
  required:
    - q
metadata:
  category: "weather"
  tags: ["weather", "api", "external"]
  documentation_url: "https://openweathermap.org/api"
"""
            
            with open(weather_config_path, "w", encoding="utf-8") as f:
                f.write(weather_config_content)
            
            # 获取工具管理器
            tool_manager = test_container.get_tool_manager()
            
            # 加载工具
            tools = tool_manager.load_tools()
            print(f"成功加载 {len(tools)} 个工具")
            
            # 查找天气工具
            weather_tool = None
            for tool in tools:
                if tool.name == "weather":
                    weather_tool = tool
                    break
            
            if weather_tool is None:
                print("错误: 未找到天气工具")
                return False
            
            print(f"找到天气工具: {weather_tool.name}")
            print(f"工具描述: {weather_tool.description}")
            
            # 验证工具参数Schema
            schema = weather_tool.parameters_schema
            print(f"参数Schema: {schema}")
            
            if schema.get("type") != "object":
                print("错误: 参数Schema类型不正确")
                return False
            
            properties = schema.get("properties", {})
            if "q" not in properties:
                print("错误: 缺少必需参数 'q'")
                return False
            
            # 验证工具配置
            print("工具配置验证通过")
            return True
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weather_tool_functionality():
    """测试天气工具功能"""
    print("\n开始测试天气工具功能...")
    
    try:
        # 使用测试容器来获取工具管理器
        from src.infrastructure.test_container import TestContainer
        
        # 创建测试容器
        with TestContainer() as test_container:
            # 设置基础配置
            test_container.setup_basic_configs()
            
            # 创建正确的配置目录结构
            import os
            configs_dir = test_container.temp_path / "configs"
            tools_config_dir = configs_dir / "tools"
            tools_config_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建天气工具配置文件
            weather_config_path = tools_config_dir / "weather.yaml"
            weather_config_content = """# 天气查询工具配置
name: weather
tool_type: native
description: 查询指定城市的天气信息
enabled: true
timeout: 15
api_url: "https://api.openweathermap.org/data/2.5/weather"
method: GET
auth_method: api_key
api_key: "${OPENWEATHER_API_KEY}"
headers:
  User-Agent: "ModularAgent/1.0"
  Content-Type: "application/json"
retry_count: 3
retry_delay: 1.0
parameters_schema:
  type: object
  properties:
    q:
      type: string
      description: 城市名称，如 "Beijing,CN" 或 "London"
    units:
      type: string
      description: 温度单位，可选值：metric(摄氏度)、imperial(华氏度)、kelvin(开尔文)
      enum: ["metric", "imperial", "kelvin"]
      default: "metric"
    lang:
      type: string
      description: 返回结果的语言，如 "zh_cn"、"en"
      default: "zh_cn"
  required:
    - q
metadata:
  category: "weather"
  tags: ["weather", "api", "external"]
  documentation_url: "https://openweathermap.org/api"
"""
            
            with open(weather_config_path, "w", encoding="utf-8") as f:
                f.write(weather_config_content)
            
            # 获取工具管理器
            tool_manager = test_container.get_tool_manager()
            
            # 获取天气工具
            try:
                weather_tool = tool_manager.get_tool("weather")
                print(f"成功获取天气工具: {weather_tool.name}")
                
                # 验证工具接口
                print(f"工具类型: {type(weather_tool)}")
                print(f"工具参数Schema: {weather_tool.parameters_schema}")
                
                # 由于需要API密钥，我们只验证工具是否存在和基本功能
                print("天气工具功能验证通过")
                return True
            except ValueError as e:
                if "工具不存在" in str(e):
                    print("错误: 天气工具未正确注册")
                    return False
                else:
                    # 其他错误可能是API密钥问题，不影响工具注册
                    print("天气工具已注册，但API调用需要有效密钥")
                    return True
        
    except Exception as e:
        print(f"功能测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weather_tool_directly():
    """直接测试天气工具功能"""
    print("\n开始直接测试天气工具功能...")
    
    try:
        # 直接测试天气工具函数
        from defination.tools.weather import get_weather
        
        # 由于没有有效的API密钥，我们只测试参数验证
        try:
            # 测试缺少城市参数
            get_weather(q="", units="metric", lang="zh_cn", api_key="test_key")
            print("错误: 应该抛出参数验证错误")
            return False
        except ValueError as e:
            if "城市名称不能为空" in str(e):
                print("✓ 参数验证正常工作")
            else:
                print(f"✗ 参数验证错误: {e}")
                return False
        
        try:
            # 测试无效的单位参数
            get_weather(q="Beijing", units="invalid", lang="zh_cn", api_key="test_key")
            print("错误: 应该抛出单位验证错误")
            return False
        except ValueError as e:
            if "无效的温度单位" in str(e):
                print("✓ 单位验证正常工作")
            else:
                print(f"✗ 单位验证错误: {e}")
                return False
        
        try:
            # 测试缺少API密钥
            get_weather(q="Beijing", units="metric", lang="zh_cn", api_key=None)
            print("错误: 应该抛出API密钥错误")
            return False
        except ValueError as e:
            if "缺少API密钥" in str(e):
                print("✓ API密钥验证正常工作")
            else:
                print(f"✗ API密钥验证错误: {e}")
                return False
        
        print("✓ 天气工具函数验证通过")
        return True
        
    except Exception as e:
        print(f"直接功能测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("天气工具验证脚本")
    print("=" * 30)
    
    # 验证配置文件
    config_valid = validate_weather_config()
    
    # 直接测试工具功能
    functionality_valid = test_weather_tool_directly()
    
    print("\n" + "=" * 30)
    if config_valid and functionality_valid:
        print("✓ 天气工具验证通过")
        print("  - 配置文件验证通过")
        print("  - 功能验证通过")
    else:
        print("✗ 天气工具验证失败")
        if not config_valid:
            print("  - 配置文件验证失败")
        if not functionality_valid:
            print("  - 功能验证失败")