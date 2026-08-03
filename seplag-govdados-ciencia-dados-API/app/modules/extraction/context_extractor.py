import re
from ..validation.base_validators import _normalizar_texto
from difflib import SequenceMatcher

def extrair_contexto_reduzido(context, nome_servidor,tipo_documento, linhas_acima=3, linhas_abaixo=2):
    """
    Extrai um trecho reduzido de texto (contexto) em torno do nome de um servidor público.

    Args:
    - context : str       Texto completo (todo o documento).
    - nome_servidor : str Nome do servidor a buscar.
    - linhas_acima : int  Número de linhas acima a incluir quando o padrão não estiver presente.
    - linhas_abaixo : int Número de linhas abaixo a incluir quando o padrão não estiver presente.

    Returns:
    - str : trecho reduzido conforme as regras descritas.
    """

    contexto_reduzido = None

    context_normalized = _normalizar_texto(context)
    nome_servidor = _normalizar_texto(nome_servidor)


    # Divide o texto completo em linhas
    linhas = context.split('\n')
    linhas_servidor = context_normalized.split('\n')


    # Normaliza o nome do servidor
    nome_busca = nome_servidor.upper().strip()
    partes_nome = nome_busca.split()

    # Estratégias progressivas de busca
    estrategias = [
        lambda linha: nome_busca in linha.upper(),
        lambda linha: len(partes_nome) >= 3 and all(parte in linha.upper() for parte in partes_nome[:3]),
        lambda linha: len(partes_nome) >= 2 and all(parte in linha.upper() for parte in partes_nome[:2])
    ]

    linha_encontrada = None
    indice_linha = None

    # Busca pela linha onde o nome do servidor aparece
    for i, linha in enumerate(linhas_servidor):
        for estrategia in estrategias:
            if estrategia(linha):
                linha_encontrada = linha
                indice_linha = i
                break
        if linha_encontrada:
            break

    # Se o nome não for encontrado, retorna vazio
    if linha_encontrada is None:
        return ""
   
    # Padrão da frase que indica estabilidade
    padrao_resolve_declarar = (
        r'RESOLVE\s+DECLARAR\s+a\s+estabilidade\s+no\s+Serviço\s+Público\s+Estadual'
    )

    # Procura a frase apenas nas linhas abaixo do nome encontrado
    linha_padrao = ""
    if indice_linha is not None:
        for l in linhas[indice_linha + 1:]:  # apenas abaixo do nome
            if re.search(padrao_resolve_declarar, l, flags=re.IGNORECASE):
                linha_padrao = l
                break
    if tipo_documento == "Imagem":
        # Se a frase for encontrada abaixo, retorna apenas a linha do nome + linha da frase
        if linha_padrao != "":
            return f"{linha_encontrada.strip()}\n{linha_padrao.strip()}"

    if tipo_documento == "Texto Selecionável":
        # Se a frase for encontrada abaixo, retorna apenas a linha do nome + linha da frase
        inicio = max(0, indice_linha - linhas_acima)
        if linha_padrao != "":
            linhas_abaixo = 3
        fim = min(len(linhas), indice_linha + linhas_abaixo + 1)
        linhas_contexto = linhas[inicio:fim]
        contexto_reduzido = '\n'.join(linhas_contexto)
        return f"{contexto_reduzido.strip()}\n{linha_padrao.strip()}"

    return contexto_reduzido

def extrair_nome_servidor(context, nome_servidor):
    # Normaliza o texto e o nome
    context = context.replace('\n', ' ')

    context = _normalizar_texto(context)
    nome_busca = _normalizar_texto(nome_servidor)

    if nome_busca in context:
        return nome_servidor  # ou o trecho encontrado, se quiser
    else:
        return ""
    
def contexto_reduzido_diploma(context, nome_servidor, linhas_acima=3, linhas_abaixo=2, similaridade_minima=0.6):
    """
    Extrai dois trechos de texto e os concatena:
    1. Trecho em torno do nome do servidor (com linhas acima e abaixo)
    2. Trecho da frase "Documento conferido e validado por" (0 linhas acima, 1 linha abaixo)
    
    Args:
        context (str): Texto completo do documento
        nome_servidor (str): Nome do servidor a buscar
        linhas_acima (int): Número de linhas acima do nome do servidor
        linhas_abaixo (int): Número de linhas abaixo do nome do servidor
        similaridade_minima (float): Similaridade mínima para considerar uma correspondência (0.0 a 1.0)
    
    Returns:
        str: Trechos concatenados ou contexto indicando que todos os campos devem ser nulos.
    """
    
    context = _normalizar_texto(context)
    nome_servidor = _normalizar_texto(nome_servidor)

    # Divide o texto em linhas
    linhas = context.split('\n')
    
    # Normaliza o nome do servidor para busca
    nome_busca = nome_servidor.upper().strip()
    
    linha_servidor = None
    indice_servidor = None
    melhor_similaridade = 0
    
    for i, linha in enumerate(linhas):
        linha_upper = linha.upper().strip()
        
        # Calcula similaridade usando SequenceMatcher
        similaridade = SequenceMatcher(None, nome_busca, linha_upper).ratio()
        
        if similaridade >= similaridade_minima and similaridade > melhor_similaridade:
            melhor_similaridade = similaridade
            linha_servidor = linha
            indice_servidor = i
    
    # Se não encontrou com SequenceMatcher, tenta busca por partes do nome
    if linha_servidor is None:
        partes_nome = nome_busca.split()
        
        for i, linha in enumerate(linhas):
            linha_upper = linha.upper()
            
            # Tenta encontrar todas as partes do nome
            if len(partes_nome) >= 2 and all(parte in linha_upper for parte in partes_nome[:2]):
                linha_servidor = linha
                indice_servidor = i
                break
    
    # Se ainda não encontrou, retorna vazio
    if linha_servidor is None:
        return context
    
    # Extrai o contexto em torno do nome do servidor
    inicio_servidor = max(0, indice_servidor - linhas_acima)
    fim_servidor = min(len(linhas), indice_servidor + linhas_abaixo + 1)
    trecho_servidor = '\n'.join(linhas[inicio_servidor:fim_servidor])
    
    padrao_validacao = r'Documento\s+conferido\s+e\s+validado\s+por'
    
    linha_validacao = None
    indice_validacao = None
    
    for i, linha in enumerate(linhas):
        if re.search(padrao_validacao, linha, flags=re.IGNORECASE):
            linha_validacao = linha
            indice_validacao = i
            break
    
    # Se encontrou a frase de validação, extrai o contexto (0 acima, 1 abaixo)
    trecho_validacao = ""
    if linha_validacao is not None:
        fim_validacao = min(len(linhas), indice_validacao + 3)  # linha atual + 2 abaixo
        trecho_validacao = '\n'.join(linhas[indice_validacao:fim_validacao])
    
    if trecho_validacao:
        resultado = f"{trecho_servidor.strip()}\n\n{trecho_validacao.strip()}"
    else:
        resultado = trecho_servidor.strip()

    if resultado == "" or resultado == None:
       return context
    
    return resultado