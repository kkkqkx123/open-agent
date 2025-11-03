`src/infrastructure/di_config.py` 模块的配置主要来源于以下两个层面：

### 1. 配置加载器 (IConfigLoader)
该模块通过 `YamlConfigLoader` 实例从文件系统加载配置，具体来源如下：
- **配置路径**：默认从 `configs/` 目录加载，可通过 `configure_core_services` 方法的 `config_path` 参数指定。
- **配置格式**：支持 YAML 格式的配置文件。
- **环境变量注入**：支持 `${VAR}` 和 `${VAR:default}` 语法，从系统环境变量中注入值。
- **配置继承**：支持通过 `inherits_from` 字段实现配置继承。

在 `di_config.py` 中，配置加载器通过 `_register_config_loader` 方法注册：
```python
def _register_config_loader(self, config_path: str) -> None:
    if not self.container.has_service(IConfigLoader):
        config_loader = YamlConfigLoader(base_path=config_path)
        self.container.register_instance(IConfigLoader, config_loader)
        self._config_loader = config_loader
```

### 2. 依赖注入容器配置
除了外部文件配置，模块还通过依赖注入容器进行内部配置：
- **服务注册**：使用 `register_instance`、`register_factory` 等方法将服务注册到容器中。
- **生命周期管理**：通过 `ServiceLifetime.SINGLETON` 等设置服务生命周期。
- **动态配置**：通过 `register_additional_services` 方法支持运行时动态注册服务。

### 3. 全局配置入口
模块提供了多个配置入口：
- `create_container()`：创建并配置依赖注入容器
- `get_global_container()`：获取全局容器实例
- `DIConfig.configure_core_services()`：配置核心服务

这些配置机制共同构成了模块的配置体系，实现了外部配置文件与内部服务注册的有机结合。