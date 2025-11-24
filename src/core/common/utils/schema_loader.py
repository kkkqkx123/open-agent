"""配置模式加载工具

专门用于配置系统的模式加载和验证功能。
"""

import json
from typing import Dict, Any, Optional, List, cast
from pathlib import Path


class SchemaLoader:
    """配置模式加载器"""

    def __init__(self, schema_dir: str = "schemas"):
        """初始化模式加载器

        Args:
            schema_dir: 模式文件目录
        """
        # 确保路径是绝对路径或正确处理相对路径
        self.schema_dir = Path(schema_dir)
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """加载配置模式

        Args:
            schema_name: 模式名称

        Returns:
            模式字典
        """
        if schema_name in self._schemas:
            return self._schemas[schema_name]

        # 在 schemas 子目录中查找
        schema_file = self.schema_dir / "schemas" / f"{schema_name}.json"
        
        # 如果在 schemas 子目录中找不到，也尝试在主目录中查找
        if not schema_file.exists():
            schema_file = self.schema_dir / f"{schema_name}.json"

        if not schema_file.exists():
            raise FileNotFoundError(f"模式文件不存在: {schema_file}")

        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)

            # 确保 schema 是字典类型
            if not isinstance(schema, dict):
                raise ValueError(f"模式文件 {schema_file} 必须包含 JSON 对象")

            self._schemas[schema_name] = schema
            return cast(Dict[str, Any], schema)

        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON模式文件 {schema_file}: {e}")
        except ValueError as e:
            # 重新抛出 ValueError，不包装
            raise
        except Exception as e:
            raise RuntimeError(f"加载模式文件失败 {schema_file}: {e}")

    def validate_config(self, config: Dict[str, Any], schema_name: str) -> bool:
        """验证配置是否符合模式

        Args:
            config: 配置字典
            schema_name: 模式名称

        Returns:
            是否有效
        """
        try:
            schema = self.load_schema(schema_name)
            return self._validate_against_schema(config, schema)
        except Exception:
            return False

    def _validate_against_schema(
        self, config: Dict[str, Any], schema: Dict[str, Any]
    ) -> bool:
        """根据模式验证配置

        Args:
            config: 配置字典
            schema: 模式字典

        Returns:
            是否有效
        """
        # 简单的模式验证实现
        # 在实际项目中，可以使用 jsonschema 库进行更严格的验证

        # 检查必需字段
        required = schema.get("required", [])
        for field in required:
            if field not in config:
                return False

        # 检查字段类型
        properties = schema.get("properties", {})
        for field, value in config.items():
            if field in properties:
                field_schema = properties[field]
                expected_type = field_schema.get("type")

                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False

        return True

    def get_schema_field_info(
        self, schema_name: str, field_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取模式字段信息

        Args:
            schema_name: 模式名称
            field_name: 字段名称

        Returns:
            字段信息字典
        """
        try:
            schema = self.load_schema(schema_name)
            properties = schema.get("properties", {})
            field_info = properties.get(field_name)
            return cast(Optional[Dict[str, Any]], field_info)
        except Exception:
            return cast(Optional[Dict[str, Any]], None)

    def list_schemas(self) -> List[str]:
        """列出所有可用的模式

        Returns:
            模式名称列表
        """
        # 首先尝试在 schemas 子目录中查找
        schemas_subdir = self.schema_dir / "schemas"
        if schemas_subdir.exists():
            schemas = []
            for file_path in schemas_subdir.glob("*.json"):
                schemas.append(file_path.stem)
            return schemas

        # 如果 schemas 子目录不存在，则在主目录中查找
        if not self.schema_dir.exists():
            return []

        schemas = []
        for file_path in self.schema_dir.glob("*.json"):
            schemas.append(file_path.stem)

        return schemas

    def reload_schema(self, schema_name: str) -> Dict[str, Any]:
        """重新加载模式

        Args:
            schema_name: 模式名称

        Returns:
            模式字典
        """
        if schema_name in self._schemas:
            del self._schemas[schema_name]
        return self.load_schema(schema_name)

    def reload_all_schemas(self) -> None:
        """重新加载所有模式"""
        self._schemas.clear()

    def create_default_schema(self, schema_name: str, config: Dict[str, Any]) -> None:
        """根据配置创建默认模式

        Args:
            schema_name: 模式名称
            config: 配置字典
        """
        schema = self._generate_schema_from_config(config)

        # 确保 schemas 目录存在
        schemas_dir = self.schema_dir / "schemas"
        schemas_dir.mkdir(parents=True, exist_ok=True)

        schema_file = schemas_dir / f"{schema_name}.json"

        try:
            with open(schema_file, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)

            # 更新缓存
            self._schemas[schema_name] = schema

        except Exception as e:
            raise RuntimeError(f"创建模式文件失败 {schema_file}: {e}")

    def _generate_schema_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """根据配置生成模式

        Args:
            config: 配置字典

        Returns:
            模式字典
        """
        properties = {}
        required = []

        for key, value in config.items():
            field_schema = self._infer_field_schema(value)
            properties[key] = field_schema

            # 对于非空值，假设为必需字段
            if value is not None and value != "":
                required.append(key)

        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _infer_field_schema(self, value: Any) -> Dict[str, Any]:
        """推断字段模式

        Args:
            value: 字段值

        Returns:
            字段模式字典
        """
        if isinstance(value, bool):  # 检查布尔值必须在检查整数之前
            return {"type": "boolean"}
        elif isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, list):
            if value:
                item_schema = self._infer_field_schema(value[0])
                return {"type": "array", "items": item_schema}
            else:
                return {"type": "array"}
        elif isinstance(value, dict):
            properties = {}
            for k, v in value.items():
                properties[k] = self._infer_field_schema(v)
            return {"type": "object", "properties": properties}
        else:
            return {"type": "string"}  # 默认为字符串类型