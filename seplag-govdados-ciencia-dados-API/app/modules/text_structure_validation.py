import logging
from typing import Optional, Dict, Any, Tuple
import importlib
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.pdf import PDF
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def get_pydantic_model(doc_type: str, model_type: str):
    """
    Obtém dinamicamente o modelo Pydantic correspondente ao tipo de documento.
    
    Args:
        doc_type (str): Tipo do documento (ex: "portaria", "doe")
        model_type (str): Tipo do modelo (ex: "Full", "Base")
        
    Returns:
        Optional[BaseModel]: Modelo Pydantic ou None se não encontrado
    """
    module_name = f"..schemas.docs.{doc_type.lower()}"
    try:
        module = importlib.import_module(module_name, __package__)
        model = getattr(module, f"{doc_type.capitalize()}{model_type}", None)
        return model
    except ModuleNotFoundError:
        return None

def validate_structured_text_with_model(model, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Valida dados estruturados usando um modelo Pydantic.
    
    Args:
        model: Modelo Pydantic para validação
        data (Dict[str, Any]): Dados a serem validados
        
    Returns:
        Tuple[bool, Optional[str]]: Tupla contendo (status_validacao, mensagem_erro)
    """
    try:
        model.model_validate(data)
        return True, None
    except Exception as e:
        return False, str(e)

def validation_text_structure(file_id, structured_text, doc_type, model_type) -> Dict[str, Any]:
    """
    Valida a estrutura do texto de um documento usando modelo Pydantic apropriado.
    
    Args:
        file_id: ID do arquivo
        structured_text: Texto estruturado para validação
        doc_type: Tipo do documento
        model_type: Tipo do modelo
        
    Returns:
        Dict[str, Any]: Status e mensagem da validação
    """
    try:
        # Obtém o modelo Pydantic apropriado
        model = get_pydantic_model(doc_type, model_type)
        if not model:
            return {"status": "erro", "message": f"Modelo Pydantic para '{doc_type}' não encontrado."}

        # Realiza a validação
        is_valid, error = validate_structured_text_with_model(model, structured_text)
        
        if is_valid:
            logging.info({"status": "completo", "message": "Texto estruturado válido para o modelo."})
            return {"status": "completo", "message": "Texto estruturado válido para o modelo."}
        else:
            logging.error({"status": "incompleto", "message": "Erros de validação encontrados.", "errors": error})
            return {"status": "incompleto", "message": "Erros de validação encontrados.", "errors": error}

    except Exception as e:
        logging.error(f"Erro ao validar o texto estruturado do PDF ID {file_id}: {e}")
        return {"status": "erro", "message": f"Erro ao validar o texto estruturado do PDF ID {file_id}: {str(e)}"}
