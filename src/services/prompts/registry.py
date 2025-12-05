"""
提示词注册表

提供提示词的注册、查找、版本管理等功能
"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import threading

from ...interfaces.prompts import IPromptLoader, IPromptRegistry
from ...interfaces.prompts.models import (
    PromptMeta, 
    PromptConfig, 
    PromptSearchCriteria,
    PromptSearchResult,
    PromptStatus
)
from src.interfaces.prompts.exceptions import (
    PromptNotFoundError,
    PromptError as PromptRegistrationError,
    PromptValidationError
)
from ...services.logger import get_logger

logger = get_logger(__name__)


class PromptRegistry(IPromptRegistry):
    """提示词注册表实现"""
    
    def __init__(
        self,
        loader: IPromptLoader,
        config: Optional[PromptConfig] = None
    ):
        self._loader = loader
        self._config = config or PromptConfig(
            system_prompt=None,
            user_command=None,
            context=None,
            examples=None,
            constraints=None,
            format=None
        )
        
        # 存储结构
        self._prompts: Dict[str, PromptMeta] = {}  # ID -> PromptMeta
        self._versions: Dict[str, Dict[str, PromptMeta]] = {}  # ID -> version -> PromptMeta
        self._aliases: Dict[str, str] = {}  # alias -> ID
        self._tags_index: Dict[str, Set[str]] = {}  # tag -> set of IDs
        self._categories_index: Dict[str, Set[str]] = {}  # category -> set of IDs
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 统计信息
        self._load_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    async def register(self, meta: PromptMeta) -> None:
        """注册提示词"""
        with self._lock:
            # 验证提示词
            await self._validate_prompt(meta)
            
            # 检查是否已存在
            if meta.id in self._prompts:
                existing = self._prompts[meta.id]
                if existing.version == meta.version:
                    raise PromptRegistrationError(
                        f"提示词 '{meta.id}' 版本 '{meta.version}' 已存在"
                    )
            
            # 存储提示词
            self._prompts[meta.id] = meta
            
            # 版本管理
            if meta.id not in self._versions:
                self._versions[meta.id] = {}
            self._versions[meta.id][meta.version] = meta
            
            # 更新索引
            self._update_indexes(meta)
            
            self._load_count += 1
    
    async def get(self, ref_id: str, version: Optional[str] = None) -> PromptMeta:
        """获取提示词"""
        with self._lock:
            # 检查别名
            actual_id = self._aliases.get(ref_id, ref_id)
            
            if actual_id not in self._prompts:
                self._cache_misses += 1
                raise PromptNotFoundError(f"提示词 '{ref_id}' 未找到")
            
            if version:
                if actual_id not in self._versions:
                    raise PromptNotFoundError(f"提示词 '{actual_id}' 未找到")
                
                if version not in self._versions[actual_id]:
                    raise PromptNotFoundError(
                        f"提示词 '{actual_id}' 版本 '{version}' 未找到"
                    )
                
                self._cache_hits += 1
                return self._versions[actual_id][version]
            
            self._cache_hits += 1
            return self._prompts[actual_id]
    
    async def get_by_alias(self, alias: str) -> PromptMeta:
        """通过别名获取提示词"""
        with self._lock:
            if alias not in self._aliases:
                raise PromptNotFoundError(f"别名 '{alias}' 未找到")
            
            return await self.get(self._aliases[alias])
    
    def get_prompt_meta(self, category: str, name: str) -> PromptMeta:
        """获取提示词元数据（同步方法）
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            PromptMeta: 提示词元数据
            
        Raises:
            PromptNotFoundError: 提示词未找到
        """
        prompt_id = f"{category}.{name}"
        
        # 检查别名
        actual_id = self._aliases.get(prompt_id, prompt_id)
        
        if actual_id not in self._prompts:
            raise PromptNotFoundError(f"提示词 '{prompt_id}' 未找到")
        
        return self._prompts[actual_id]
    
    async def list_versions(self, prompt_id: str) -> List[str]:
        """列出提示词的所有版本"""
        with self._lock:
            actual_id = self._aliases.get(prompt_id, prompt_id)
            
            if actual_id not in self._versions:
                return []
            
            versions = list(self._versions[actual_id].keys())
            # 按版本号排序
            versions.sort(key=self._version_key, reverse=True)
            return versions
    
    async def search(self, criteria: PromptSearchCriteria) -> PromptSearchResult:
        """搜索提示词"""
        with self._lock:
            results = []
            
            # 遍历所有提示词
            for prompt in self._prompts.values():
                if self._matches_criteria(prompt, criteria):
                    results.append(prompt)
            
            # 排序
            results = self._sort_results(results, criteria)
            
            # 分页
            total = len(results)
            offset = criteria.offset
            limit = criteria.limit
            paginated_results = results[offset:offset + limit]
            
            return PromptSearchResult(
                items=paginated_results,
                total=total,
                offset=offset,
                limit=limit
            )
    
    async def list_by_tag(self, tag: str) -> List[PromptMeta]:
        """按标签列出提示词"""
        with self._lock:
            if tag not in self._tags_index:
                return []
            
            prompt_ids = self._tags_index[tag]
            return [self._prompts[prompt_id] for prompt_id in prompt_ids]
    
    async def list_prompts(self, category: str, tags: Optional[List[str]] = None) -> List[PromptMeta]:
        """列出提示词（按类别和可选的标签过滤）"""
        with self._lock:
            if category not in self._categories_index:
                return []
            
            prompt_ids = self._categories_index[category]
            prompts = [self._prompts[prompt_id] for prompt_id in prompt_ids]
            
            # 按标签过滤
            if tags:
                tag_set = set(tags)
                prompts = [p for p in prompts if tag_set.intersection(set(p.tags))]
            
            return prompts
    
    async def list_by_category(self, category: str) -> List[PromptMeta]:
        """按分类列出提示词"""
        with self._lock:
            if category not in self._categories_index:
                return []
            
            prompt_ids = self._categories_index[category]
            return [self._prompts[prompt_id] for prompt_id in prompt_ids]
    
    async def update(self, prompt: PromptMeta) -> None:
        """更新提示词"""
        with self._lock:
            if prompt.id not in self._prompts:
                raise PromptNotFoundError(f"提示词 '{prompt.id}' 未找到")
            
            # 验证提示词
            await self._validate_prompt(prompt)
            
            # 更新时间戳
            prompt.update_timestamp()
            
            # 更新存储
            old_prompt = self._prompts[prompt.id]
            self._prompts[prompt.id] = prompt
            
            # 版本管理
            if prompt.id not in self._versions:
                self._versions[prompt.id] = {}
            self._versions[prompt.id][prompt.version] = prompt
            
            # 更新索引
            self._remove_from_indexes(old_prompt)
            self._update_indexes(prompt)
    
    async def delete(self, prompt_id: str) -> bool:
        """删除提示词"""
        with self._lock:
            actual_id = self._aliases.get(prompt_id, prompt_id)
            
            if actual_id not in self._prompts:
                return False
            
            prompt = self._prompts[actual_id]
            
            # 从存储中删除
            del self._prompts[actual_id]
            
            # 从版本管理中删除
            if actual_id in self._versions:
                del self._versions[actual_id]
            
            # 从索引中删除
            self._remove_from_indexes(prompt)
            
            # 从别名中删除
            aliases_to_remove = []
            for alias, pid in self._aliases.items():
                if pid == actual_id:
                    aliases_to_remove.append(alias)
            
            for alias in aliases_to_remove:
                del self._aliases[alias]
            
            return True
    
    async def add_alias(self, prompt_id: str, alias: str) -> None:
        """添加别名"""
        with self._lock:
            actual_id = self._aliases.get(prompt_id, prompt_id)
            
            if actual_id not in self._prompts:
                raise PromptNotFoundError(f"提示词 '{prompt_id}' 未找到")
            
            if alias in self._aliases:
                raise PromptRegistrationError(f"别名 '{alias}' 已存在")
            
            self._aliases[alias] = actual_id
    
    async def remove_alias(self, alias: str) -> bool:
        """移除别名"""
        with self._lock:
            if alias not in self._aliases:
                return False
            
            del self._aliases[alias]
            return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        with self._lock:
            active_count = sum(
                1 for prompt in self._prompts.values() 
                if prompt.status == PromptStatus.ACTIVE
            )
            
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
            
            return {
                "total_prompts": len(self._prompts),
                "active_prompts": active_count,
                "total_versions": sum(len(versions) for versions in self._versions.values()),
                "total_aliases": len(self._aliases),
                "total_tags": len(self._tags_index),
                "total_categories": len(self._categories_index),
                "load_count": self._load_count,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": hit_rate
            }
    
    async def reload(self) -> None:
        """重新加载所有提示词"""
        with self._lock:
            # 清空当前数据
            self._prompts.clear()
            self._versions.clear()
            self._aliases.clear()
            self._tags_index.clear()
            self._categories_index.clear()
            
            # 重置统计
            self._load_count = 0
            self._cache_hits = 0
            self._cache_misses = 0
            
            # 重新加载
            logger.warning("提示词注册表已清空，待重新加载")
    
    async def resolve_dependencies(self, prompt_name: str) -> List[PromptMeta]:
        """解析提示词依赖"""
        with self._lock:
            # 查找对应的提示词
            result = []
            for prompt in self._prompts.values():
                if prompt.name == prompt_name:
                    # 返回该提示词的所有依赖项
                    for dep_id in prompt.dependencies:
                        if dep_id in self._prompts:
                            result.append(self._prompts[dep_id])
                    return result
            
            return result
    
    async def validate_prompt(self, meta: PromptMeta) -> List[str]:
        """验证提示词，返回验证错误列表"""
        errors: List[str] = []
        
        try:
            await self._validate_prompt(meta)
        except PromptValidationError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"验证失败: {str(e)}")
        
        return errors
    
    async def _validate_prompt(self, prompt: PromptMeta) -> None:
        """验证提示词"""
        if not self._config.enable_validation:
            return
        
        # 基本验证
        if not prompt.content or not prompt.content.strip():
            raise PromptValidationError("提示词内容不能为空")
        
        if len(prompt.content) > self._config.max_content_length:
            raise PromptValidationError(
                f"提示词内容超过最大长度限制 ({self._config.max_content_length})"
            )
        
        # 自定义验证规则
        if prompt.validation:
            await self._apply_validation_rules(prompt)
    
    async def _apply_validation_rules(self, prompt: PromptMeta) -> None:
        """应用验证规则"""
        validation = prompt.validation
        if validation is None:
            return
        
        content = prompt.content
        
        # 长度验证
        if validation.min_length is not None and len(content) < validation.min_length:
            raise PromptValidationError(
                f"提示词内容长度小于最小限制 ({validation.min_length})"
            )
        
        if validation.max_length is not None and len(content) > validation.max_length:
            raise PromptValidationError(
                f"提示词内容长度超过最大限制 ({validation.max_length})"
            )
        
        # 正则表达式验证
        if validation.pattern is not None:
            import re
            if not re.match(validation.pattern, content):
                raise PromptValidationError("提示词内容不匹配指定的模式")
        
        # 禁用词汇验证
        if validation.forbidden_words is not None:
            content_lower = content.lower()
            for word in validation.forbidden_words:
                if word.lower() in content_lower:
                    raise PromptValidationError(f"提示词内容包含禁用词汇: {word}")
        
        # 必需关键词验证
        if validation.required_keywords is not None:
            content_lower = content.lower()
            for keyword in validation.required_keywords:
                if keyword.lower() not in content_lower:
                    raise PromptValidationError(f"提示词内容缺少必需关键词: {keyword}")
    
    def _update_indexes(self, prompt: PromptMeta) -> None:
        """更新索引"""
        # 标签索引
        for tag in prompt.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = set()
            self._tags_index[tag].add(prompt.id)
        
        # 分类索引
        if prompt.category:
            if prompt.category not in self._categories_index:
                self._categories_index[prompt.category] = set()
            self._categories_index[prompt.category].add(prompt.id)
    
    def _remove_from_indexes(self, prompt: PromptMeta) -> None:
        """从索引中移除"""
        # 标签索引
        for tag in prompt.tags:
            if tag in self._tags_index:
                self._tags_index[tag].discard(prompt.id)
                if not self._tags_index[tag]:
                    del self._tags_index[tag]
        
        # 分类索引
        if prompt.category and prompt.category in self._categories_index:
            self._categories_index[prompt.category].discard(prompt.id)
            if not self._categories_index[prompt.category]:
                del self._categories_index[prompt.category]
    
    def _matches_criteria(self, prompt: PromptMeta, criteria: PromptSearchCriteria) -> bool:
        """检查提示词是否匹配搜索条件"""
        # 查询匹配
        if criteria.query:
            query_lower = criteria.query.lower()
            if (query_lower not in prompt.name.lower() and 
                query_lower not in (prompt.description or "").lower() and
                query_lower not in prompt.content.lower()):
                return False
        
        # 类型匹配
        if criteria.type and prompt.type != criteria.type:
            return False
        
        # 状态匹配
        if criteria.status and prompt.status != criteria.status:
            return False
        
        # 分类匹配
        if criteria.category and prompt.category != criteria.category:
            return False
        
        # 标签匹配
        if criteria.tags:
            prompt_tags = set(prompt.tags)
            search_tags = set(criteria.tags)
            
            if criteria.tags_match_all:
                if not search_tags.issubset(prompt_tags):
                    return False
            else:
                if not search_tags.intersection(prompt_tags):
                    return False
        
        # 时间范围匹配
        if criteria.created_after and prompt.created_at < criteria.created_after:
            return False
        
        if criteria.created_before and prompt.created_at > criteria.created_before:
            return False
        
        if criteria.updated_after and prompt.updated_at < criteria.updated_after:
            return False
        
        if criteria.updated_before and prompt.updated_at > criteria.updated_before:
            return False
        
        return True
    
    def _sort_results(self, results: List[PromptMeta], criteria: PromptSearchCriteria) -> List[PromptMeta]:
        """排序结果"""
        reverse = criteria.sort_order == "desc"
        
        if criteria.sort_by == "name":
            return sorted(results, key=lambda p: p.name, reverse=reverse)
        elif criteria.sort_by == "created_at":
            return sorted(results, key=lambda p: p.created_at, reverse=reverse)
        elif criteria.sort_by == "updated_at":
            return sorted(results, key=lambda p: p.updated_at, reverse=reverse)
        elif criteria.sort_by == "priority":
            return sorted(results, key=lambda p: p.priority, reverse=reverse)
        else:
            return sorted(results, key=lambda p: getattr(p, criteria.sort_by), reverse=reverse)
    
    def _version_key(self, version: str) -> tuple:
        """版本号排序键"""
        try:
            parts = version.split('.')
            return tuple(int(p) for p in parts)
        except ValueError:
            return (0,)