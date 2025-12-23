"""
LLM的API调用封装 
"""

import os
import json
from typing import List, Dict, Optional, Iterator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry  
from utils.logger import get_logger

logger = get_logger(__name__)


class DeepseekClient:
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        初始化Deepseek客户端
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1")
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  
        
        self.session = requests.Session()
        # total=3: 总共重试3次
        # backoff_factor=1: 每次重试间隔增加 (1s, 2s, 4s...)
        # status_forcelist: 遇到 502/503/504 等服务器错误时重试
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # -------------------------------------------

        if not self.api_key:
            logger.warning("未设置DEEPSEEK_API_KEY，LLM功能不可用")
        else:
            logger.info(f"Deepseek客户端已初始化，API URL: {self.base_url}, 模型: {self.model}")
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, 
             temperature: float = 0.7, max_tokens: int = 2000, stream: bool = False) -> Dict:
        """发送聊天请求"""
        if not self.api_key:
            return {
                "error": "API密钥未设置",
                "answer": "请先设置DEEPSEEK_API_KEY环境变量或在配置中提供API密钥"
            }
        
        model = model or self.model
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            if stream:
                return self._stream_chat(url, headers, data)
            else:
                logger.debug(f"调用Deepseek API: {url}")
                response = self.session.post(
                    url, 
                    headers=headers, 
                    json=data, 
                    timeout=(10, 100), 
                    verify=True  
                )
                # -------------------------------------------
                
                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = json.dumps(error_json, ensure_ascii=False)
                    except:
                        pass
                    return {
                        "error": f"API请求失败 (状态码: {response.status_code})",
                        "error_detail": error_detail,
                        "answer": f"抱歉，LLM服务返回错误 (状态码: {response.status_code})。"
                    }
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" not in result or len(result["choices"]) == 0:
                    return {
                        "error": "API响应格式错误",
                        "answer": "抱歉，LLM服务返回了无效的响应格式"
                    }
                
                return {
                    "answer": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                    "model": result.get("model", model)
                }

        except requests.exceptions.ReadTimeout:
            # 专门捕获超时错误
            error_msg = "API响应超时，模型思考时间过长"
            logger.error(error_msg)
            return {"error": error_msg, "answer": "抱歉，由于问题过于复杂，服务器响应超时，请重试。"}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API请求失败: {str(e)}"
            logger.error(f"{error_msg}")
            return {
                "error": error_msg,
                "answer": f"抱歉，LLM服务暂时不可用: {str(e)}"
            }
        except Exception as e:
            error_msg = f"处理响应时出错: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {
                "error": error_msg,
                "answer": f"抱歉，处理响应时出现错误: {str(e)}"
            }
    
    def _stream_chat(self, url: str, headers: Dict, data: Dict) -> Iterator[str]:
        """流式聊天响应"""
        try:
            response = self.session.post(
                url, 
                headers=headers, 
                json=data, 
                stream=True, 
                timeout=(10, 100),
                verify=True  
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_text = line_text[6:]
                        if data_text == '[DONE]':
                            break
                        try:
                            data_json = json.loads(data_text)
                            if 'choices' in data_json and len(data_json['choices']) > 0:
                                delta = data_json['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"流式响应错误: {str(e)}"
    
    def is_available(self) -> bool:
        """检查API是否可用"""
        return bool(self.api_key)