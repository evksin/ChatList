"""
Модуль для улучшения промтов с помощью AI.
Использует существующую инфраструктуру для отправки запросов к моделям.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any
from models import ModelManager
from db import Database

logger = logging.getLogger(__name__)


class PromptImprover:
    """Класс для улучшения промтов с помощью AI."""
    
    def __init__(self, db: Database, model_manager: ModelManager):
        """
        Инициализация улучшателя промтов.
        
        Args:
            db: Экземпляр базы данных
            model_manager: Менеджер моделей для отправки запросов
        """
        self.db = db
        self.model_manager = model_manager
    
    def get_improver_model_id(self) -> Optional[int]:
        """
        Получить ID модели для улучшения промтов из настроек.
        
        Returns:
            ID модели или None, если модель не выбрана
        """
        model_id_str = self.db.get_setting('prompt_improver_model')
        if model_id_str:
            try:
                return int(model_id_str)
            except (ValueError, TypeError):
                return None
        return None
    
    def is_enabled(self) -> bool:
        """
        Проверить, включен ли ассистент улучшения промтов.
        
        Returns:
            True, если включен, False иначе
        """
        enabled = self.db.get_setting('prompt_improver_enabled', 'true')
        return enabled.lower() in ['true', '1', 'yes']
    
    def _create_system_prompt(self, original_prompt: str) -> str:
        """
        Создать системный промт для улучшения.
        
        Args:
            original_prompt: Исходный промт пользователя
            
        Returns:
            Системный промт для отправки модели
        """
        system_prompt = f"""Ты - эксперт по улучшению промптов для AI-моделей. Твоя задача - улучшить следующий промпт, сделав его более четким, конкретным и эффективным.

Исходный промпт:
{original_prompt}

Пожалуйста, предоставь ответ в следующем JSON-формате:
{{
    "improved": "улучшенная версия промпта",
    "alternatives": [
        "первый альтернативный вариант",
        "второй альтернативный вариант",
        "третий альтернативный вариант"
    ],
    "adaptations": {{
        "code": "версия для задач программирования",
        "analysis": "версия для аналитических задач",
        "creative": "версия для креативных задач"
    }}
}}

