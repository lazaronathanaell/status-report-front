import logging
from datetime import datetime, date
from typing import Dict, Any, Literal, Optional, Union, Type, List
from sqlalchemy.orm import Session
#from ...database.session import get_db
from ...models.pdf import PDF
import unicodedata
from difflib import SequenceMatcher

def _adicionar_contexto(json_document: Dict[str, Any], msg: str) -> None:
    """
    Adiciona mensagem de erro ao contexto do documento e marca como não validado.
    
    Args:
        json_document: Documento JSON para adicionar contexto
        msg: Mensagem de erro a ser adicionada
    """
    json_document["documento_validado"]["documento_validado"] = False
    json_document["documento_validado"]["contexto"] += f"{msg}"


def _normalizar_texto(texto: str) -> str:
    """
    Remove acentos, espaços extras e converte para minúsculas um texto.
    
    Args:
        texto: Texto a ser normalizado
        
    Returns:
        str: Texto normalizado sem acentos e em minúsculas
    """
    
    if not texto:
        return ""
    
    texto_nfd = unicodedata.normalize('NFD', texto)
    
    
    texto_sem_acento = ''.join(
        char for char in texto_nfd 
        if unicodedata.category(char) != 'Mn' 
    )
    
    return texto_sem_acento.strip().lower()


def _validar_campo(json_document: Dict[str, Any], esperado: Optional[str], extraido: Optional[str], campo: str) -> None:
    """
    Valida se um campo esperado corresponde ao campo extraído.
    A comparação ignora acentuação, maiúsculas/minúsculas e espaços extras.
    
    Args:
        json_document: Documento JSON onde adicionar erro se houver
        esperado: Valor esperado do campo
        extraido: Valor extraído do documento
        campo: Nome do campo sendo validado
    """
    esperado_normalizado = _normalizar_texto(esperado) if esperado else ""
    extraido_normalizado = _normalizar_texto(extraido) if extraido else ""
    
    if esperado_normalizado != extraido_normalizado:
        msg = f"{campo} não corresponde. Esperado: {esperado}. Extraído: {extraido}. "
        logging.error(msg)
        _adicionar_contexto(json_document, msg)
    else:
        logging.info(f"Documento passou na validação de {campo}")

def _validar_datas(
    json_document: Dict[str, Any],
    data_1: str,
    data_2: str,
    descricao_data_1: str,
    descricao_data_2: str,
    comparacao: Literal["igual", "ordem"] = "igual",
    formato: str = "%d/%m/%Y"
) -> None:
    """
    Compara duas datas e valida se são iguais ou se estão em ordem cronológica.
    
    Args:
        json_document: Documento para registro de erros
        data_1: Primeira data para comparação
        data_2: Segunda data para comparação
        descricao_data_1: Descrição da primeira data
        descricao_data_2: Descrição da segunda data
        comparacao: Tipo de comparação ("igual" ou "ordem")
        formato: Formato das datas
    """

    try:

        if isinstance(data_2, date):
            data_2 = data_2.strftime('%d/%m/%Y')

        if comparacao == "igual" and data_1 != data_2:
            msg = f"{descricao_data_1} e {descricao_data_2} não correspondem: {data_1} ≠ {data_2}. "
            logging.error(msg)
            _adicionar_contexto(json_document, msg)
        elif comparacao == "ordem" and datetime.strptime(data_1, formato) < datetime.strptime(data_2, formato):
            msg = f"{descricao_data_1} é inferior a {descricao_data_2}: {data_1} < {data_2}. "
            logging.error(msg)
            _adicionar_contexto(json_document, msg)
        else:
            logging.info(f"Documento passou na validação de {descricao_data_1} e {descricao_data_2}")
    except Exception as e:
        _adicionar_contexto(json_document, f"Erro ao validar datas ({descricao_data_1} e {descricao_data_2})")


def _validar_nomes(
    json_document: Dict[str, Any],
    nome_cargo: Optional[str],
    nome_assinante: Optional[str],
    cargo: Literal["Secretário(a) de Educação", "Ordenador(a) de Despesas"]
) -> None:
    """
    Valida se o nome do ocupante do cargo corresponde ao nome do assinante.
    
    Args:
        json_document: Documento para registro de erros
        nome_cargo: Nome do ocupante do cargo
        nome_assinante: Nome do assinante do documento
        cargo: Tipo do cargo sendo validado
    """

    nome_cargo_norm = _normalizar_texto(nome_cargo) if nome_cargo else ""
    nome_assinante_norm = _normalizar_texto(nome_assinante) if nome_assinante else ""

    if nome_cargo_norm != nome_assinante_norm:
        msg = f"Nome do {cargo} não corresponde ao Assinante. Cargo: {nome_cargo}, Assinante: {nome_assinante}. "
        logging.error(msg)
        _adicionar_contexto(json_document, msg)
    else:
        logging.info(f"Documento passou na validação de {cargo}")

