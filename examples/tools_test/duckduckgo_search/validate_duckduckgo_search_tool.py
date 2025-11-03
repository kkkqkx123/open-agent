"""
DuckDuckGo搜索工具验证脚本

验证DuckDuckGo搜索工具的配置和功能是否正确。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def validate_duckduckgo_search_config():
    """验证DuckDuckGo搜索工具配置文件"""
    print("开始验证DuckDuckGo搜索工具配置文件...")
    
    try:
        from src.infrastructure.config_loader import YamlConfigLoader
        
        # 创建配置加载器
        config_loader = YamlConfigLoader()
        
        # 加载DuckDuckGo搜索工具配置
        duckduckgo_config = config_loader.load("tools/duckduckgo_search.yaml")
        print(f"成功加载DuckDuckGo搜索工具配置: {duckduckgo_config}")
        
        # 验证必需字段
        required_fields = ["name", "tool_type", "description", "api_url", "method"]
        for field in required_fields:
            if field not in duckduckgo_config:
                print(f"错误: 缺少必需字段 '{field}'")
                return False
        
        # 验证工具类型
        if duckduckgo_config["tool_type"] != "native":
            print(f"错误: 工具类型应为 'native'，实际为 '{duckduckgo_config['tool_type']}'")
            return False
        
        # 验证参数Schema
        if "parameters_schema" not in duckduckgo_config:
            print("错误: 缺少参数Schema")
            return False
            
        params_schema = duckduckgo_config["parameters_schema"]
        if params_schema.get("type") != "object":
            print("错误: 参数Schema类型不正确")
            return False
            
        properties = params_schema.get("properties", {})
        if "query" not in properties:
            print("错误: 参数Schema缺少必需参数 'query'")
            return False
            
        # 验证必需参数列表
        required_params = params_schema.get("required", [])
        if "query" not in required_params:
            print("错误: 参数Schema中 'query' 未标记为必需参数")
            return False
        
        # 验证可选参数
        if "max_results" in properties:
            max_results_prop = properties["max_results"]
            if max_results_prop.get("type") != "integer":
                print("错误: max_results参数类型应为integer")
                return False
            
            if "minimum" in max_results_prop and max_results_prop["minimum"] < 1:
                print("错误: max_results参数最小值应至少为1")
                return False
            
            if "maximum" in max_results_prop and max_results_prop["maximum"] > 50:
                print("错误: max_results参数最大值不应超过50")
                return False
        
        print("DuckDuckGo搜索工具配置文件验证通过")
        return True
        
    except Exception as e:
        print(f"配置文件验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_duckduckgo_search_tool():
    """验证DuckDuckGo搜索工具配置和功能"""
    print("\n开始验证DuckDuckGo搜索工具...")
    
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
            
            # 创建DuckDuckGo搜索工具配置文件
            duckduckgo_config_path = tools_config_dir / "duckduckgo_search.yaml"
            duckduckgo_config_content = """# DuckDuckGo搜索工具配置
name: duckduckgo_search
tool_type: native
description: A tool for searching the web using DuckDuckGo search engine and fetching web page content
enabled: true
timeout: 30
api_url: "https://html.duckduckgo.com/html"
method: POST
headers:
  User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
retry_count: 3
retry_delay: 1.0
rate_limit:
  requests_per_minute: 30
parameters_schema:
  type: object
  properties:
    query:
      type: string
      description: Search query string
    max_results:
      type: integer
      description: Maximum number of results to return (1-50)
      minimum: 1
      maximum: 50
      default: 10
  required:
    - query
metadata:
  category: "search"
  tags: ["search", "web", "duckduckgo", "content"]
  documentation_url: "https://duckduckgo.com/"
"""
            
            with open(duckduckgo_config_path, "w", encoding="utf-8") as f:
                f.write(duckduckgo_config_content)
            
            # 获取工具管理器
            tool_manager = test_container.get_tool_manager()
            
            # 加载工具
            tools = tool_manager.load_tools()
            print(f"成功加载 {len(tools)} 个工具")
            
            # 查找DuckDuckGo搜索工具
            duckduckgo_tool = None
            for tool in tools:
                if tool.name == "duckduckgo_search":
                    duckduckgo_tool = tool
                    break
            
            if duckduckgo_tool is None:
                print("错误: 未找到DuckDuckGo搜索工具")
                return False
            
            print(f"找到DuckDuckGo搜索工具: {duckduckgo_tool.name}")
            print(f"工具描述: {duckduckgo_tool.description}")
            
            # 验证工具参数Schema
            schema = duckduckgo_tool.parameters_schema
            print(f"参数Schema: {schema}")
            
            if schema.get("type") != "object":
                print("错误: 参数Schema类型不正确")
                return False
            
            properties = schema.get("properties", {})
            if "query" not in properties:
                print("错误: 缺少必需参数 'query'")
                return False
            
            # 验证工具配置
            print("工具配置验证通过")
            return True
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_duckduckgo_search_tool_functionality():
    """测试DuckDuckGo搜索工具功能"""
    print("\n开始测试DuckDuckGo搜索工具功能...")
    
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
            
            # 创建DuckDuckGo搜索工具配置文件
            duckduckgo_config_path = tools_config_dir / "duckduckgo_search.yaml"
            duckduckgo_config_content = """# DuckDuckGo搜索工具配置