Если исходный промпт уже хорош, можешь оставить его почти без изменений, но все равно предоставь альтернативные варианты и адаптации."""
        
        return system_prompt
    
    def improve_prompt(self, original_prompt: str) -> Dict[str, Any]:
        """
        Улучшить промт с помощью AI.
        
        Args:
            original_prompt: Исходный промт для улучшения
            
        Returns:
            Словарь с результатами:
            {
                "success": bool,
                "improved": str,
                "alternatives": List[str],
                "adaptations": Dict[str, str],
                "error": str (если success=False)
            }
        """
        if not self.is_enabled():
            return {
                "success": False,
                "error": "Функция улучшения промтов отключена в настройках"
            }
        
        model_id = self.get_improver_model_id()
        if not model_id:
            return {
                "success": False,
                "error": "Модель для улучшения промтов не выбрана. Выберите модель в настройках."
            }
        
        # Получаем модель из БД
        model_data = self.db.get_model(model_id)
        if not model_data:
            return {
                "success": False,
                "error": f"Модель с ID {model_id} не найдена"
            }
        
        # Формируем системный промт
        system_prompt = self._create_system_prompt(original_prompt)
        
        # Отправляем запрос к модели
        try:
            result = self.model_manager.send_prompt_to_model(system_prompt, model_data)
            
            if not result.get('success', False):
                return {
                    "success": False,
                    "error": result.get('error', 'Неизвестная ошибка при запросе к модели')
                }
            
            # Парсим ответ
            response_text = result.get('text', '')
            parsed_result = self._parse_response(response_text)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error improving prompt: {e}")
            return {
                "success": False,
                "error": f"Ошибка при улучшении промта: {str(e)}"
            }
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Распарсить ответ от модели.
        
        Args:
            response_text: Текст ответа от модели
            
        Returns:
            Словарь с распарсенными данными
        """
        if not response_text or not response_text.strip():
            return {
                "success": False,
                "error": "Пустой ответ от модели"
            }
        
        # Пытаемся найти JSON в ответе (может быть в markdown коде или просто в тексте)
        # Ищем JSON блоки в markdown
        import re
        
        # Паттерн для JSON в markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                return self._validate_parsed_data(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from code block: {e}")
        
        # Пытаемся найти JSON без markdown
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                data = json.loads(json_str)
                return self._validate_parsed_data(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {e}")
        
        # Если JSON не найден, пытаемся распарсить как текст
        return self._parse_text_response(response_text)
    
    def _validate_parsed_data(self, data: Dict) -> Dict[str, Any]:
        """
        Валидировать и нормализовать распарсенные данные.
        
        Args:
            data: Распарсенные данные из JSON
            
        Returns:
            Валидированный словарь с данными
        """
        improved = data.get("improved", "").strip()
        alternatives = data.get("alternatives", [])
        adaptations = data.get("adaptations", {})
        
        # Валидация и нормализация
        if not improved:
            # Если улучшенной версии нет, используем исходный промт
            improved = ""
        
        # Убеждаемся, что alternatives - это список строк
        if not isinstance(alternatives, list):
            alternatives = []
        alternatives = [str(alt).strip() for alt in alternatives if alt and str(alt).strip()]
        alternatives = alternatives[:3]  # Максимум 3 варианта
        
        # Убеждаемся, что adaptations - это словарь
        if not isinstance(adaptations, dict):
            adaptations = {}
        
        # Нормализуем адаптации
        normalized_adaptations = {}
        for key in ['code', 'analysis', 'creative']:
            if key in adaptations and adaptations[key]:
                normalized_adaptations[key] = str(adaptations[key]).strip()
        
        return {
            "success": True,
            "improved": improved,
            "alternatives": alternatives,
            "adaptations": normalized_adaptations
        }
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """
        Распарсить текстовый ответ (fallback, если JSON не найден).
        
        Args:
            response_text: Текст ответа
            
        Returns:
            Словарь с распарсенными данными
        """
        lines = response_text.split('\n')
        improved = ""
        alternatives = []
        adaptations = {}
        
        current_section = None
        improved_lines = []
        alternative_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Определяем секцию по ключевым словам
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in ['улучшен', 'improved', 'лучший вариант', 'рекомендуемый']):
                current_section = 'improved'
                # Извлекаем текст после заголовка
                if ':' in line:
                    improved = line.split(':', 1)[1].strip()
                    if improved:
                        continue
                continue
            elif any(keyword in line_lower for keyword in ['альтернатив', 'alternative', 'вариант', 'другой']):
                current_section = 'alternatives'
                continue
            elif any(keyword in line_lower for keyword in ['адаптац', 'adaptation', 'для программирования', 'для анализа', 'для креатива']):
                current_section = 'adaptations'
                continue
            elif any(keyword in line_lower for keyword in ['код', 'code', 'программирование', 'programming']):
                if ':' in line:
                    adaptations['code'] = line.split(':', 1)[1].strip()
                current_section = 'adaptations'
                continue
            elif any(keyword in line_lower for keyword in ['анализ', 'analysis', 'аналитик']):
                if ':' in line:
                    adaptations['analysis'] = line.split(':', 1)[1].strip()
                current_section = 'adaptations'
                continue
            elif any(keyword in line_lower for keyword in ['креатив', 'creative', 'творческ']):
                if ':' in line:
                    adaptations['creative'] = line.split(':', 1)[1].strip()
                current_section = 'adaptations'
                continue
            
            # Добавляем текст в соответствующую секцию
            if current_section == 'improved':
                if not improved:
                    improved = line
                else:
                    improved_lines.append(line)
            elif current_section == 'alternatives':
                # Пропускаем маркеры списка
                clean_line = line.lstrip('- *•').strip()
                if clean_line and len(clean_line) > 10:  # Минимальная длина для валидного варианта
                    alternative_lines.append(clean_line)
            elif current_section == 'adaptations':
                # Обработка адаптаций уже сделана выше
                pass
        
        # Объединяем строки улучшенной версии
        if improved_lines:
            improved = improved + " " + " ".join(improved_lines)
        
        # Ограничиваем количество альтернатив
        alternatives = alternative_lines[:3]
        
        # Если ничего не найдено, используем весь текст как улучшенную версию
        if not improved:
            improved = response_text.strip()
            # Пытаемся извлечь хотя бы первую часть как улучшенную версию
            if len(improved) > 200:
                improved = improved[:200] + "..."
        
        return {
            "success": True,
            "improved": improved.strip(),
            "alternatives": alternatives,
            "adaptations": adaptations
        }