def _validar_assinatura(
    json_document: Dict[str, Any],
    assinatura_validada: Dict[str, Any],
    campo: str
) -> None:
    """
    Valida se uma assinatura eletrônica é válida.
    
    Args:
        json_document: Documento para registro de erros
        assinatura_validada: Dados da assinatura para validação
        campo: Descrição do campo de assinatura
    """

    if not assinatura_validada.get("signature_valid"):
        mensagem = (
            f"Falha na verificação de {campo}."
            f"Status: {assinatura_validada.get('status', '')}, "
            f"Tipo: {assinatura_validada.get('document_type', '')}, "
            f"Assinado por: {assinatura_validada.get('user_name', '')}. "
        )
        logging.error(mensagem)
        _adicionar_contexto(json_document, mensagem)
    else:
        logging.info(f"Documento passou na validação de {campo}")


def _validar_lista_matriculas(
    json_document: Dict[str, Any],
    esperado: Optional[list[str]],
    extraidos: Union[str, list[str], None],
    comparacao: Literal["total", "parcial"] = "total"
) -> None:
    """
    Valida matrículas extraídas contra uma lista de matrículas esperadas.
    
    Args:
        json_document: Documento para registro de erros
        esperado: Lista de matrículas esperadas
        extraidos: Matrícula(s) extraída(s) do documento
        comparacao: Tipo de comparação ("total" ou "parcial")
    """

    if isinstance(extraidos, str) and comparacao == "parcial":
        if any(str(item).lower() in str(extraidos).lower() for item in esperado):
            logging.info(f"Documento passou na validação de Matrícula")
        else:
            mensagem = (
                f"Matrícula não corresponde."
                f"Esperado: {esperado}. Extraído: {extraidos}. "
            )
            logging.error(mensagem)
            _adicionar_contexto(json_document, mensagem)
        return
    
    elif isinstance(extraidos, str) and comparacao == "total":
        if any(str(extraidos).lower() == str(item).lower() for item in esperado):
            logging.info(f"Documento passou na validação de Matrícula")
        else:
            mensagem = (
                f"Matrícula não corresponde."
                f"Esperado: {esperado}. Extraído: {extraidos}. "
            )
            logging.error(mensagem)
            _adicionar_contexto(json_document, mensagem)
        return

    if isinstance(extraidos, list):
        if all(any(str(e).lower() == str(a).lower() for a in esperado) for e in extraidos):
            logging.info(f"Documento passou na validação de Matrícula")
        else:
            mensagem = (
                f"Matrícula não corresponde."
                f"Esperado: {esperado}. Extraído: {extraidos}. "
            )
            logging.error(mensagem)
            _adicionar_contexto(json_document, mensagem)
        return


def _validar_booleano(
    json_document: Dict[str, Any],
    valor_extraido: Any,
    campo: str
) -> None:
    """
    Valida se um campo booleano é verdadeiro.
    
    Args:
        json_document: Documento para registro de erros
        valor_extraido: Valor booleano extraído
        campo: Nome do campo sendo validado
    """

    if valor_extraido is not True:
        msg = f"{campo} deveria ser verdadeiro. Valor extraído: {valor_extraido}. "
        logging.error(msg)
        _adicionar_contexto(json_document, msg)
    else:
       logging.info(f"Documento passou na validação de {campo}")

