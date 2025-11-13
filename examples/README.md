`examples` 目录下的文件无法直接运行，因为它们需要将项目根目录添加到 Python 的模块搜索路径中，以便能够正确导入 `src` 模块。

根据项目结构和 `pyproject.toml` 文件的配置，解决方案如下：

**运行方法：**

在项目根目录 (`d:/项目/agent/open-agent`) 下，使用 `-m` 参数从模块路径运行示例文件。正确的命令格式是：

```bash
python -m examples.<example_file_name_without_extension>
```

例如，要运行 `examples/graph_workflow_examples.py` 文件，应使用：

```bash
python -m examples.graph_workflow_examples
```
