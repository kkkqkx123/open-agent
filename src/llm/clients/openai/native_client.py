"""OpenAI Responses API原生客户端"""

import httpx
import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Generator


from .config import OpenAIConfig


class OpenAIResponsesClient:
    """OpenAI Responses API原生客户端"""

    def __init__(self, config: OpenAIConfig) -> None:
        """
        初始化Responses API客户端

        Args:
            config: OpenAI配置
        """
        self.config = config
        self.base_url = (
            config.base_url.rstrip("/")
            if config.base_url
            else "https://api.openai.com/v1"
        )
        self.api_key = config.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 添加自定义标头
        resolved_headers = config.get_resolved_headers()
        self.headers.update(resolved_headers)

    async def create_response(
        self, input_text: str, previous_response_id: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        创建Responses API请求（异步）

        Args:
            input_text: 输入文本
            previous_response_id: 之前的响应ID（用于对话上下文）
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: API响应
        """
        url = f"{self.base_url}/responses"

        payload = {"model": self.config.model_name, "input": input_text, **kwargs}

        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return dict(response.json())

    def create_response_sync(
        self, input_text: str, previous_response_id: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        创建Responses API请求（同步）

        Args:
            input_text: 输入文本
            previous_response_id: 之前的响应ID（用于对话上下文）
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: API响应
        """
        url = f"{self.base_url}/responses"

        payload = {"model": self.config.model_name, "input": input_text, **kwargs}

        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return dict(response.json())

    async def create_stream_response(
        self, input_text: str, previous_response_id: Optional[str] = None, **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        创建流式Responses API请求（异步）

        Args:
            input_text: 输入文本
            previous_response_id: 之前的响应ID（用于对话上下文）
            **kwargs: 其他参数

        Yields:
            Dict[str, Any]: 流式响应块
        """
        url = f"{self.base_url}/responses"

        payload = {
            "model": self.config.model_name,
            "input": input_text,
            "stream": True,
            **kwargs,
        }

        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST", url, headers=self.headers, json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        if data == "[DONE]":
                            break
                        try:
                            yield dict(json.loads(data))
                        except json.JSONDecodeError:
                            continue

    def create_stream_response_sync(
        self, input_text: str, previous_response_id: Optional[str] = None, **kwargs: Any
    ) -> Generator[Dict[str, Any], None, None]:
        """
        创建流式Responses API请求（同步）

        Args:
            input_text: 输入文本
            previous_response_id: 之前的响应ID（用于对话上下文）
            **kwargs: 其他参数

        Yields:
            Dict[str, Any]: 流式响应块
        """
        url = f"{self.base_url}/responses"

        payload = {
            "model": self.config.model_name,
            "input": input_text,
            "stream": True,
            **kwargs,
        }

        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        with httpx.Client(timeout=self.config.timeout) as client:
            with client.stream(
                "POST", url, headers=self.headers, json=payload
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        if data == "[DONE]":
                            break
                        try:
                            yield dict(json.loads(data))
                        except json.JSONDecodeError:
                            continue