def _validar_nome_parcial(
    json_document: Dict[str, Any], 
    nome_user: str, 
    nome_extraido: str, 
    campo: str = "Nome do Servidor",
    similaridade_minima: float = 0.80
) -> None:
    """
    Valida o nome do servidor usando correspondência fuzzy para lidar com mudanças
    de sobrenome devido a casamento ou divórcio.
    
    A validação usa o algoritmo de similaridade de sequências (SequenceMatcher) que
    calcula a razão de similaridade entre duas strings, retornando um valor entre 
    0.0 (totalmente diferente) e 1.0 (idêntico).
    
    Args:
        json_document: Documento JSON onde adicionar erro se houver validação falhar
        nome_user: Nome esperado do servidor (do cadastro)
        nome_extraido: Nome extraído do documento
        campo: Nome do campo sendo validado (padrão: "Nome do Servidor")
        similaridade_minima: Limiar mínimo de similaridade (padrão: 0.80 = 80%)
    
    Returns:
        None: Adiciona mensagem de erro ao json_document se a validação falhar
    """
    
    # Normalizar ambos os nomes (remove acentos, lowercase, espaços extras)
    nome_user_norm = _normalizar_texto(nome_user) if nome_user else ""
    nome_extraido_norm = _normalizar_texto(nome_extraido) if nome_extraido else ""
    
    # Validação 1: Correspondência exata
    if nome_user_norm == nome_extraido_norm:
        logging.info(
            f"Documento passou na validação de {campo} "
            )
        return
    
    # Validação 2: Correspondência fuzzy usando SequenceMatcher
    # SequenceMatcher compara as sequências e retorna uma razão de similaridade
    # onde 1.0 = idêntico e 0.0 = totalmente diferente
    similaridade = SequenceMatcher(None, nome_user_norm, nome_extraido_norm).ratio()
    
    if similaridade >= similaridade_minima:
        logging.info(
            f"Documento passou na validação de {campo} "
            f"(similaridade aceitável: {similaridade * 100:.1f}%)."
        )
        return
    
    # Validação falhou: nomes são muito diferentes
    msg = (
        f"{campo} não corresponde. "
        f"Esperado: {nome_user}. "
        f"Extraído: {nome_extraido}. "
    )
    logging.error(msg)
    _adicionar_contexto(json_document, msg)

def normalizar_data(valor: str) -> str:
        """
        Normaliza diferentes formatos de data para o padrão DD/MM/YYYY.
        
        Args:
            valor: String contendo data em formato YYYY-MM-DD ou DD/MM/YYYY
        
        Returns:
            str: Data normalizada no formato DD/MM/YYYY ou string original se falhar
        """
        if not valor:
            return ""
        try:
            if "-" in valor:
                return datetime.strptime(valor, "%Y-%m-%d").strftime("%d/%m/%Y")
            return datetime.strptime(valor, "%d/%m/%Y").strftime("%d/%m/%Y")
        except Exception:
            return valor.strip()
        
def _validar_legislacao(
    json_document: Dict[str, Any],
    esperado: List[Dict[str, str]],
    extraido: List[Dict[str, str]]
) -> None:
    """
    Valida a legislação citada no documento contra uma lista de referência.
    
    Args:
        json_document: Documento para registro de erros
        esperado: Lista de legislações esperadas
        extraido: Lista de legislações extraídas do documento
    """

    if not esperado or not extraido:
        msg = f"Campo 'legislação' ausente ou inválido. Esperado: {esperado}, Extraído: {extraido}. "
        logging.error(msg)
        _adicionar_contexto(json_document, msg)
        return

    for item_esp in esperado:
        numero_esp = str(item_esp.get("numero", "")).strip()
        data_esp = normalizar_data(item_esp.get("data", ""))
        tipo_esp = str(item_esp.get("tipo", "")).strip().upper()

        correspondente = next(
            (
                item for item in extraido
                if str(item.get("numero", "")).strip() == numero_esp
                and normalizar_data(item.get("data", "")) == data_esp
                and str(item.get("tipo", "")).strip().upper() == tipo_esp
            ),
            None,
        )

        if not correspondente:
            msg = f"Legislação não encontrada ou incorreta: {item_esp}. "
            logging.error(msg)
            _adicionar_contexto(json_document, msg)
        else:
            logging.info(f"Legislação não encontrada ou incorreta: {item_esp}")

    logging.info("Validação de legislação concluída.")


def atualizar_documento(file_id: int, json_atualizado: Dict[str, Any]) -> Optional[str]:
    """
    Atualiza o documento no banco de dados com os dados validados.
    
    Args:
        file_id: ID do arquivo a ser atualizado
        json_atualizado: Dados atualizados do documento
        
    Returns:
        Optional[str]: Mensagem de sucesso ou erro
    """

    db: Session = next(get_db())
    try:
        db_pdf = db.query(PDF).filter(PDF.id == file_id).first()
        if not db_pdf:
            return f"PDF {file_id} não encontrado"
        db_pdf.structured_text = json_atualizado
        db.commit()
        return f"Documento {file_id} atualizado com sucesso"
    except Exception as e:
        logging.error(f"Erro ao atualizar documento {file_id}: {e}")
        db.rollback()
    finally:
        db.close()
