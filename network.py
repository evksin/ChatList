"""
Модуль для работы с API различных провайдеров нейросетей.
Обрабатывает HTTP-запросы к OpenAI, DeepSeek, Groq и другим API.
"""

import requests
import json
import logging
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


# Настройка логирования
import os
from datetime import datetime

# Создаём папку для логов, если её нет
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настройка логирования в файл и консоль
log_file = os.path.join(log_dir, f"chatlist_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class APIProvider(ABC):
    """Базовый класс для провайдеров API."""
    
    def __init__(self, api_key: str, api_url: str, timeout: int = 30):
        """
        Инициализация провайдера API.
        
        Args:
            api_key: API-ключ для аутентификации
            api_url: URL API-эндпоинта
            timeout: Таймаут запроса в секундах
        """
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
    
    @abstractmethod
    def send_request(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправить запрос к API.
        
        Args:
            prompt: Текст промта
            model: Название модели (опционально)
            
        Returns:
            Словарь с ответом API или информацией об ошибке
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: requests.Response) -> str:
        """
        Парсить ответ от API и извлечь текст.
        
        Args:
            response: Объект ответа requests
            
        Returns:
            Текст ответа
        """
        pass


class OpenAIProvider(APIProvider):
    """Провайдер для OpenAI API."""
    
    def send_request(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Отправить запрос к OpenAI API."""
        if not model:
            model = "gpt-3.5-turbo"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            logger.info(f"Sending request to OpenAI API (model: {model})")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            text = self.parse_response(response)
            
            logger.info(f"OpenAI API response received successfully")
            return {
                "success": True,
                "text": text,
                "raw_response": result
            }
        except requests.exceptions.Timeout:
            logger.error("OpenAI API request timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "text": ""
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "text": ""
            }
    
    def parse_response(self, response: requests.Response) -> str:
        """Парсить ответ от OpenAI API."""
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing OpenAI response: {e}")
            return ""


class DeepSeekProvider(APIProvider):
    """Провайдер для DeepSeek API."""
    
    def send_request(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Отправить запрос к DeepSeek API."""
        if not model:
            model = "deepseek-chat"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            logger.info(f"Sending request to DeepSeek API (model: {model})")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            text = self.parse_response(response)
            
            logger.info(f"DeepSeek API response received successfully")
            return {
                "success": True,
                "text": text,
                "raw_response": response.json()
            }
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API request timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "text": ""
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
        except Exception as e:
            logger.error(f"Unexpected error in DeepSeek API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "text": ""
            }
    
    def parse_response(self, response: requests.Response) -> str:
        """Парсить ответ от DeepSeek API."""
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing DeepSeek response: {e}")
            return ""


class GroqProvider(APIProvider):
    """Провайдер для Groq API."""
    
    def send_request(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Отправить запрос к Groq API."""
        if not model:
            model = "llama2-70b-4096"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": model,
            "temperature": 0.7
        }
        
        try:
            logger.info(f"Sending request to Groq API (model: {model})")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            text = self.parse_response(response)
            
            logger.info(f"Groq API response received successfully")
            return {
                "success": True,
                "text": text,
                "raw_response": response.json()
            }
        except requests.exceptions.Timeout:
            logger.error("Groq API request timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "text": ""
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
        except Exception as e:
            logger.error(f"Unexpected error in Groq API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "text": ""
            }
    
    def parse_response(self, response: requests.Response) -> str:
        """Парсить ответ от Groq API."""
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing Groq response: {e}")
            return ""


class OpenRouterProvider(APIProvider):
    """Провайдер для OpenRouter API."""
    
    def send_request(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Отправить запрос к OpenRouter API."""
        if not model:
            model = "openai/gpt-3.5-turbo"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/chatlist",  # Опционально
            "X-Title": "ChatList"  # Опционально
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            logger.info(f"Sending request to OpenRouter API (model: {model})")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            text = self.parse_response(response)
            
            logger.info(f"OpenRouter API response received successfully")
            return {
                "success": True,
                "text": text,
                "raw_response": response.json()
            }
        except requests.exceptions.Timeout:
            logger.error("OpenRouter API request timeout")
            return {
                "success": False,
                "error": "Request timeout",
                "text": ""
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
        except Exception as e:
            logger.error(f"Unexpected error in OpenRouter API: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "text": ""
            }
    
    def parse_response(self, response: requests.Response) -> str:
        """Парсить ответ от OpenRouter API."""
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing OpenRouter response: {e}")
            return ""


def create_provider(provider_type: str, api_key: str, api_url: str, 
                   timeout: int = 30) -> Optional[APIProvider]:
    """
    Фабричная функция для создания провайдера API.
    
    Args:
        provider_type: Тип провайдера ('openai', 'deepseek', 'groq', 'openrouter')
        api_key: API-ключ
        api_url: URL API
        timeout: Таймаут запроса
        
    Returns:
        Экземпляр провайдера или None
    """
    provider_type = provider_type.lower()
    
    if provider_type == 'openai':
        return OpenAIProvider(api_key, api_url, timeout)
    elif provider_type == 'deepseek':
        return DeepSeekProvider(api_key, api_url, timeout)
    elif provider_type == 'groq':
        return GroqProvider(api_key, api_url, timeout)
    elif provider_type == 'openrouter':
        return OpenRouterProvider(api_key, api_url, timeout)
    else:
        logger.warning(f"Unknown provider type: {provider_type}")
        return None


def detect_provider_type(api_url: str) -> str:
    """
    Определить тип провайдера по URL.
    
    Args:
        api_url: URL API
        
    Returns:
        Тип провайдера
    """
    api_url_lower = api_url.lower()
    
    if 'openrouter' in api_url_lower:
        return 'openrouter'
    elif 'openai' in api_url_lower:
        return 'openai'
    elif 'deepseek' in api_url_lower:
        return 'deepseek'
    elif 'groq' in api_url_lower:
        return 'groq'
    else:
        # По умолчанию пробуем OpenAI формат
        return 'openai'

