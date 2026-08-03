# Importação das bibliotecas necessárias
import re
import json
import requests

import logging
from typing import Optional, Dict
import os
from sqlalchemy.orm import Session

from .structure import estrutura_dados
from ..database.session import get_db
from ..models.pdf import PDF
from ..models.user import User

from ..utils.signature import signature_validation


from dotenv import load_dotenv
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL = os.getenv("MODEL")


def run_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt},
        stream=True
    )
    resposta = ''
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode(errors='ignore'))
               
                resposta += data.get('response', '')
            except Exception:
                continue
    return resposta


def answer_question_ollama(question: str, context: str):
    """
    Responde a uma pergunta baseada no contexto fornecido.

    :param question: A pergunta a ser respondida.
    :param context: O contexto onde a resposta será buscada.
    :return: Um dicionário com a resposta e a pontuação de confiança.
    """
    try:
        result = run_ollama(prompt=question + '\n\n' + context)
        return {
            "answer": result,
            
        }
    except Exception as e:
        logging.error(f"Erro ao processar a pergunta: {e}")
        return {"answer": None, "score": 0.0}
    
def load_context(file_id: int):
    db: Session = next(get_db())
    try:
        db_pdf = db.query(PDF).filter(PDF.id == file_id).first()

        if not db_pdf:
            return f"PDF com ID {file_id} não encontrado."

        if not db_pdf.extracted_text:
            return f"PDF com ID {file_id} não possui texto extraído."

        return db_pdf.extracted_text

    except Exception as e:
        logging.error(f"Erro ao carregar o contexto: {e}")
        return None

    finally:
        db.close()

def filter_answer(context: str, prompt:str) -> Dict:
    
    res = answer_question_ollama(prompt, context)

    print(f"Context length (characters): {len(context)}")

    print("\n\nResposta: " + res['answer'])
    
    return res['answer']

def extrair_json_para_dicionario(context: str, prompt:str) -> Dict:
    """
    Extrai um bloco JSON de uma string de resposta do SLM e o retorna como um dicionário Python.

    Args:
        resposta_slm (str): A string de resposta do SLM, contendo o JSON.

    Returns:
        dict or None: Um dicionário Python com os dados do JSON, ou None se nenhum JSON
                      válido for encontrado ou se houver um erro de decodificação.
    """
    
    print("Contexto: " +context)
    print(prompt)

    resposta_slm = filter_answer(context,prompt)
    
    # Expressão regular para encontrar o bloco JSON completo
    match = re.search(r'\{[\s\S]*\}', resposta_slm)

    if match:
        json_string = match.group(0)
        try:
            # Carrega a string JSON para um objeto Python
            dados_json_brutos = json.loads(json_string)

            # Se for uma lista com pelo menos um item, retorna o primeiro dicionário.
            # Caso contrário, retorna os dados brutos (que podem ser um dicionário direto ou outros tipos).
            if isinstance(dados_json_brutos, list) and len(dados_json_brutos) > 0:
                return dados_json_brutos[0]
            else:
                return dados_json_brutos

        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            return None
    else:
        print("Nenhum bloco JSON encontrado na string de resposta do SLM.")
        return None

def process_arquivo(file_id:int, prompt:str, doc_type:str, nome_servidor: Optional[str] = None) -> Optional[str]:

    if not doc_type.startswith(("PARECER_ASJUR")):
        context = load_context(file_id)
        if not context:
            return None
    else:
        context = ''
    
    info = extrair_json_para_dicionario(context,prompt)

    documento_validado = {
        "documento_validado": True,
        "contexto": "",
    }

    assinatura_validada = None

    if doc_type in ["PORTARIA", "DECLARACAO"]:
        assinatura_validada = signature_validation(info["codigo_validacao"])
        
    if(nome_servidor != None):
        info['nome_servidor'] = nome_servidor

    dados = estrutura_dados(info, assinatura_validada, documento_validado, doc_type)


    db: Session = next(get_db())
    try:
        db_pdf = db.query(PDF).filter(PDF.id == file_id).first()

        if not db_pdf:
            return f"PDF com ID {file_id} não encontrado."
        dados_armazenados = db_pdf.structured_text
        
        if dados_armazenados:
            try:
                if isinstance(dados_armazenados, dict) and isinstance(dados, dict):
                    dados.update(dados_armazenados)
            except Exception as e:
                logging.error(f"Erro ao atualizar os dados armazenados: {e}")
                pass
        db_pdf.structured_text = dados
        db.commit()
        return f"Texto Estruturado pelo Gemma e atualizado com sucesso para o PDF ID {file_id}."
    except Exception as e:
        logging.error(f"Erro ao carregar o contexto: {e}")
        return None

    finally:
        db.close()
