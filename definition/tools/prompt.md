改造为builtin/native工具(前者不依赖外部api，后者需要【包括网络请求】。请自己选择适当的类型)工具，参考defination\tools\hash_convert.py
configs\tools\hash_convert.yaml
并编写验证文件与pytest文件，参考examples\tools_test\weather\test_weather_tool.py
examples\tools_test\weather\validate_weather_tool.py
工具放在src\domain\tools\types目录，测试文件放在tests\unit\types目录
注意：配置文件中yaml部分的所有文本和py函数的返回值使用英文，注释与py代码中无所谓


examples\tools_test\duckduckgo_search\test_duckduckgo_search_tool.py
examples\tools_test\duckduckgo_search\validate_duckduckgo_search_tool.py这2个测试已通过。创建文件，实际使用该工具执行搜索

在 defination\tools目录中实现天气工具，配置见 @/configs/tools/weather.yaml ，然后在examples\tools_test目录中编写pytest文件来测试
参考：
examples\tools_test\test_weather_tool.py
examples\tools_test\validate_weather_tool.py

或：
新增native工具hash_convert，用于把字段转为hash。参考configs\tools\weather.yaml
defination\tools\weather.py，并编写验证文件与pytest文件，参考examples\tools_test\weather\test_weather_tool.py
examples\tools_test\weather\validate_weather_tool.py