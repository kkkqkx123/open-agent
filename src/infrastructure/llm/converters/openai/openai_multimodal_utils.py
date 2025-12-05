"""OpenAI多模态工具类

提供OpenAI API的多模态内容处理功能。
"""

from typing import Dict, Any, List, Union, Optional
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils


class OpenAIMultimodalUtils(BaseMultimodalUtils):
    """OpenAI多模态工具类
    
    提供OpenAI API特定的多模态内容处理功能。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI多模态工具"""
        super().__init__()
        self._supported_image_formats = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        self._max_image_size = 20 * 1024 * 1024  # 20MB
    
    def process_content_to_provider_format(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """将内容转换为OpenAI格式"""
        if isinstance(content, str):
            return [self._create_text_content(content)]
        elif isinstance(content, list):
            return self._process_content_list(content)
        else:
            return [self._create_text_content(str(content))]
    
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从OpenAI格式内容中提取文本"""
        return self._extract_text_from_content_list(content)
    
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证OpenAI格式内容"""
        return self._validate_openai_content(content)
    
    def _create_text_content(self, text: str) -> Dict[str, Any]:
        """创建OpenAI格式的文本内容"""
        return {
            "type": "text",
            "text": text
        }
    
    def _process_dict_content(self, content_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理字典内容为OpenAI格式"""
        content_type = content_dict.get("type")
        
        if content_type == "text":
            return self._create_text_content(content_dict.get("text", ""))
        elif content_type == "image":
            return self._process_image_content(content_dict)
        elif content_type == "image_url":
            # 已经是OpenAI格式，直接返回
            return content_dict
        else:
            # 未知类型，转换为文本
            return self._create_text_content(str(content_dict))
    
    def _process_image_content(self, image_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理图像内容为OpenAI格式"""
        source = image_item.get("source", {})
        if not source:
            self.logger.warning("图像内容缺少source字段")
            return None
        
        # OpenAI使用image_url格式
        if source.get("type") == "base64":
            media_type = source.get("media_type", "image/jpeg")
            data = source.get("data", "")
            
            if not data:
                self.logger.warning("图像内容缺少base64数据")
                return None
            
            # 构建data URL
            data_url = f"data:{media_type};base64,{data}"
            
            return {
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            }
        elif source.get("type") == "url":
            # 直接使用URL
            url = source.get("url", "")
            if not url:
                self.logger.warning("图像内容缺少URL")
                return None
            
            return {
                "type": "image_url",
                "image_url": {
                    "url": url
                }
            }
        else:
            self.logger.warning(f"不支持的图像源类型: {source.get('type')}")
            return None
    
    def _validate_openai_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证OpenAI格式内容"""
        errors = []
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        if not content:
            errors.append("内容列表不能为空")
            return errors
        
        for i, item in enumerate(content):
            item_errors = self._validate_openai_content_item(item, i)
            errors.extend(item_errors)
        
        return errors
    
    def _validate_openai_content_item(self, item: Dict[str, Any], index: int) -> List[str]:
        """验证OpenAI格式内容项"""
        errors = []
        
        if not isinstance(item, dict):
            errors.append(f"内容项 {index} 必须是字典")
            return errors
        
        content_type = item.get("type")
        if not content_type:
            errors.append(f"内容项 {index} 缺少type字段")
            return errors
        
        if content_type == "text":
            text_errors = self._validate_text_item(item, index)
            errors.extend(text_errors)
        elif content_type == "image_url":
            image_errors = self._validate_image_url_item(item, index)
            errors.extend(image_errors)
        else:
            errors.append(f"内容项 {index} 有不支持的类型: {content_type}")
        
        return errors
    
    def _validate_text_item(self, text_item: Dict[str, Any], index: int) -> List[str]:
        """验证文本内容项"""
        errors = []
        
        text = text_item.get("text")
        if not isinstance(text, str):
            errors.append(f"文本内容项 {index} 的text字段必须是字符串")
        
        return errors
    
    def _validate_image_url_item(self, image_item: Dict[str, Any], index: int) -> List[str]:
        """验证图像URL内容项"""
        errors = []
        
        image_url = image_item.get("image_url")
        if not isinstance(image_url, dict):
            errors.append(f"图像内容项 {index} 的image_url字段必须是字典")
            return errors
        
        url = image_url.get("url")
        if not isinstance(url, str):
            errors.append(f"图像内容项 {index} 的url字段必须是字符串")
        elif not url.strip():
            errors.append(f"图像内容项 {index} 的url字段不能为空")
        else:
            # 验证URL格式
            url_errors = self._validate_image_url(url, index)
            errors.extend(url_errors)
        
        return errors
    
    def _validate_image_url(self, url: str, index: int) -> List[str]:
        """验证图像URL"""
        errors = []
        
        if url.startswith("data:"):
            # Base64编码的图像
            data_url_errors = self._validate_data_url(url, index)
            errors.extend(data_url_errors)
        elif url.startswith(("http://", "https://")):
            # HTTP/HTTPS URL
            # 这里可以添加更多的URL验证逻辑
            pass
        else:
            errors.append(f"图像内容项 {index} 的url格式无效")
        
        return errors
    
    def _validate_data_url(self, data_url: str, index: int) -> List[str]:
        """验证Data URL格式"""
        errors = []
        
        try:
            # 解析Data URL格式: data:[<mediatype>][;base64],<data>
            if not data_url.startswith("data:"):
                errors.append(f"图像内容项 {index} 的data URL格式无效")
                return errors
            
            # 找到逗号位置
            comma_index = data_url.find(",")
            if comma_index == -1:
                errors.append(f"图像内容项 {index} 的data URL缺少逗号分隔符")
                return errors
            
            # 提取媒体类型和数据部分
            media_part = data_url[5:comma_index]  # 去掉"data:"前缀
            data_part = data_url[comma_index + 1:]
            
            # 验证媒体类型
            if not media_part:
                errors.append(f"图像内容项 {index} 的data URL缺少媒体类型")
            else:
                # 检查是否为base64编码
                if ";base64" in media_part:
                    media_type = media_part.replace(";base64", "")
                    
                    # 验证媒体类型
                    if media_type not in self._supported_image_formats:
                        errors.append(f"图像内容项 {index} 的媒体类型 '{media_type}' 不支持")
                    
                    # 验证base64数据
                    try:
                        import base64
                        base64.b64decode(data_part)
                    except Exception:
                        errors.append(f"图像内容项 {index} 的base64数据无效")
                else:
                    errors.append(f"图像内容项 {index} 的data URL必须是base64编码")
            
            # 估算数据大小（base64编码后的字符串长度）
            estimated_size = len(data_part) * 3 // 4  # 近似解码后的大小
            if estimated_size > self._max_image_size:
                errors.append(f"图像内容项 {index} 的大小超过限制 ({self._max_image_size / 1024 / 1024:.1f}MB)")
        
        except Exception as e:
            errors.append(f"图像内容项 {index} 的data URL解析失败: {e}")
        
        return errors
    
    def create_image_content_from_file(
        self, 
        image_path: str, 
        detail: str = "auto"
    ) -> Dict[str, Any]:
        """从文件路径创建OpenAI格式的图像内容
        
        Args:
            image_path: 图像文件路径
            detail: 图像细节级别 ("low", "high", "auto")
            
        Returns:
            Dict[str, Any]: OpenAI格式的图像内容
        """
        import base64
        import mimetypes
        
        try:
            # 自动检测媒体类型
            media_type, _ = mimetypes.guess_type(image_path)
            if not media_type:
                media_type = "image/jpeg"  # 默认
            
            # 验证媒体类型
            if media_type not in self._supported_image_formats:
                raise ValueError(f"不支持的图像格式: {media_type}")
            
            # 读取并编码图像
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # 检查大小限制
            if len(image_data) > self._max_image_size:
                raise ValueError(f"图像大小超过限制: {len(image_data)} bytes")
            
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            data_url = f"data:{media_type};base64,{encoded_data}"
            
            return {
                "type": "image_url",
                "image_url": {
                    "url": data_url,
                    "detail": detail
                }
            }
        except Exception as e:
            self.logger.error(f"创建图像内容失败: {e}")
            raise
    
    def create_image_content_from_url(
        self, 
        url: str, 
        detail: str = "auto"
    ) -> Dict[str, Any]:
        """从URL创建OpenAI格式的图像内容
        
        Args:
            url: 图像URL
            detail: 图像细节级别 ("low", "high", "auto")
            
        Returns:
            Dict[str, Any]: OpenAI格式的图像内容
        """
        return {
            "type": "image_url",
            "image_url": {
                "url": url,
                "detail": detail
            }
        }
    
    def create_image_content_from_base64(
        self, 
        base64_data: str, 
        media_type: str = "image/jpeg",
        detail: str = "auto"
    ) -> Dict[str, Any]:
        """从base64数据创建OpenAI格式的图像内容
        
        Args:
            base64_data: base64编码的图像数据
            media_type: 媒体类型
            detail: 图像细节级别 ("low", "high", "auto")
            
        Returns:
            Dict[str, Any]: OpenAI格式的图像内容
        """
        # 验证媒体类型
        if media_type not in self._supported_image_formats:
            raise ValueError(f"不支持的图像格式: {media_type}")
        
        # 验证base64数据
        try:
            import base64
            decoded_data = base64.b64decode(base64_data)
            
            # 检查大小限制
            if len(decoded_data) > self._max_image_size:
                raise ValueError(f"图像大小超过限制: {len(decoded_data)} bytes")
        except Exception as e:
            raise ValueError(f"无效的base64数据: {e}")
        
        data_url = f"data:{media_type};base64,{base64_data}"
        
        return {
            "type": "image_url",
            "image_url": {
                "url": data_url,
                "detail": detail
            }
        }
    
    def _get_max_image_size(self) -> int:
        """获取最大图像大小限制"""
        return self._max_image_size
    
    def _get_supported_image_formats(self) -> set:
        """获取支持的图像格式"""
        return self._supported_image_formats
    
    def extract_image_urls_from_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """从内容中提取图像URL列表
        
        Args:
            content: OpenAI格式的内容列表
            
        Returns:
            List[str]: 图像URL列表
        """
        urls = []
        
        for item in content:
            if isinstance(item, dict) and item.get("type") == "image_url":
                image_url = item.get("image_url", {})
                url = image_url.get("url")
                if url:
                    urls.append(url)
        
        return urls
    
    def count_tokens_in_content(self, content: List[Dict[str, Any]]) -> int:
        """估算内容中的token数量（粗略估算）
        
        Args:
            content: OpenAI格式的内容列表
            
        Returns:
            int: 估算的token数量
        """
        total_tokens = 0
        
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text = item.get("text", "")
                    # 粗略估算：1个token约等于4个字符（英文）或1.5个字符（中文）
                    # 这里使用简单的字符数除以4的估算
                    total_tokens += max(1, len(text) // 4)
                elif item.get("type") == "image_url":
                    # 图像的token计算比较复杂，这里使用OpenAI的估算规则
                    image_url = item.get("image_url", {})
                    detail = image_url.get("detail", "auto")
                    
                    if detail == "low":
                        total_tokens += 85  # 低分辨率图像约85个tokens
                    elif detail == "high":
                        total_tokens += 170  # 高分辨率图像约170个tokens
                    else:
                        total_tokens += 85  # 默认使用低分辨率的估算
        
        return total_tokens
    
    def optimize_content_for_context(
        self, 
        content: List[Dict[str, Any]], 
        max_tokens: int
    ) -> List[Dict[str, Any]]:
        """优化内容以适应上下文长度限制
        
        Args:
            content: OpenAI格式的内容列表
            max_tokens: 最大token数量
            
        Returns:
            List[Dict[str, Any]]: 优化后的内容列表
        """
        current_tokens = self.count_tokens_in_content(content)
        
        if current_tokens <= max_tokens:
            return content
        
        optimized_content = []
        remaining_tokens = max_tokens
        
        # 优先保留文本内容，然后处理图像
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text = item.get("text", "")
                    text_tokens = max(1, len(text) // 4)
                    
                    if text_tokens <= remaining_tokens:
                        optimized_content.append(item)
                        remaining_tokens -= text_tokens
                    else:
                        # 截断文本
                        max_chars = remaining_tokens * 4
                        truncated_text = text[:max_chars]
                        optimized_content.append({
                            "type": "text",
                            "text": truncated_text
                        })
                        remaining_tokens = 0
                        break
                
                elif item.get("type") == "image_url" and remaining_tokens >= 85:
                    # 只有在有足够token时才包含图像
                    image_url = item.get("image_url", {})
                    detail = image_url.get("detail", "auto")
                    
                    image_tokens = 85 if detail == "low" else 170
                    if image_tokens <= remaining_tokens:
                        optimized_content.append(item)
                        remaining_tokens -= image_tokens
        
        return optimized_content