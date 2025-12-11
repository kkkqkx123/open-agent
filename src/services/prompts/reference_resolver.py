"""增强的提示词引用解析器

提供更强大的提示词引用解析功能，支持多种引用格式和高级特性。
"""

import re
import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from src.interfaces.dependency_injection import get_logger

from ...interfaces import IPromptRegistry, PromptMeta, PromptConfig
from src.interfaces.prompts.exceptions import (
    PromptReferenceError,
    PromptNotFoundError,
    PromptCircularReferenceError
)

logger = get_logger(__name__)


@dataclass
class ReferenceConfig:
    """引用配置"""
    enable_reference_resolution: bool = True
    max_reference_depth: int = 10
    enable_conditional_references: bool = True
    enable_template_variables: bool = True
    enable_file_references: bool = True
    prompts_directory: str = "configs/prompts"


@dataclass
class ResolvedReference:
    """解析结果"""
    content: str
    metadata: Dict[str, Any]
    dependencies: List[str]  # 依赖的提示词ID
    variables: Dict[str, Any]  # 使用的变量


class PromptReferenceResolver:
    """增强的提示词引用解析器
    
    支持的引用格式：
    1. 基础引用: {{ref:prompt_id}}
    2. 版本引用: {{ref:prompt_id@version}}
    3. 别名引用: {{ref:prompt_id as alias}}
    4. 条件引用: {{if ref:prompt_id}}content{{endif}}
    5. 文件引用: {{file:category/name.md}}
    6. 变量引用: {{var:variable_name}}
    7. 环境变量: {{env:ENV_VAR}}
    8. 配置引用: {{config:config_path}}
    """
    
    def __init__(
        self,
        registry: IPromptRegistry,
        config: Optional[ReferenceConfig] = None
    ):
        self._registry = registry
        self._config = config or ReferenceConfig()
        
        # 编译正则表达式模式
        self._compile_patterns()
        
        # 解析缓存
        self._resolution_cache: Dict[str, ResolvedReference] = {}
        
        logger.debug("增强提示词引用解析器初始化完成")
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 基础引用模式
        self._reference_pattern = re.compile(
            r'\{\{\s*ref\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 文件引用模式
        self._file_pattern = re.compile(
            r'\{\{\s*file\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 变量模式
        self._variable_pattern = re.compile(
            r'\{\{\s*var\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 环境变量模式
        self._env_pattern = re.compile(
            r'\{\{\s*env\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 配置引用模式
        self._config_pattern = re.compile(
            r'\{\{\s*config\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 条件引用模式
        self._conditional_pattern = re.compile(
            r'\{\{\s*if\s+ref\s*:\s*([^}]+)\s*\}\}(.*?)\{\{\s*endif\s*\}\}',
            re.IGNORECASE | re.DOTALL
        )
        
        # 循环模式
        self._loop_pattern = re.compile(
            r'\{\{\s*for\s+(\w+)\s+in\s+(\w+)\s*\}\}(.*?)\{\{\s*endfor\s*\}\}',
            re.IGNORECASE | re.DOTALL
        )
    
    async def resolve_references(
        self,
        prompt: PromptMeta,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ResolvedReference:
        """解析提示词中的所有引用
        
        Args:
            prompt: 提示词元数据
            variables: 变量字典
            context: 上下文字典
            
        Returns:
            解析结果
        """
        if not self._config.enable_reference_resolution:
            return ResolvedReference(
                content=prompt.content,
                metadata={"resolution_disabled": True},
                dependencies=[],
                variables=variables or {}
            )
        
        # 检查缓存
        cache_key = self._generate_cache_key(prompt.id, variables or {}, context or {})
        if cache_key in self._resolution_cache:
            logger.debug(f"引用解析缓存命中: {prompt.id}")
            return self._resolution_cache[cache_key]
        
        # 解析上下文
        variables = variables or {}
        context = context or {}
        merged_context = {**variables, **context}
        
        try:
            # 解析引用
            resolved_content, dependencies = await self._resolve_content(
                prompt.content,
                prompt.id,
                merged_context,
                visited=set(),
                depth=0
            )
            
            # 创建解析结果
            result = ResolvedReference(
                content=resolved_content,
                metadata={
                    "prompt_id": prompt.id,
                    "resolution_depth": 0,
                    "timestamp": str(asyncio.get_event_loop().time())
                },
                dependencies=list(dependencies),
                variables=variables
            )
            
            # 缓存结果
            self._resolution_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"解析引用失败: {prompt.id}, 错误: {e}")
            raise PromptReferenceError(f"解析引用失败: {e}")
    
    async def _resolve_content(
        self,
        content: str,
        prompt_id: str,
        context: Dict[str, Any],
        visited: Set[str],
        depth: int
    ) -> Tuple[str, Set[str]]:
        """解析内容中的引用
        
        Args:
            content: 内容
            prompt_id: 提示词ID
            context: 上下文
            visited: 已访问的提示词ID
            depth: 当前深度
            
        Returns:
            解析后的内容和依赖列表
        """
        # 检查深度限制
        if depth >= self._config.max_reference_depth:
            raise PromptReferenceError(
                f"引用解析深度超过限制 ({self._config.max_reference_depth})"
            )
        
        # 检查循环引用
        if prompt_id in visited:
            cycle = " -> ".join(list(visited) + [prompt_id])
            raise PromptCircularReferenceError(f"检测到循环引用: {cycle}")
        
        # 添加到已访问集合
        visited = visited.copy()
        visited.add(prompt_id)
        depth += 1
        
        dependencies = set()
        
        try:
            # 1. 解析条件引用
            if self._config.enable_conditional_references:
                content = await self._resolve_conditional_references(
                    content, context, visited, depth
                )
            
            # 2. 解析循环
            content = await self._resolve_loops(content, context)
            
            # 3. 解析文件引用
            if self._config.enable_file_references:
                content, file_deps = await self._resolve_file_references(content, context)
                dependencies.update(file_deps)
            
            # 4. 解析环境变量
            content = self._resolve_environment_variables(content)
            
            # 5. 解析配置引用
            content = self._resolve_config_references(content, context)
            
            # 6. 解析变量
            if self._config.enable_template_variables:
                content = self._resolve_variables(content, context)
            
            # 7. 解析提示词引用
            content, ref_deps = await self._resolve_prompt_references(
                content, context, visited, depth
            )
            dependencies.update(ref_deps)
            
            return content, dependencies
            
        except Exception as e:
            logger.error(f"解析内容失败: {prompt_id}, 错误: {e}")
            raise
    
    async def _resolve_prompt_references(
        self,
        content: str,
        context: Dict[str, Any],
        visited: Set[str],
        depth: int
    ) -> Tuple[str, Set[str]]:
        """解析提示词引用"""
        dependencies = set()
        
        async def replace_reference(match):
            ref_spec = match.group(1).strip()
            
            try:
                # 解析引用规范
                ref_info = self._parse_reference_spec(ref_spec)
                
                # 获取引用的提示词
                referenced_prompt = await self._registry.get(
                    ref_info["ref_id"],
                    ref_info.get("version")
                )
                
                # 递归解析引用的提示词
                resolved_content, ref_deps = await self._resolve_content(
                    referenced_prompt.content,
                    ref_info["ref_id"],
                    context,
                    visited,
                    depth
                )
                
                dependencies.add(ref_info["ref_id"])
                dependencies.update(ref_deps)
                
                return resolved_content
                
            except PromptNotFoundError:
                logger.warning(f"引用的提示词未找到: {ref_spec}")
                return match.group(0)
            except Exception as e:
                logger.warning(f"解析引用失败: {ref_spec}, 错误: {e}")
                return match.group(0)
        
        # 替换所有引用
        tasks = []
        for match in self._reference_pattern.finditer(content):
            tasks.append(replace_reference(match))
        
        if tasks:
            replacements = await asyncio.gather(*tasks)
            result = content
            for i, match in enumerate(self._reference_pattern.finditer(content)):
                result = result.replace(match.group(0), replacements[i], 1)
            return result, dependencies
        
        return content, dependencies
    
    async def _resolve_conditional_references(
        self,
        content: str,
        context: Dict[str, Any],
        visited: Set[str],
        depth: int
    ) -> str:
        """解析条件引用"""
        async def replace_conditional(match):
            ref_spec = match.group(1).strip()
            conditional_content = match.group(2)
            
            try:
                ref_info = self._parse_reference_spec(ref_spec)
                
                # 检查引用的提示词是否存在
                await self._registry.get(ref_info["ref_id"], ref_info.get("version"))
                
                # 引用存在，解析条件内容
                resolved_content, _ = await self._resolve_content(
                    conditional_content,
                    f"conditional:{ref_info['ref_id']}",
                    context,
                    visited,
                    depth
                )
                
                return resolved_content
                
            except PromptNotFoundError:
                # 引用不存在，返回空字符串
                return ""
            except Exception as e:
                logger.warning(f"解析条件引用失败: {ref_spec}, 错误: {e}")
                return match.group(0)
        
        # 替换所有条件引用
        tasks = []
        for match in self._conditional_pattern.finditer(content):
            tasks.append(replace_conditional(match))
        
        if tasks:
            replacements = await asyncio.gather(*tasks)
            result = content
            for i, match in enumerate(self._conditional_pattern.finditer(content)):
                result = result.replace(match.group(0), replacements[i], 1)
            return result
        
        return content
    
    async def _resolve_file_references(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Tuple[str, Set[str]]:
        """解析文件引用"""
        dependencies = set()
        
        async def replace_file(match):
            file_path = match.group(1).strip()
            
            try:
                # 构建完整文件路径
                full_path = Path(self._config.prompts_directory) / file_path
                
                # 检查文件是否存在
                if not full_path.exists():
                    logger.warning(f"引用的文件不存在: {full_path}")
                    return match.group(0)
                
                # 读取文件内容
                with open(full_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # 处理文件内容中的变量
                if self._config.enable_template_variables:
                    file_content = self._resolve_variables(file_content, context)
                
                dependencies.add(f"file:{file_path}")
                return file_content
                
            except Exception as e:
                logger.warning(f"解析文件引用失败: {file_path}, 错误: {e}")
                return match.group(0)
        
        # 替换所有文件引用
        tasks = []
        for match in self._file_pattern.finditer(content):
            tasks.append(replace_file(match))
        
        if tasks:
            replacements = await asyncio.gather(*tasks)
            result = content
            for i, match in enumerate(self._file_pattern.finditer(content)):
                result = result.replace(match.group(0), replacements[i], 1)
            return result, dependencies
        
        return content, dependencies
    
    async def _resolve_loops(self, content: str, context: Dict[str, Any]) -> str:
        """解析循环"""
        def replace_loop(match):
            var_name = match.group(1)
            collection_name = match.group(2)
            loop_content = match.group(3)
            
            try:
                # 获取集合
                collection = context.get(collection_name, [])
                if not isinstance(collection, (list, tuple)):
                    logger.warning(f"循环集合不是列表类型: {collection_name}")
                    return match.group(0)
                
                # 生成循环内容
                result_parts = []
                for item in collection:
                    loop_context = context.copy()
                    loop_context[var_name] = item
                    
                    # 处理循环内容中的变量
                    processed_content = self._resolve_variables(loop_content, loop_context)
                    result_parts.append(processed_content)
                
                return "\n".join(result_parts)
                
            except Exception as e:
                logger.warning(f"解析循环失败: {var_name} in {collection_name}, 错误: {e}")
                return match.group(0)
        
        # 替换所有循环
        result = content
        for match in self._loop_pattern.finditer(content):
            result = result.replace(match.group(0), replace_loop(match), 1)
        
        return result
    
    def _resolve_environment_variables(self, content: str) -> str:
        """解析环境变量"""
        import os
        
        def replace_env(match):
            env_name = match.group(1).strip()
            return os.getenv(env_name, "")
        
        return self._env_pattern.sub(replace_env, content)
    
    def _resolve_config_references(self, content: str, context: Dict[str, Any]) -> str:
        """解析配置引用"""
        def replace_config(match):
            config_path = match.group(1).strip()
            
            try:
                # 从上下文中获取配置值
                keys = config_path.split('.')
                value = context
                
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        logger.warning(f"配置路径不存在: {config_path}")
                        return match.group(0)
                
                return str(value) if value is not None else ""
                
            except Exception as e:
                logger.warning(f"解析配置引用失败: {config_path}, 错误: {e}")
                return match.group(0)
        
        return self._config_pattern.sub(replace_config, content)
    
    def _resolve_variables(self, content: str, context: Dict[str, Any]) -> str:
        """解析变量"""
        def replace_variable(match):
            var_name = match.group(1).strip()
            
            if var_name in context:
                value = context[var_name]
                return str(value) if value is not None else ""
            
            return match.group(0)
        
        return self._variable_pattern.sub(replace_variable, content)
    
    def _parse_reference_spec(self, spec: str) -> Dict[str, Any]:
        """解析引用规范"""
        # 支持的格式：
        # 1. ref_id
        # 2. ref_id@version
        # 3. ref_id as alias
        # 4. ref_id@version as alias
        
        result = {"ref_id": spec.strip(), "version": None, "alias": None}
        
        # 解析版本
        if "@" in spec:
            ref_part, version_part = spec.split("@", 1)
            result["ref_id"] = ref_part.strip()
            
            if " as " in version_part:
                version, alias = version_part.split(" as ", 1)
                result["version"] = version.strip()
                result["alias"] = alias.strip()
            else:
                result["version"] = version_part.strip()
        elif " as " in spec:
            ref_id, alias = spec.split(" as ", 1)
            result["ref_id"] = ref_id.strip()
            result["alias"] = alias.strip()
        
        return result
    
    def _generate_cache_key(self, prompt_id: str, variables: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib
        
        cache_data = {
            "prompt_id": prompt_id,
            "variables": sorted(variables.items()) if variables else [],
            "context_keys": sorted(context.keys()) if context else []
        }
        
        return hashlib.md5(str(cache_data).encode()).hexdigest()
    
    async def extract_references(self, content: str) -> List[Dict[str, Any]]:
        """从内容中提取所有引用"""
        references = []
        
        # 提取提示词引用
        for match in self._reference_pattern.finditer(content):
            ref_spec = match.group(1).strip()
            ref_info = self._parse_reference_spec(ref_spec)
            ref_info["type"] = "prompt"
            ref_info["match"] = match.group(0)
            references.append(ref_info)
        
        # 提取文件引用
        if self._config.enable_file_references:
            for match in self._file_pattern.finditer(content):
                file_path = match.group(1).strip()
                references.append({
                    "type": "file",
                    "path": file_path,
                    "match": match.group(0)
                })
        
        # 提取变量引用
        if self._config.enable_template_variables:
            for match in self._variable_pattern.finditer(content):
                var_name = match.group(1).strip()
                references.append({
                    "type": "variable",
                    "name": var_name,
                    "match": match.group(0)
                })
        
        return references
    
    async def validate_references(self, prompt: PromptMeta) -> List[str]:
        """验证提示词中的所有引用"""
        errors = []
        
        try:
            # 提取引用
            references = await self.extract_references(prompt.content)
            
            # 验证每个引用
            for ref in references:
                if ref["type"] == "prompt":
                    try:
                        await self._registry.get(ref["ref_id"], ref.get("version"))
                    except PromptNotFoundError:
                        errors.append(f"引用的提示词未找到: {ref['ref_id']}")
                    except Exception as e:
                        errors.append(f"验证引用失败 {ref['ref_id']}: {e}")
                
                elif ref["type"] == "file":
                    file_path = Path(self._config.prompts_directory) / ref["path"]
                    if not file_path.exists():
                        errors.append(f"引用的文件不存在: {ref['path']}")
            
            # 检查循环引用
            await self._check_circular_references(prompt.id, prompt.content)
            
        except PromptCircularReferenceError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"验证引用时发生错误: {e}")
        
        return errors
    
    async def _check_circular_references(self, prompt_id: str, content: str) -> None:
        """检查循环引用"""
        visited = set()
        await self._check_circular_references_recursive(prompt_id, content, visited, 0)
    
    async def _check_circular_references_recursive(
        self, prompt_id: str, content: str, visited: Set[str], depth: int
    ) -> None:
        """递归检查循环引用"""
        if depth >= self._config.max_reference_depth:
            return
        
        if prompt_id in visited:
            cycle = " -> ".join(list(visited) + [prompt_id])
            raise PromptCircularReferenceError(f"检测到循环引用: {cycle}")
        
        visited.add(prompt_id)
        
        try:
            # 提取引用
            references = await self.extract_references(content)
            
            # 递归检查每个引用
            for ref in references:
                if ref["type"] == "prompt":
                    try:
                        referenced_prompt = await self._registry.get(
                            ref["ref_id"],
                            ref.get("version")
                        )
                        
                        await self._check_circular_references_recursive(
                            ref["ref_id"],
                            referenced_prompt.content,
                            visited.copy(),
                            depth + 1
                        )
                        
                    except PromptNotFoundError:
                        # 引用不存在，跳过
                        continue
                        
        finally:
            visited.discard(prompt_id)
    
    def clear_cache(self) -> None:
        """清理解析缓存"""
        self._resolution_cache.clear()
        logger.debug("引用解析缓存已清理")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self._resolution_cache),
            "max_reference_depth": self._config.max_reference_depth,
            "enable_reference_resolution": self._config.enable_reference_resolution,
            "enable_conditional_references": self._config.enable_conditional_references,
            "enable_template_variables": self._config.enable_template_variables,
            "enable_file_references": self._config.enable_file_references
        }