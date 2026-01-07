"""
Модуль для работы с API различных провайдеров нейросетей.
Обрабатывает HTTP-запросы к OpenAI, DeepSeek, Groq и другим API.
"""

import requests
import json
import logging
import time
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import SSLError as Urllib3SSLError


# Настройка логирования
import os
import sys
from datetime import datetime

# Импортируем функцию для получения пользовательской директории
try:
    from db import get_user_data_dir
except ImportError:
    # Если db.py ещё не загружен, определяем функцию здесь
    def get_user_data_dir():
        if sys.platform == "win32":
            app_data_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ChatList")
        else:
            app_data_dir = os.path.join(os.path.expanduser("~"), ".chatlist")
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir, exist_ok=True)
        return app_data_dir

# Создаём папку для логов в пользовательской директории
# Используем %LocalAppData%\ChatList\logs для избежания проблем с правами доступа
user_data_dir = get_user_data_dir()
log_dir = os.path.join(user_data_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

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
    
    def __init__(self, api_key: str, api_url: str, timeout: int = 30, verify_ssl: bool = True):
        """
        Инициализация провайдера API.
        
        Args:
            api_key: API-ключ для аутентификации
            api_url: URL API-эндпоинта
            timeout: Таймаут запроса в секундах
            verify_ssl: Проверять ли SSL сертификаты (по умолчанию True)
        """
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session = None
    
    def _get_session(self) -> requests.Session:
        """
        Получить сессию requests с настройками retry для SSL ошибок.
        
        Returns:
            Настроенная сессия requests
        """
        if self._session is None:
            self._session = requests.Session()
            
            # Отключаем использование прокси по умолчанию
            # Это решает проблему с ProxyError при работе через VPN
            # Прокси будет использоваться только если явно указан USE_PROXY=true
            proxy_env = os.getenv('USE_PROXY', '').lower()
            if proxy_env not in ['true', '1', 'yes']:
                # Отключаем автоматическое использование прокси из переменных окружения
                self._session.trust_env = False
                # Явно устанавливаем пустые прокси, чтобы requests не пытался их использовать
                self._session.proxies = {
                    'http': None,
                    'https': None,
                    'no_proxy': '*'
                }
                logger.debug("Proxy disabled - using direct connection")
            
            # Настройка retry стратегии
            # Для работы через VPN нужны retry, но не для SSL ошибок
            # SSL ошибки обрабатываются вручную в send_request
            retry_strategy = Retry(
                total=2,  # Небольшое количество retry для временных сетевых проблем
                backoff_factor=0.5,  # Короткая задержка
                status_forcelist=[429, 500, 502, 503, 504],  # HTTP коды для retry
                allowed_methods=["POST", "GET"],
                raise_on_status=False,
                respect_retry_after_header=True
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        
        return self._session
    
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
                timeout=self.timeout,
                verify=self.verify_ssl
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
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    error_details = f"{error_details}. Response: {error_body}"
                except:
                    error_details = f"{error_details}. Status: {e.response.status_code}"
            logger.error(f"OpenAI API request error: {error_details}")
            return {
                "success": False,
                "error": error_details,
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
                timeout=self.timeout,
                verify=self.verify_ssl
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
                timeout=self.timeout,
                verify=self.verify_ssl
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
            "Content-Type": "application/json"
        }
        
        # Опциональные заголовки для OpenRouter (рекомендуется для отслеживания)
        # OpenRouter требует, чтобы заголовки были без префикса HTTP-
        referer_url = os.getenv("OPENROUTER_REFERER", "https://github.com/chatlist")
        app_name = os.getenv("OPENROUTER_APP_NAME", "ChatList")
        
        if referer_url:
            headers["HTTP-Referer"] = referer_url
        if app_name:
            headers["X-Title"] = app_name
        
        # Проверяем, что API-ключ не пустой
        if not self.api_key or self.api_key.strip() == "":
            logger.error("OpenRouter API key is empty or not set")
            return {
                "success": False,
                "error": "API key is not set. Please check your .env file.",
                "text": ""
            }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Проверяем, нужно ли отключить проверку SSL (для диагностики или VPN)
        disable_ssl = os.getenv('DISABLE_SSL_VERIFY', '').lower() in ['true', '1', 'yes']
        use_vpn = os.getenv('USE_VPN', '').lower() in ['true', '1', 'yes']
        
        if disable_ssl:
            logger.warning("SSL verification is DISABLED via DISABLE_SSL_VERIFY environment variable!")
            self.verify_ssl = False
        elif use_vpn:
            # Для VPN часто нужно отключать проверку SSL из-за особенностей туннелирования
            logger.info("VPN mode detected. Consider setting DISABLE_SSL_VERIFY=true if SSL errors occur.")
        
        # Попытки с обработкой SSL ошибок
        max_ssl_retries = 3
        ssl_retry_delay = 2  # секунды
        
        for attempt in range(max_ssl_retries):
            try:
                logger.info(f"Sending request to OpenRouter API (model: {model}, url: {self.api_url}, attempt: {attempt + 1})")
                # Логируем заголовки без ключа для безопасности
                safe_headers = {k: (v[:20] + "..." if k == "Authorization" else v) for k, v in headers.items()}
                logger.debug(f"Request headers: {safe_headers}")
                
                # Используем сессию с retry механизмом
                session = self._get_session()
                
                # Для работы через VPN увеличиваем таймаут
                use_vpn = os.getenv('USE_VPN', '').lower() in ['true', '1', 'yes']
                current_timeout = self.timeout
                if use_vpn:
                    current_timeout = self.timeout * 2  # Увеличиваем таймаут для VPN
                    logger.debug(f"VPN mode: increased timeout to {current_timeout}s")
                
                response = session.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=current_timeout,
                    verify=self.verify_ssl
                )
                
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                
                # Успешный ответ - обрабатываем и возвращаем
                text = self.parse_response(response)
                
                logger.info(f"OpenRouter API response received successfully")
                return {
                    "success": True,
                    "text": text,
                    "raw_response": response.json()
                }
                
            except requests.exceptions.ProxyError as proxy_error:
                error_msg = str(proxy_error)
                logger.warning(f"Proxy error on attempt {attempt + 1}/{max_ssl_retries}: {error_msg}")
                
                # Если прокси не настроен, отключаем его и пробуем снова
                if attempt == 0 and 'Cannot connect to proxy' in error_msg:
                    logger.info("Disabling proxy due to connection error, retrying without proxy...")
                    self._session.proxies = {'http': None, 'https': None}
                    self._session.trust_env = False
                    # Пробуем снова без прокси
                    continue
                
                if attempt < max_ssl_retries - 1:
                    time.sleep(ssl_retry_delay * (attempt + 1))
                    continue
                else:
                    user_friendly_error = (
                        "Ошибка подключения к прокси. "
                        "Проверьте настройки прокси или отключите его в настройках системы."
                    )
                    logger.error(f"Proxy error after {max_ssl_retries} attempts: {error_msg}")
                    return {
                        "success": False,
                        "error": user_friendly_error,
                        "text": ""
                    }
            except (requests.exceptions.SSLError, Urllib3SSLError) as ssl_error:
                error_msg = str(ssl_error)
                logger.warning(f"SSL error on attempt {attempt + 1}/{max_ssl_retries}: {error_msg}")
                
                if attempt < max_ssl_retries - 1:
                    # Ждём перед следующей попыткой
                    time.sleep(ssl_retry_delay * (attempt + 1))
                    continue
                else:
                    # Все попытки исчерпаны
                    user_friendly_error = (
                        "Ошибка SSL соединения. Возможные причины:\n"
                        "1. Проблемы с интернет-соединением\n"
                        "2. Блокировка антивирусом или файрволом\n"
                        "3. Устаревшие SSL сертификаты\n"
                        "4. Проблемы на стороне сервера OpenRouter\n\n"
                        "Попробуйте:\n"
                        "- Проверить интернет-соединение\n"
                        "- Временно отключить антивирус/файрвол\n"
                        "- Повторить запрос через несколько минут"
                    )
                    logger.error(f"SSL error after {max_ssl_retries} attempts: {error_msg}")
                    return {
                        "success": False,
                        "error": user_friendly_error,
                        "text": ""
                    }
            except requests.exceptions.Timeout:
                if attempt < max_ssl_retries - 1:
                    time.sleep(ssl_retry_delay)
                    continue
                else:
                    logger.error("OpenRouter API request timeout after retries")
                    return {
                        "success": False,
                        "error": "Request timeout. Проверьте интернет-соединение.",
                        "text": ""
                    }
            except requests.exceptions.RequestException as e:
                # Обработка HTTP ошибок (403, 404, 500 и т.д.)
                # Для 403 и других постоянных ошибок не делаем retry
                error_details = str(e)
                user_friendly_error = None
                
                # Проверяем код статуса
                status_code = None
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    
                    # Для 400, 403 и других постоянных ошибок не делаем retry
                    if status_code in [400, 403, 401, 404]:
                        try:
                            error_body = e.response.json()
                            logger.error(f"OpenRouter API error details: {error_body}")
                            
                            # Обрабатываем специфичные ошибки
                            if 'error' in error_body:
                                error_info = error_body['error']
                                
                                # Проверяем, есть ли вложенная ошибка от провайдера
                                if 'metadata' in error_info and 'raw' in error_info['metadata']:
                                    try:
                                        provider_error = json.loads(error_info['metadata']['raw'])
                                        if 'error' in provider_error:
                                            provider_error_code = provider_error['error'].get('code', '')
                                            provider_error_msg = provider_error['error'].get('message', '')
                                            
                                            # Специальная обработка для ошибки региона
                                            if 'unsupported_country_region_territory' in provider_error_code:
                                                # Определяем имя провайдера из ответа
                                                provider_name = error_info.get('provider_name', 'Unknown')
                                                
                                                user_friendly_error = (
                                                    f"Модель {model} (провайдер: {provider_name}) недоступна в вашем регионе. "
                                                    f"Попробуйте использовать другую модель через OpenRouter "
                                                    f"(например, meta-llama, anthropic/claude, google/gemini и др.). "
                                                    f"Ошибка: {provider_error_msg}"
                                                )
                                            else:
                                                # Обработка других ошибок от провайдера
                                                if 'Request not allowed' in provider_error_msg:
                                                    provider_name = error_info.get('provider_name', 'Unknown')
                                                    user_friendly_error = (
                                                        f"Модель {model} (провайдер: {provider_name}): запрос не разрешён. "
                                                        f"Возможно, требуется специальный API-ключ или модель недоступна для вашего аккаунта."
                                                    )
                                                else:
                                                    user_friendly_error = f"{provider_error_msg} (код: {provider_error_code})"
                                    except:
                                        pass
                                
                                # Обработка ошибок без вложенной структуры (например, 404, 400)
                                if not user_friendly_error and 'message' in error_info:
                                    error_msg = error_info['message']
                                    if 'No endpoints found' in error_msg:
                                        user_friendly_error = (
                                            f"Модель {model} не найдена в OpenRouter. "
                                            f"Возможно, модель была удалена или переименована. "
                                            f"Проверьте актуальный список моделей на https://openrouter.ai/models"
                                        )
                                    else:
                                        user_friendly_error = error_msg
                                
                                # Обработка ошибки 400 Bad Request
                                if status_code == 400 and not user_friendly_error:
                                    user_friendly_error = (
                                        f"Некорректный запрос для модели {model}. "
                                        f"Возможно, имя модели указано неверно или модель больше не поддерживается. "
                                        f"Проверьте актуальный список моделей на https://openrouter.ai/models"
                                    )
                            
                            error_details = f"{error_details}. Response: {error_body}"
                        except:
                            error_details = f"{error_details}. Status: {status_code}"
                    
                    # Для других ошибок (500, 502, 503, 504) можно попробовать retry
                    elif status_code in [500, 502, 503, 504]:
                        if attempt < max_ssl_retries - 1:
                            logger.warning(f"Server error {status_code}, retrying...")
                            time.sleep(ssl_retry_delay * (attempt + 1))
                            continue
                        else:
                            user_friendly_error = f"Ошибка сервера (код {status_code}). Попробуйте позже."
                
                # Если это постоянная ошибка (400, 403, 401, 404) или все попытки исчерпаны
                if status_code in [400, 403, 401, 404] or (status_code in [500, 502, 503, 504] and attempt >= max_ssl_retries - 1):
                    final_error = user_friendly_error if user_friendly_error else error_details
                    logger.error(f"OpenRouter API request error: {error_details}")
                    return {
                        "success": False,
                        "error": final_error,
                        "text": ""
                    }
                else:
                    # Для других RequestException продолжаем retry
                    if attempt < max_ssl_retries - 1:
                        time.sleep(ssl_retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": error_details,
                            "text": ""
                        }
            except Exception as e:
                # Обработка других неожиданных ошибок (не RequestException)
                logger.error(f"Unexpected error in OpenRouter API: {e}")
                if attempt < max_ssl_retries - 1:
                    time.sleep(ssl_retry_delay)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Неожиданная ошибка: {str(e)}",
                        "text": ""
                    }
        
        # Если мы дошли сюда, значит все попытки не удались, но не было возврата
        # Это не должно произойти, но на всякий случай
        return {
            "success": False,
            "error": "Не удалось выполнить запрос после всех попыток",
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
                   timeout: int = 30, verify_ssl: Optional[bool] = None) -> Optional[APIProvider]:
    """
    Фабричная функция для создания провайдера API.
    
    Args:
        provider_type: Тип провайдера ('openai', 'deepseek', 'groq', 'openrouter')
        api_key: API-ключ
        api_url: URL API
        timeout: Таймаут запроса
        verify_ssl: Проверять ли SSL сертификаты (None = использовать из окружения или True)
        
    Returns:
        Экземпляр провайдера или None
    """
    # Проверяем переменную окружения для отключения проверки SSL
    if verify_ssl is None:
        disable_ssl = os.getenv('DISABLE_SSL_VERIFY', '').lower() in ['true', '1', 'yes']
        verify_ssl = not disable_ssl
    
    provider_type = provider_type.lower()
    
    if provider_type == 'openai':
        return OpenAIProvider(api_key, api_url, timeout, verify_ssl)
    elif provider_type == 'deepseek':
        return DeepSeekProvider(api_key, api_url, timeout, verify_ssl)
    elif provider_type == 'groq':
        return GroqProvider(api_key, api_url, timeout, verify_ssl)
    elif provider_type == 'openrouter':
        return OpenRouterProvider(api_key, api_url, timeout, verify_ssl)
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

