"""客户端元数据服务

负责获取和管理LLM客户端的元数据信息。
"""

from typing import Any, Dict

from src.interfaces.llm import ILLMClient


class ClientMetadataService:
    """客户端元数据服务
    
    负责获取LLM客户端的元数据信息，如模型名称、提供商、能力等。
    """
    
    def get_client_info(self, client: ILLMClient, name: str) -> Dict[str, Any]:
        """
        获取客户端信息
        
        Args:
            client: LLM客户端实例
            name: 客户端名称
            
        Returns:
            Dict[str, Any]: 客户端信息字典
        """
        # 获取基础模型信息
        model_info = self._safe_get_model_info(client)
        
        # 构建客户端信息
        return {
            "name": name,
            "model": model_info.get("model_name", "unknown"),
            "provider": model_info.get("provider", "unknown"),
            "capabilities": self._get_capabilities(client),
            "model_info": model_info,
            "client_type": type(client).__name__,
        }
    
    def _safe_get_model_info(self, client: ILLMClient) -> Dict[str, Any]:
        """
        安全地获取模型信息
        
        Args:
            client: LLM客户端实例
            
        Returns:
            Dict[str, Any]: 模型信息
        """
        try:
            return client.get_model_info()
        except Exception:
            # 如果客户端不支持get_model_info，返回默认值
            return {
                "model_name": getattr(client, 'model_name', 'unknown'),
                "provider": getattr(client, 'provider', 'unknown'),
            }
    
    def _get_capabilities(self, client: ILLMClient) -> Dict[str, bool]:
        """
        获取客户端能力
        
        Args:
            client: LLM客户端实例
            
        Returns:
            Dict[str, bool]: 能力字典
        """
        capabilities = {}
        
        # 检查函数调用支持
        capabilities["supports_function_calling"] = self._safe_check_function_calling(client)
        
        # 检查流式生成支持
        capabilities["supports_streaming"] = hasattr(client, 'stream_generate_async') and callable(getattr(client, 'stream_generate_async'))
        
        # 检查异步生成支持
        capabilities["supports_async"] = hasattr(client, 'generate_async') and callable(getattr(client, 'generate_async'))
        
        # 检查同步生成支持
        capabilities["supports_sync"] = hasattr(client, 'generate') and callable(getattr(client, 'generate'))
        
        # 检查token计数支持
        
        return capabilities
    
    def _safe_check_function_calling(self, client: ILLMClient) -> bool:
        """
        安全地检查函数调用支持
        
        Args:
            client: LLM客户端实例
            
        Returns:
            bool: 是否支持函数调用
        """
        try:
            return client.supports_function_calling()
        except Exception:
            # 如果调用失败，假设不支持
            return False
    
    def get_client_summary(self, client: ILLMClient, name: str) -> Dict[str, Any]:
        """
        获取客户端摘要信息
        
        Args:
            client: LLM客户端实例
            name: 客户端名称
            
        Returns:
            Dict[str, Any]: 客户端摘要
        """
        info = self.get_client_info(client, name)
        capabilities = info["capabilities"]
        
        # 生成能力描述
        capability_descriptions = []
        if capabilities["supports_function_calling"]:
            capability_descriptions.append("函数调用")
        if capabilities["supports_streaming"]:
            capability_descriptions.append("流式生成")
        if capabilities["supports_async"]:
            capability_descriptions.append("异步调用")
        if capabilities["supports_token_counting"]:
            capability_descriptions.append("Token计数")
        
        return {
            "name": name,
            "model": info["model"],
            "provider": info["provider"],
            "capabilities": ", ".join(capability_descriptions) if capability_descriptions else "基础生成",
            "is_advanced": len(capability_descriptions) >= 2,
        }
    
    def compare_clients(self, clients: Dict[str, ILLMClient]) -> Dict[str, Any]:
        """
        比较多个客户端的能力
        
        Args:
            clients: 客户端名称到实例的映射
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        comparison = {
            "clients": {},
            "capabilities_matrix": {},
            "summary": {
                "total_clients": len(clients),
                "providers": set(),
                "models": set(),
                "capability_counts": {},
            }
        }
        
        # 收集每个客户端的信息
        for name, client in clients.items():
            info = self.get_client_info(client, name)
            comparison["clients"][name] = info
            
            # 更新摘要信息
            comparison["summary"]["providers"].add(info["provider"])
            comparison["summary"]["models"].add(info["model"])
            
            # 构建能力矩阵
            for capability, supported in info["capabilities"].items():
                if capability not in comparison["capabilities_matrix"]:
                    comparison["capabilities_matrix"][capability] = {}
                comparison["capabilities_matrix"][capability][name] = supported
                
                # 统计能力数量
                if supported:
                    comparison["summary"]["capability_counts"][capability] = comparison["summary"]["capability_counts"].get(capability, 0) + 1
        
        # 转换集合为列表
        comparison["summary"]["providers"] = list(comparison["summary"]["providers"])
        comparison["summary"]["models"] = list(comparison["summary"]["models"])
        
        return comparison