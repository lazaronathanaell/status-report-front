import logging
from typing import Dict, Any, Tuple, Type
from pydantic import BaseModel, ValidationError, TypeAdapter

def validate_field_with_model(field_name: str, value: Any, model: Type[BaseModel]) -> bool:
    """
    Valida se um valor específico é compatível com o tipo esperado de um campo no modelo Pydantic.
    
    Args:
        field_name: Nome do campo no modelo
        value: Valor a ser validado
        model: Classe do modelo Pydantic
        
    Returns:
        bool: True se o valor é válido para o campo, False caso contrário
    """
    try:
        # Obtém as informações do campo no modelo
        if field_name not in model.model_fields:
            logging.error(f"Campo '{field_name}' não existe no modelo {model.__name__}")
            return False
        
        field_info = model.model_fields[field_name]
        field_type = field_info.annotation
        
        # Usa TypeAdapter para validar apenas o tipo do campo individual
        type_adapter = TypeAdapter(field_type)
        type_adapter.validate_python(value)
        
        return True
        
    except ValidationError as e:
        logging.error(f"Erro de validação no campo '{field_name}': {e}")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado ao validar campo '{field_name}': {e}")
        return False