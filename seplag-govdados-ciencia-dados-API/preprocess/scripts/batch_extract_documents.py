"""
Script de extração em batch para documentos no diretório data/separated_docs
Processa todos os documentos sem dependências de Celery ou Banco de Dados
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

# Configurar caminhos - adiciona o diretório raiz do projeto ao sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # Sobe até seplag-govdados-ciencia-dados-API
sys.path.insert(0, str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos de extração (imports absolutos)
from app.modules.extraction.text_extractor import check_hybrid_pdf_and_extract
from app.modules.extraction.document_detector import detectar_tipo_documento
from app.modules.extraction.context_extractor import (
    extrair_contexto_reduzido, 
    extrair_nome_servidor, 
    contexto_reduzido_diploma
)
from app.modules.extraction.table_extraction import (
    extrair_tabelas_pymupdf,
    processar_pdf_tabelas_pg_01,
    processar_pdf_tabelas_pg_02,
)

# Configuração de caminhos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "separated_docs"
OUTPUT_DIR = BASE_DIR / "data" / "extracted_results"

# Criar diretório de saída se não existir
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def read_file_bytes(file_path: str) -> Optional[bytes]:
    """Lê um arquivo e retorna seus bytes"""
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {file_path}: {str(e)}")
        return None


def extract_text_from_document(file_path: str, content_type: str, nome_servidor: str = "") -> Tuple[Optional[str], Optional[str], dict]:
    """
    Extrai texto de um documento
    
    Args:
        file_path: Caminho do arquivo
        content_type: Tipo de conteúdo/nome do documento
        nome_servidor: Nome do servidor
    
    Returns:
        Tupla com (texto_extraído, tipo_documento, status_info)
    """
    try:
        file_bytes = read_file_bytes(file_path)
        if not file_bytes:
            return None, None, {"status": "erro", "motivo": "Falha ao ler arquivo"}

        # Extração especial para diploma
        if content_type.upper() == "DIPLOMA":
            extracted_text, status = check_hybrid_pdf_and_extract(file_bytes, 1, True)
            logger.info(f"Diploma extraído - Status: {status}")
            
            tipo_doc = "DIPLOMA"
            extracted_text = contexto_reduzido_diploma(
                extracted_text, 
                nome_servidor=nome_servidor, 
                linhas_acima=4, 
                linhas_abaixo=8
            )
            return extracted_text, tipo_doc, {"status": "sucesso", "tipo": tipo_doc}

        else:
            # Extração padrão
            extracted_text, status = check_hybrid_pdf_and_extract(file_bytes)
            logger.info(f"Documento extraído - Status: {status}")

            # Detectar tipo de documento
            tipo_doc = detectar_tipo_documento(extracted_text, content_type)

            if(content_type.upper() == "REPERCUSSAO_FINANCEIRA_PG_02" or content_type.upper() == "REPERCUSSAO_FINANCEIRA_PG_01"):
                tipo_doc = "REPERCUSSAO_FINANCEIRA"

            # Tratamento especial: Repercussão financeira
            if tipo_doc == "REPERCUSSAO_FINANCEIRA":
                try:
                    nome_original = str(nome_servidor) if nome_servidor else ""
                    nome_extraido = extrair_nome_servidor(extracted_text, nome_original)

                    if content_type.upper() == "REPERCUSSAO_FINANCEIRA_PG_01":
                        extracted_text = processar_pdf_tabelas_pg_01(file_bytes, [1], extrair_tabelas_pymupdf)
                    elif content_type.upper() == "REPERCUSSAO_FINANCEIRA_PG_02":
                        extracted_text = processar_pdf_tabelas_pg_02(file_bytes, [1], extrair_tabelas_pymupdf)
                    
                    
                    combined = []
                    if extracted_text:
                        combined.append(extracted_text)
                    
                    
                    final_text = "\n\n".join(combined).strip()
                    return final_text, tipo_doc, {"status": "sucesso", "tipo": tipo_doc}
                except Exception as e:
                    logger.error(f"Erro no tratamento REPERCUSSAO_FINANCEIRA: {e}")
                    return extracted_text, tipo_doc, {"status": "erro", "motivo": str(e)}

            # Tratamento especial: Parecer ASJUR
            if tipo_doc == "PARECER_ASJUR":
                try:
                    paginas = extracted_text.split("\f")[:-1] if extracted_text else []
                    pag1 = paginas[0] if paginas else ""
                    pag_finais = paginas[-2:] if len(paginas) > 3 else paginas[1:]

                    # Se houver primeira página e páginas finais, insere marcador (...) no meio
                    if pag1 and pag_finais:
                        final_text = pag1 + "\n\n(... )\n\n" + '\n\n'.join(pag_finais)
                    else:
                        final_parts = []
                        if pag1:
                            final_parts.append(pag1)
                        if pag_finais:
                            final_parts.append('\n\n'.join(pag_finais))

                        final_text = '\n\n'.join(final_parts).strip()
                    return final_text, tipo_doc, {"status": "sucesso", "tipo": tipo_doc}
                except Exception as e:
                    logger.error(f"Erro no tratamento PARECER_ASJUR: {e}")
                    return extracted_text, tipo_doc, {"status": "erro", "motivo": str(e)}

            # Extração especial para DOE
            if tipo_doc == "DOE":
                tipo_documento = status[0].get("type", "") if status else ""
                extracted_text = extrair_contexto_reduzido(
                    extracted_text, 
                    nome_servidor=nome_servidor,
                    tipo_documento=tipo_documento
                )

            return extracted_text, tipo_doc, {"status": "sucesso", "tipo": tipo_doc}

    except Exception as e:
        logger.error(f"Erro ao processar {file_path}: {str(e)}")
        return None, None, {"status": "erro", "motivo": str(e)}


def process_documents(user_id: Optional[str] = None):
    """Processa todos os documentos no diretório data/separated_docs"""
    
    if not DATA_DIR.exists():
        logger.error(f"Diretório não encontrado: {DATA_DIR}")
        return

    logger.info(f"Iniciando processamento em: {DATA_DIR}")

    results_summary = {
        "total_processados": 0,
        "sucesso": 0,
        "erro": 0,
        "documentos": []
    }

    # Iterar por user_id (subpastas principais) - apenas a primeira pasta para teste
    for user_id_folder in list(DATA_DIR.iterdir())[:1]:
        if not user_id_folder.is_dir():
            print(f"[⚠️] Ignorando {user_id_folder}, não é um diretório.")
            continue

        user_id = user_id_folder.name
        logger.info(f"\n=== Processando user_id: {user_id} ===")

        # Iterar pelos arquivos diretamente dentro de cada user_id
        for file_path in user_id_folder.iterdir():
            if not file_path.is_file():
                print(f"[⚠️] Ignorando {file_path}, não é um arquivo.")
                continue

            if file_path.suffix.lower() not in ['.pdf', '.txt']:
                continue

            content_type = file_path.stem
            logger.info(f"  Processando arquivo: {content_type}")

            logger.info(f"    Processando arquivo: {file_path.name}")

            extracted_text, tipo_doc, status_info = extract_text_from_document(
                str(file_path), 
                content_type
            )

            results_summary["total_processados"] += 1

            if extracted_text:
                results_summary["sucesso"] += 1

                # Salvar resultado em arquivo JSON
                result_data = {
                    "user_id": user_id,
                    "content_type": content_type,
                    "arquivo_original": file_path.name,
                    "tipo_documento": tipo_doc,
                    "extracted_text": extracted_text,
                    "status": status_info
                }

                # Criar estrutura de diretórios de saída
                user_output_dir = OUTPUT_DIR / user_id / content_type
                user_output_dir.mkdir(parents=True, exist_ok=True)

                output_file = user_output_dir / f"{file_path.stem}_extracted.json"
                
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"    ✓ Resultado salvo em: {output_file}")
                except Exception as e:
                    logger.error(f"    ✗ Erro ao salvar resultado: {str(e)}")

                results_summary["documentos"].append({
                    "user_id": user_id,
                    "content_type": content_type,
                    "arquivo": file_path.name,
                    "tipo": tipo_doc,
                    "status": "sucesso"
                })
            else:
                results_summary["erro"] += 1
                results_summary["documentos"].append({
                    "user_id": user_id,
                    "content_type": content_type,
                    "arquivo": file_path.name,
                    "status": "erro",
                    "motivo": status_info.get("motivo", "Desconhecido")
                })
                logger.error(f"    ✗ Falha ao processar: {status_info}")

    # Salvar resumo geral
    summary_file = OUTPUT_DIR / "extraction_summary.json"
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results_summary, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✓ Resumo salvo em: {summary_file}")
    except Exception as e:
        logger.error(f"Erro ao salvar resumo: {str(e)}")

    # Imprimir estatísticas finais
    logger.info("\n" + "="*50)
    logger.info("ESTATÍSTICAS FINAIS")
    logger.info("="*50)
    logger.info(f"Total processados: {results_summary['total_processados']}")
    logger.info(f"Sucesso: {results_summary['sucesso']}")
    logger.info(f"Erro: {results_summary['erro']}")
    logger.info(f"Diretório de saída: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_documents()
