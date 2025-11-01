在 defination\tools目录中实现天气工具，配置见 @/configs/tools/weather.yaml ，然后在examples\tools_test目录中编写pytest文件来测试
参考：
examples\tools_test\test_weather_tool.py
examples\tools_test\validate_weather_tool.py

或：
新增native工具hash_convert，用于把字段转为hash。参考configs\tools\weather.yaml
defination\tools\weather.py，并编写验证文件与pytest文件，参考examples\tools_test\weather\test_weather_tool.py
examples\tools_test\weather\validate_weather_tool.py