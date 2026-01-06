"""
Модуль для работы с нейросетевыми моделями.
Обеспечивает загрузку моделей из БД, работу с API-ключами и отправку запросов.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from db import get_db
from network import create_provider, detect_provider_type, APIProvider


# Загрузка переменных окружения из .env файла
load_dotenv()

logger = logging.getLogger(__name__)


class ModelManager:
    """Класс для управления моделями и отправки запросов."""
    
    def __init__(self, db_path: str = "chatlist.db", timeout: int = 30):
        """
        Инициализация менеджера моделей.
        
        Args:
            db_path: Путь к базе данных
            timeout: Таймаут для HTTP-запросов
        """
        self.db = get_db(db_path)
        self.timeout = timeout
        self._providers_cache = {}  # Кэш провайдеров для оптимизации
    
    def get_active_models(self) -> List[Dict]:
        """
        Получить список активных моделей из БД.
        
        Returns:
            Список словарей с информацией о моделях
        """
        return self.db.get_active_models()
    
    def get_all_models(self) -> List[Dict]:
        """
        Получить список всех моделей из БД.
        
        Returns:
            Список словарей с информацией о моделях
        """
        return self.db.get_all_models()
    
    def load_api_key(self, api_id: str) -> Optional[str]:
        """
        Загрузить API-ключ из переменной окружения.
        
        Args:
            api_id: Имя переменной окружения с API-ключом
            
        Returns:
            API-ключ или None, если не найден
        """
        api_key = os.getenv(api_id)
        if not api_key:
            logger.warning(f"API key not found for {api_id}. Check your .env file.")
        elif api_key.strip() == "":
            logger.warning(f"API key for {api_id} is empty. Check your .env file.")
            return None
        else:
            # Логируем только факт загрузки, но не сам ключ
            logger.debug(f"API key loaded for {api_id} (length: {len(api_key)})")
        return api_key
    
    def _get_provider(self, model: Dict) -> Optional[APIProvider]:
        """
        Получить провайдер API для модели (с кэшированием).
        
        Args:
            model: Словарь с информацией о модели
            
        Returns:
            Экземпляр провайдера или None
        """
        model_id = model['id']
        
        # Проверяем кэш
        if model_id in self._providers_cache:
            return self._providers_cache[model_id]
        
        # Загружаем API-ключ
        api_key = self.load_api_key(model['api_id'])
        if not api_key:
            logger.error(f"API key not found for model {model['name']}")
            return None
        
        # Определяем тип провайдера
        provider_type = detect_provider_type(model['api_url'])
        
        # Создаём провайдер
        provider = create_provider(
            provider_type=provider_type,
            api_key=api_key,
            api_url=model['api_url'],
            timeout=self.timeout
        )
        
        if provider:
            self._providers_cache[model_id] = provider
        
        return provider
    
    def send_prompt_to_model(self, prompt: str, model: Dict) -> Dict[str, Any]:
        """
        Отправить промт в конкретную модель.
        
        Args:
            prompt: Текст промта
            model: Словарь с информацией о модели
            
        Returns:
            Словарь с результатом запроса
        """
        provider = self._get_provider(model)
        
        if not provider:
            return {
                "success": False,
                "error": f"Provider not available for model {model['name']}",
                "text": "",
                "model_name": model['name']
            }
        
        try:
            # Используем model_name из БД, если указано и не пустое
            # Если model_name не указано, используем имя модели из БД (name)
            api_model_name = model.get('model_name')
            if not api_model_name or api_model_name.strip() == '':
                # Если model_name не указано, используем name как имя модели для API
                # Это работает для случаев, когда name уже содержит правильное имя модели (например, "anthropic/claude-3-haiku")
                api_model_name = model.get('name')
            
            result = provider.send_request(prompt, model=api_model_name)
            result["model_name"] = model['name']
            result["model_id"] = model['id']
            return result
        except Exception as e:
            logger.error(f"Error sending prompt to {model['name']}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "model_name": model['name'],
                "model_id": model['id']
            }
    
    def send_prompt_to_all_active(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Отправить промт во все активные модели.
        
        Args:
            prompt: Текст промта
            
        Returns:
            Список результатов от всех моделей
        """
        active_models = self.get_active_models()
        results = []
        
        logger.info(f"Sending prompt to {len(active_models)} active models")
        
        for model in active_models:
            result = self.send_prompt_to_model(prompt, model)
            results.append(result)
        
        return results
    
    def clear_cache(self):
        """Очистить кэш провайдеров."""
        self._providers_cache.clear()
        logger.info("Provider cache cleared")
    
    def format_request_for_api(self, prompt: str, provider_type: str) -> Dict:
        """
        Форматировать запрос для конкретного типа API.
        
        Args:
            prompt: Текст промта
            provider_type: Тип провайдера
            
        Returns:
            Словарь с данными запроса
        """
        provider_type = provider_type.lower()
        
        if provider_type in ['openai', 'deepseek']:
            return {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        elif provider_type == 'groq':
            return {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        else:
            # Формат по умолчанию (OpenAI-совместимый)
            return {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
    
    def parse_response_from_api(self, response_data: Dict, provider_type: str) -> str:
        """
        Парсить ответ от API конкретного типа.
        
        Args:
            response_data: Данные ответа от API
            provider_type: Тип провайдера
            
        Returns:
            Текст ответа
        """
        try:
            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            elif "content" in response_data:
                return response_data["content"]
            else:
                logger.warning(f"Unexpected response format from {provider_type}")
                return ""
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing response from {provider_type}: {e}")
            return ""


# Глобальный экземпляр менеджера моделей
_model_manager_instance = None


def get_model_manager(db_path: str = "chatlist.db", timeout: int = 30) -> ModelManager:
    """
    Получить экземпляр менеджера моделей (singleton).
    
    Args:
        db_path: Путь к базе данных
        timeout: Таймаут для запросов
        
    Returns:
        Экземпляр ModelManager
    """
    global _model_manager_instance
    if _model_manager_instance is None:
        _model_manager_instance = ModelManager(db_path, timeout)
    return _model_manager_instance

