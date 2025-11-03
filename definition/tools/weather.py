"""
天气工具实现

提供查询指定城市天气信息的功能。
"""

import json
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from urllib.parse import urlencode


def get_weather(
    q: str, 
    units: str = "metric", 
    lang: str = "zh_cn",
    api_key: Optional[str] = None,
    api_url: str = "https://api.openweathermap.org/data/2.5/weather"
) -> Dict[str, Any]:
    """查询指定城市的天气信息
    
    Args:
        q: 城市名称，如 "Beijing,CN" 或 "London"
        units: 温度单位，可选值: metric(摄氏度), imperial(华氏度), kelvin(开尔文)
        lang: 返回结果的语言，如 "zh_cn", "en"
        api_key: OpenWeatherMap API密钥
        api_url: API URL
        
    Returns:
        Dict[str, Any]: 天气信息
        
    Raises:
        ValueError: 参数错误或API调用失败
    """
    # 验证必需参数
    if not q:
        raise ValueError("City name cannot be empty")
    
    # 验证units参数
    valid_units = ["metric", "imperial", "kelvin"]
    if units not in valid_units:
        raise ValueError(f"Invalid temperature unit: {units}, valid values are: {valid_units}")
    
    # 构建查询参数
    params = {
        "q": q,
        "units": units,
        "lang": lang
    }
    
    # 添加API密钥
    if api_key:
        params["appid"] = api_key
    else:
        raise ValueError("Missing API key")
    
    # 构建完整URL
    url = f"{api_url}?{urlencode(params)}"
    
    # 同步执行HTTP请求
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_fetch_weather_data(url))
        return result
    finally:
        loop.close()


async def _fetch_weather_data(url: str) -> Dict[str, Any]:
    """异步获取天气数据
    
    Args:
        url: 完整的API URL
        
    Returns:
        Dict[str, Any]: 天气信息
        
    Raises:
        ValueError: API调用失败
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # 检查响应状态
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"API call failed: {response.status} {error_text}")
                
                # 解析JSON响应
                data = await response.json()
                return _format_weather_response(data)
    except aiohttp.ClientError as e:
        raise ValueError(f"Network request error: {str(e)}")
    except asyncio.TimeoutError:
        raise ValueError("Request timed out")
    except Exception as e:
        raise ValueError(f"Failed to get weather data: {str(e)}")


def _format_weather_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """格式化天气响应数据
    
    Args:
        data: 原始API响应数据
        
    Returns:
        Dict[str, Any]: 格式化后的天气信息
    """
    try:
        # 提取关键信息
        weather_info = {
            "city": data.get("name", "Unknown city"),
            "country": data.get("sys", {}).get("country", "Unknown country"),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "description": data.get("weather", [{}])[0].get("description", "No description"),
            "main": data.get("weather", [{}])[0].get("main", "Unknown"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "wind_direction": data.get("wind", {}).get("deg"),
            "visibility": data.get("visibility"),
            "clouds": data.get("clouds", {}).get("all") if isinstance(data.get("clouds"), dict) else data.get("clouds"),
            "sunrise": data.get("sys", {}).get("sunrise"),
            "sunset": data.get("sys", {}).get("sunset")
        }
        
        return weather_info
    except Exception as e:
        raise ValueError(f"Failed to format weather data: {str(e)}")


# 示例用法
if __name__ == "__main__":
    # 测试天气工具
    try:
        # 注意：需要替换为有效的API密钥
        result = get_weather(
            q="Beijing,CN",
            units="metric",
            lang="zh_cn",
            api_key="your_api_key_here"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except ValueError as e:
        print(f"错误: {e}")