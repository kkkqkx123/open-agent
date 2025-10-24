"""提示词加载器测试"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from tempfile import TemporaryDirectory

from src.domain.prompts.loader import PromptLoader
from src.domain.prompts.interfaces import IPromptRegistry
from src.domain.prompts.models import PromptMeta


class TestPromptLoader:
    """提示词加载器测试类"""
    
    @pytest.fixture
    def mock_registry(self):
        """模拟提示词注册表"""
        registry = Mock(spec=IPromptRegistry)
        
        # 简单提示词元信息
        simple_meta = PromptMeta(
            name="assistant",
            category="system",
            path=Path("prompts/system/assistant.md"),
            description="通用助手系统提示词",
            is_composite=False
        )
        
        # 复合提示词元信息
        composite_meta = PromptMeta(
            name="coder",
            category="system",
            path=Path("prompts/system/coder/"),
            description="代码生成专家系统提示词",
            is_composite=True
        )
        
        registry.get_prompt_meta.side_effect = lambda category, name: {
            ("system", "assistant"): simple_meta,
            ("system", "coder"): composite_meta
        }.get((category, name))
        
        return registry
    
    @pytest.fixture
    def loader(self, mock_registry):
        """创建提示词加载器实例"""
        return PromptLoader(mock_registry)
    
    def test_load_simple_prompt(self, loader):
        """测试加载简单提示词"""
        simple_content = """---
description: 通用助手提示词
---
你是一个通用助手，负责解答用户问题。"""
        
        with patch("builtins.open", mock_open(read_data=simple_content)):
            with patch.object(Path, 'exists', return_value=True):
                content = loader.load_prompt("system", "assistant")
                
                # 验证移除了元信息部分
                assert "你是一个通用助手" in content
                assert "description:" not in content
                assert "---" not in content
    
    def test_load_simple_prompt_without_metadata(self, loader):
        """测试加载无元信息的简单提示词"""
        simple_content = "你是一个通用助手，负责解答用户问题。"
        
        with patch("builtins.open", mock_open(read_data=simple_content)):
            with patch.object(Path, 'exists', return_value=True):
                content = loader.load_prompt("system", "assistant")
                
                assert content == simple_content
    
    def test_load_composite_prompt(self, loader):
        """测试加载复合提示词"""
        # 简化测试，只验证基本功能
        with patch.object(loader, 'load_simple_prompt') as mock_load_simple:
            # 设置模拟返回值
            mock_load_simple.return_value = "测试内容"
            
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'iterdir', return_value=[]):
                    content = loader.load_composite_prompt(Path("coder/"))
                    
                    assert content == "测试内容"
                    # 验证load_simple_prompt被调用了一次（用于index.md）
                    assert mock_load_simple.call_count == 1
    
    def test_load_prompt_caching(self, loader):
        """测试提示词缓存"""
        simple_content = "你是一个通用助手。"
        
        with patch("builtins.open", mock_open(read_data=simple_content)):
            with patch.object(Path, 'exists', return_value=True):
                # 第一次加载
                content1 = loader.load_prompt("system", "assistant")
                
                # 第二次加载（应该从缓存获取）
                content2 = loader.load_prompt("system", "assistant")
                
                assert content1 == content2
                # 验证只调用了一次文件读取
                assert loader.registry.get_prompt_meta.call_count == 1
    
    def test_clear_cache(self, loader):
        """测试清空缓存"""
        simple_content = "你是一个通用助手。"
        
        with patch("builtins.open", mock_open(read_data=simple_content)):
            with patch.object(Path, 'exists', return_value=True):
                # 加载提示词
                loader.load_prompt("system", "assistant")
                
                # 验证缓存不为空
                assert len(loader._cache) > 0
                
                # 清空缓存
                loader.clear_cache()
                
                # 验证缓存已清空
                assert len(loader._cache) == 0
    
    def test_load_simple_prompt_file_not_found(self, loader):
        """测试加载不存在的简单提示词文件"""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="提示词文件不存在"):
                loader.load_simple_prompt(Path("nonexistent.md"))
    
    def test_load_composite_prompt_directory_not_found(self, loader):
        """测试加载不存在的复合提示词目录"""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="复合提示词目录不存在"):
                loader.load_composite_prompt(Path("nonexistent/"))
    
    def test_load_composite_prompt_missing_index(self, loader):
        """测试复合提示词缺少index文件"""
        # 简化测试，直接模拟exists方法返回不同的值
        with patch.object(Path, 'exists') as mock_exists:
            # 第一次调用（目录）返回True，第二次调用（index文件）返回False
            mock_exists.side_effect = [True, False]
            
            with patch.object(Path, 'iterdir', return_value=[]):
                with pytest.raises(FileNotFoundError, match="复合提示词缺少index.md"):
                    loader.load_composite_prompt(Path("coder/"))
    
    def test_load_nonexistent_prompt(self, loader):
        """测试加载不存在的提示词"""
        loader.registry.get_prompt_meta.side_effect = ValueError("提示词不存在")
        
        with pytest.raises(ValueError, match="提示词不存在"):
            loader.load_prompt("system", "nonexistent")
    
    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    def test_load_simple_prompt_with_encoding(self, mock_file, loader):
        """测试加载简单提示词的编码处理"""
        with patch.object(Path, 'exists', return_value=True):
            loader.load_simple_prompt(Path("test.md"))
            
            # 验证以UTF-8编码打开文件
            mock_file.assert_called_once_with(Path("test.md"), 'r', encoding='utf-8')