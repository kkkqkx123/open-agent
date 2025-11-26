"""
提示词引用解析器

提供提示词引用的解析和替换功能
"""

import re
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio

from interfaces.prompts.models import PromptReference

from ...interfaces import IPromptRegistry, PromptMeta, PromptConfig
from ...core.common.exceptions import (
    PromptReferenceError,
    PromptNotFoundError,
    PromptCircularReferenceError
)


@dataclass
class ReferenceContext:
    """引用解析上下文"""
    visited: Set[str]  # 已访问的提示词ID（用于检测循环引用）
    depth: int  # 当前解析深度
    max_depth: int  # 最大解析深度
    variables: Dict[str, Any]  # 变量上下文


class PromptReferenceResolver:
    """提示词引用解析器"""
    
    def __init__(
        self,
        registry: IPromptRegistry,
        config: Optional[PromptConfig] = None
    ):
        self._registry = registry
        self._config = config or PromptConfig(
            system_prompt=None,
            user_command=None,
            context=None,
            examples=None,
            constraints=None,
            format=None
        )
        
        # 引用模式
        self._reference_pattern = re.compile(
            r'\{\{\s*ref\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 变量模式
        self._variable_pattern = re.compile(
            r'\{\{\s*var\s*:\s*([^}]+)\s*\}\}',
            re.IGNORECASE
        )
        
        # 条件引用模式
        self._conditional_pattern = re.compile(
            r'\{\{\s*if\s+ref\s*:\s*([^}]+)\s*\}\}(.*?)\{\{\s*endif\s*\}\}',
            re.IGNORECASE | re.DOTALL
        )
    
    async def resolve_references(
        self,
        prompt: PromptMeta,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """解析提示词中的所有引用"""
        if not self._config.enable_reference_resolution:
            return prompt.content
        
        context = ReferenceContext(
            visited=set(),
            depth=0,
            max_depth=self._config.max_reference_depth,
            variables=variables or {}
        )
        
        try:
            resolved_content = await self._resolve_content(
                prompt.content,
                prompt.id,
                context
            )
            
            # 解析变量
            resolved_content = await self._resolve_variables(
                resolved_content,
                context.variables
            )
            
            return resolved_content
            
        except Exception as e:
            raise PromptReferenceError(f"解析引用失败: {e}")
    
    async def resolve_single_reference(
        self,
        reference: PromptReference,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """解析单个引用"""
        try:
            # 获取引用的提示词
            referenced_prompt = await self._registry.get(
                reference.ref_id, 
                reference.version
            )
            
            # 如果有别名，使用别名作为上下文
            context_id = reference.alias or reference.ref_id
            
            # 创建解析上下文
            context = ReferenceContext(
                visited={reference.ref_id},
                depth=0,
                max_depth=self._config.max_reference_depth,
                variables=variables or {}
            )
            
            # 解析引用的提示词内容
            resolved_content = await self._resolve_content(
                referenced_prompt.content,
                context_id,
                context
            )
            
            return resolved_content
            
        except PromptNotFoundError:
            raise PromptReferenceError(f"引用的提示词未找到: {reference.ref_id}")
        except Exception as e:
            raise PromptReferenceError(f"解析引用失败: {e}")
    
    async def extract_references(self, content: str) -> List[PromptReference]:
        """从内容中提取所有引用"""
        references = []
        
        # 查找所有引用模式
        matches = self._reference_pattern.finditer(content)
        
        for match in matches:
            ref_spec = match.group(1).strip()
            
            try:
                reference = self._parse_reference_spec(ref_spec)
                references.append(reference)
            except Exception as e:
                # 记录错误但继续处理其他引用
                print(f"解析引用规范失败 '{ref_spec}': {e}")
        
        return references
    
    async def validate_references(self, prompt: PromptMeta) -> List[str]:
        """验证提示词中的所有引用"""
        errors = []
        
        # 提取引用
        references = await self.extract_references(prompt.content)
        
        # 验证每个引用
        for ref in references:
            try:
                await self._registry.get(ref.ref_id, ref.version)
            except PromptNotFoundError:
                errors.append(f"引用的提示词未找到: {ref.ref_id}")
            except Exception as e:
                errors.append(f"验证引用失败 {ref.ref_id}: {e}")
        
        # 检查循环引用
        try:
            context = ReferenceContext(
                visited=set(),
                depth=0,
                max_depth=self._config.max_reference_depth,
                variables={}
            )
            
            await self._check_circular_references(
                prompt.id,
                prompt.content,
                context
            )
            
        except PromptCircularReferenceError as e:
            errors.append(str(e))
        
        return errors
    
    async def _resolve_content(
        self,
        content: str,
        prompt_id: str,
        context: ReferenceContext
    ) -> str:
        """解析内容中的引用"""
        # 检查深度限制
        if context.depth >= context.max_depth:
            raise PromptReferenceError(
                f"引用解析深度超过限制 ({context.max_depth})"
            )
        
        # 检查循环引用
        if prompt_id in context.visited:
            raise PromptCircularReferenceError(
                f"检测到循环引用: {' -> '.join(context.visited)} -> {prompt_id}"
            )
        
        # 添加到已访问集合
        context.visited.add(prompt_id)
        context.depth += 1
        
        try:
            # 解析条件引用
            content = await self._resolve_conditional_references(content, context)
            
            # 解析普通引用
            content = await self._resolve_normal_references(content, context)
            
            return content
            
        finally:
            # 清理上下文
            context.visited.discard(prompt_id)
            context.depth -= 1
    
    async def _resolve_normal_references(
        self,
        content: str,
        context: ReferenceContext
    ) -> str:
        """解析普通引用"""
        async def replace_reference(match):
            ref_spec = match.group(1).strip()
            
            try:
                reference = self._parse_reference_spec(ref_spec)
                referenced_prompt = await self._registry.get(
                    reference.ref_id,
                    reference.version
                )
                
                # 递归解析引用的提示词
                return await self._resolve_content(
                    referenced_prompt.content,
                    reference.ref_id,
                    context
                )
                
            except Exception as e:
                # 引用解析失败时返回原始引用
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
            return result
        
        return content
    
    async def _resolve_conditional_references(
        self,
        content: str,
        context: ReferenceContext
    ) -> str:
        """解析条件引用"""
        async def replace_conditional(match):
            ref_spec = match.group(1).strip()
            conditional_content = match.group(2)
            
            try:
                reference = self._parse_reference_spec(ref_spec)
                
                # 检查引用的提示词是否存在
                await self._registry.get(reference.ref_id, reference.version)
                
                # 引用存在，解析条件内容
                return await self._resolve_content(
                    conditional_content,
                    f"conditional:{reference.ref_id}",
                    context
                )
                
            except PromptNotFoundError:
                # 引用不存在，返回空字符串
                return ""
            except Exception as e:
                # 其他错误，返回原始内容
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
    
    async def _resolve_variables(
        self,
        content: str,
        variables: Dict[str, Any]
    ) -> str:
        """解析变量"""
        def replace_variable(match):
            var_name = match.group(1).strip()
            
            if var_name in variables:
                value = variables[var_name]
                return str(value) if value is not None else ""
            
            return match.group(0)
        
        return self._variable_pattern.sub(replace_variable, content)
    
    async def _check_circular_references(
        self,
        prompt_id: str,
        content: str,
        context: ReferenceContext
    ) -> None:
        """检查循环引用"""
        # 检查深度限制
        if context.depth >= context.max_depth:
            return
        
        # 检查循环引用
        if prompt_id in context.visited:
            cycle = " -> ".join(list(context.visited) + [prompt_id])
            raise PromptCircularReferenceError(f"检测到循环引用: {cycle}")
        
        # 添加到已访问集合
        context.visited.add(prompt_id)
        context.depth += 1
        
        try:
            # 提取引用
            references = await self.extract_references(content)
            
            # 递归检查每个引用
            for ref in references:
                try:
                    referenced_prompt = await self._registry.get(
                        ref.ref_id,
                        ref.version
                    )
                    
                    await self._check_circular_references(
                        ref.ref_id,
                        referenced_prompt.content,
                        context
                    )
                    
                except PromptNotFoundError:
                    # 引用不存在，跳过
                    continue
                    
        finally:
            # 清理上下文
            context.visited.discard(prompt_id)
            context.depth -= 1
    
    def _parse_reference_spec(self, spec: str) -> PromptReference:
        """解析引用规范"""
        # 支持的格式：
        # 1. ref_id
        # 2. ref_id@version
        # 3. ref_id as alias
        # 4. ref_id@version as alias
        
        # 解析版本
        version = None
        if "@" in spec:
            ref_id, version_part = spec.split("@", 1)
            if " as " in version_part:
                version, alias = version_part.split(" as ", 1)
                version = version.strip()
                alias = alias.strip()
            else:
                ref_id = ref_id.strip()
                version = version_part.strip()
                alias = None
        elif " as " in spec:
            ref_id, alias = spec.split(" as ", 1)
            ref_id = ref_id.strip()
            alias = alias.strip()
            version = None
        else:
            ref_id = spec.strip()
            version = None
            alias = None
        
        return PromptReference(
            ref_id=ref_id,
            ref_type="prompt",
            ref_path=ref_id,
            version=version,
            alias=alias
        )