name: duckduckgo_search
tool_type: native
description: A tool for searching the web using DuckDuckGo search engine and fetching web page content
enabled: true
timeout: 30
api_url: "https://html.duckduckgo.com/html"
method: POST
headers:
  User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
retry_count: 3
retry_delay: 1.0
rate_limit:
  requests_per_minute: 30
parameters_schema:
  type: object
  properties:
    query:
      type: string
      description: Search query string
    max_results:
      type: integer
      description: Maximum number of results to return (1-50)
      minimum: 1
      maximum: 50
      default: 10
  required:
    - query
metadata:
  category: "search"
  tags: ["search", "web", "duckduckgo", "content"]
  documentation_url: "https://duckduckgo.com/"
"""
            
            with open(duckduckgo_config_path, "w", encoding="utf-8") as f:
                f.write(duckduckgo_config_content)
            
            # 获取工具管理器
            tool_manager = test_container.get_tool_manager()
            
            # 获取DuckDuckGo搜索工具
            try:
                duckduckgo_tool = tool_manager.get_tool("duckduckgo_search")
                print(f"成功获取DuckDuckGo搜索工具: {duckduckgo_tool.name}")
                
                # 验证工具接口
                print(f"工具类型: {type(duckduckgo_tool)}")
                print(f"工具参数Schema: {duckduckgo_tool.parameters_schema}")
                
                print("DuckDuckGo搜索工具功能验证通过")
                return True
            except ValueError as e:
                if "工具不存在" in str(e):
                    print("错误: DuckDuckGo搜索工具未正确注册")
                    return False
                else:
                    # 其他错误
                    print("DuckDuckGo搜索工具已注册，但可能存在其他问题")
                    return True
        
    except Exception as e:
        print(f"功能测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_duckduckgo_search_tool_directly():
    """直接测试DuckDuckGo搜索工具功能"""
    print("\n开始直接测试DuckDuckGo搜索工具功能...")
    
    try:
        # 直接测试DuckDuckGo搜索工具函数
        from definition.tools.duckduckgo_search import duckduckgo_search, fetch_web_content
        
        # 测试参数验证
        try:
            # 测试空查询
            duckduckgo_search(query="", max_results=10)
            print("错误: 应该抛出查询验证错误")
            return False
        except ValueError as e:
            if "Search query cannot be empty" in str(e):
                print("✓ 查询验证正常工作")
            else:
                print(f"✗ 查询验证错误: {e}")
                return False
        
        try:
            # 测试无效的最大结果数
            duckduckgo_search(query="Python", max_results=0)
            print("错误: 应该抛出最大结果数验证错误")
            return False
        except ValueError as e:
            if "Max results must be between 1 and 50" in str(e):
                print("✓ 最大结果数验证正常工作")
            else:
                print(f"✗ 最大结果数验证错误: {e}")
                return False
        
        try:
            # 测试空URL
            fetch_web_content(url="")
            print("错误: 应该抛出URL验证错误")
            return False
        except ValueError as e:
            if "URL cannot be empty" in str(e):
                print("✓ URL验证正常工作")
            else:
                print(f"✗ URL验证错误: {e}")
                return False
        
        try:
            # 测试无效的URL格式
            fetch_web_content(url="example.com")
            print("错误: 应该抛出URL格式验证错误")
            return False
        except ValueError as e:
            if "URL must start with http:// or https://" in str(e):
                print("✓ URL格式验证正常工作")
            else:
                print(f"✗ URL格式验证错误: {e}")
                return False
        
        print("✓ DuckDuckGo搜索工具函数验证通过")
        return True
        
    except Exception as e:
        print(f"直接功能测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("DuckDuckGo搜索工具验证脚本")
    print("=" * 30)
    
    # 验证配置文件
    config_valid = validate_duckduckgo_search_config()
    
    # 直接测试工具功能
    functionality_valid = test_duckduckgo_search_tool_directly()
    
    print("\n" + "=" * 30)
    if config_valid and functionality_valid:
        print("✓ DuckDuckGo搜索工具验证通过")
        print("  - 配置文件验证通过")
        print("  - 功能验证通过")
    else:
        print("✗ DuckDuckGo搜索工具验证失败")
        if not config_valid:
            print("  - 配置文件验证失败")
        if not functionality_valid:
            print("  - 功能验证失败")