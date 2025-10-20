"""提示词加载器实现"""

from pathlib import Path
from typing import Dict

from .interfaces import IPromptLoader, IPromptRegistry


class PromptLoader(IPromptLoader):
    """提示词加载器实现"""
    
    def __init__(self, registry: IPromptRegistry):
        self.registry = registry
        self._cache: Dict[str, str] = {}
        
    def load_prompt(self, category: str, name: str) -> str:
        """加载提示词内容"""
        cache_key = f"{category}.{name}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        # 获取元信息
        meta = self.registry.get_prompt_meta(category, name)
        
        # 加载提示词
        if meta.is_composite:
            content = self.load_composite_prompt(meta.path)
        else:
            content = self.load_simple_prompt(meta.path)
            
        # 缓存结果
        self._cache[cache_key] = content
        return content
        
    def load_simple_prompt(self, file_path: Path) -> str:
        """加载简单提示词"""
        if not file_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # 移除元信息部分（如果有）
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
                
        return content
        
    def load_composite_prompt(self, dir_path: Path) -> str:
        """加载复合提示词"""
        if not dir_path.exists():
            raise FileNotFoundError(f"复合提示词目录不存在: {dir_path}")
            
        # 加载主文件
        index_file = dir_path / "index.md"
        if not index_file.exists():
            raise FileNotFoundError(f"复合提示词缺少index.md: {dir_path}")
            
        content = self.load_simple_prompt(index_file)
        
        # 加载子章节文件
        chapter_files = []
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                chapter_files.append(file_path)
                
        # 按文件名排序
        chapter_files.sort(key=lambda x: x.name)
        
        # 合并内容
        for chapter_file in chapter_files:
            if chapter_file.name != "index.md":  # 跳过已加载的主文件
                chapter_content = self.load_simple_prompt(chapter_file)
                content += f"\n\n---\n\n{chapter_content}"
                
        return content
        
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()