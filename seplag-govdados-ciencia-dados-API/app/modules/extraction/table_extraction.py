import fitz  # PyMuPDF
import os
import glob
import logging
from io import BytesIO

# ----------------------------- Extrator com PyMuPDF -----------------------------
def extrair_tabelas_pymupdf(pdf_bytes, paginas):
    """
    Extrai tabelas de um PDF em memória usando PyMuPDF.
    
    Args:
        pdf_bytes (bytes): Conteúdo do PDF.
        paginas (list[int]): Lista de números de páginas para extrair tabelas.
    
    Returns:
        dict: {numero_pagina: [tabela1, tabela2, ...]}
    """
    tabelas_por_pagina = {}
    
    # Abre o PDF diretamente dos bytes
    with fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf") as doc:
        for i in paginas:
            if i < 1 or i > len(doc):
                continue
            pagina = doc[i - 1]  # 0-based
            resultado = []
            for tabela in getattr(pagina, "find_tables", lambda: [])():  # PyMuPDF >=1.22
                resultado.append(tabela.extract())
            tabelas_por_pagina[i] = resultado
    
    return tabelas_por_pagina


def processar_pdf_tabelas_pg_01(
    pdf_bytes: bytes,
    paginas: list[int],
    extrator_fun
) -> str:
    """
    Extrai e processa tabelas da primeira página da repercussão financeira
    diretamente dos bytes do PDF e retorna texto legível para LLM.

    Args:
        pdf_bytes (bytes): Conteúdo do PDF em memória.
        paginas (list[int]): Lista de páginas para extrair tabelas.
        extrator_fun (callable): Função que extrai tabelas do PDF.

    Returns:
        str: Texto das tabelas pronto para o LLM.
    """
    try:
        tabelas_por_pagina = extrator_fun(pdf_bytes, paginas)
    except Exception as e:
        logging.error(f"Erro ao extrair tabelas: {e}")
        return ""

    texto_final = ""
    for i, tabelas in tabelas_por_pagina.items():
        if not tabelas:
            continue
        for tabela in tabelas:
            if not tabela:
                continue
            colunas = max(len(linha) for linha in tabela)
            for linha in tabela:
                linha_pad = [str(c) if c is not None else "" for c in linha]
                linha_pad += [""] * (colunas - len(linha_pad))
                texto_final += " | ".join(linha_pad) + "\n"
            texto_final += "\n"

    return texto_final.strip()

def processar_pdf_tabelas_pg_02(
    pdf_bytes: bytes,
    paginas: list[int],
    extrator_fun
) -> str:
    """
    Extrai tabelas da segunda página da repercussão financeira e retorna como texto pronto para LLM.
    
    Args:
        pdf_bytes (bytes): Conteúdo do PDF.
        paginas (list[int]): Lista de números de páginas para extrair tabelas.
        extrator_fun (callable): Função que extrai tabelas do PDF, deve aceitar (pdf_bytes, paginas) e retornar {página: [tabelas]}.

    Returns:
        str: Texto formatado das tabelas, pronto para LLM.
    """
    try:
        tabelas_por_pagina = extrator_fun(pdf_bytes, paginas)
    except Exception as e:
        logging.error(f"Erro ao extrair tabelas: {e}")
        return ""

    texto_total = ""
    for i in paginas:
        tabelas = tabelas_por_pagina.get(i, [])
        for idx, tabela in enumerate(tabelas):
            if not tabela:
                continue

            colunas = max(len(linha) for linha in tabela)
            linhas_sem_cabecalho = tabela[1:]  # Remove a primeira linha (cabeçalho)

            for linha in linhas_sem_cabecalho:
                linha_pad = [str(c) if c is not None else "" for c in linha]
                linha_pad += [""] * (colunas - len(linha_pad))

                # Mantém só primeira e duas últimas colunas
                colunas_filtradas = ([linha_pad[0]] + linha_pad[-2:]) if len(linha_pad) >= 3 else linha_pad

                # Limpa \n
                for idx_col, valor in enumerate(colunas_filtradas):
                    colunas_filtradas[idx_col] = valor.replace('\n', ' ') if idx_col == 0 else valor.replace('\n', '')

                texto_total += " | ".join(colunas_filtradas) + "\n"

            texto_total += "\n"

    return texto_total.strip()
