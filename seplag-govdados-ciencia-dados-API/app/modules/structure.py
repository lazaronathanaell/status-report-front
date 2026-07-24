import re
from datetime import datetime

def to_float(valor):
    """
    Converte uma string numérica para float, aceitando:
      - formato brasileiro: '1.234,56'
      - formato internacional: '1234.56'
    """
    valor = str(valor).strip()

    # Caso contenha vírgula → formato brasileiro
    if ',' in valor:
        valor = valor.replace('.', '').replace(',', '.')
    # Caso contrário, assume formato internacional e só remove separadores desnecessários
    else:
        valor = valor.replace(',', '')

    try:
        return float(valor)
    except ValueError:
        return 0.0  # fallback seguro, evita crash

def to_str(valor):
        return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')



def agregar_por_ano(tabela):
    

    
    resultado = {}

    for item in tabela:
        ano = item["ano"]
        if(item['data_inicio'] == '' or item['data_inicio'] is None):
            continue
        else:
            data = datetime.strptime(item["data_inicio"], "%d/%m/%Y")
        total = to_float(item["total"])
        patronal = to_float(item["patronal"])

        if ano not in resultado:
            resultado[ano] = {
                "ano": ano,
                "data_inicio": item["data_inicio"],
                "total": total,
                "patronal": patronal
            }
        else:
            # soma valores
            resultado[ano]["total"] += total
            resultado[ano]["patronal"] += patronal
            # atualiza data se for mais antiga
            data_existente = datetime.strptime(resultado[ano]["data_inicio"], "%d/%m/%Y")
            if data < data_existente:
                resultado[ano]["data_inicio"] = item["data_inicio"]

    # reconverter para o formato original
    for ano, dados in resultado.items():
        dados["total"] = to_str(dados["total"])
        dados["patronal"] = to_str(dados["patronal"])

    return list(resultado.values())



def estrutura_dados(info, assinatura_validada, documento_validado, tipo_doc):

    if tipo_doc == "PORTARIA":
        dado = { 
            "documento": "PORTARIA",
            "nup": info["nup"],
            "numero_portaria": info["numero_portaria"],
            "nome_servidor": info["nome_servidor"],
            "matricula": info["matricula"],
            "nivel_atual": info["nivel_atual"],
            "titulacao_atual": info["titulacao_atual"],
            "nivel_almejado": info["nivel_almejado"],
            "titulacao_almejada": info["titulacao_almejada"],
            "vigencia_promocao": info["vigencia_promocao"],
            "legislacao": info["legislacao"],
            "nome_secretario_educacao": info["nome_secretario_educacao"],
            "nome_assinante_documento": info["nome_assinante_documento"],
            "data_portaria": info["data_portaria"],
            "data_assinatura": info["data_assinatura"],
            # "codigo_validacao": info["codigo_validacao"],
            # "assinatura_validada": assinatura_validada,
            "documento_validado": documento_validado,             
        }

    elif tipo_doc == "OFICIO":
        dado = {
            "documento": "OFÍCIO",
            "numero_oficio": info["numero_oficio"],
            "numero_portaria": info["numero_portaria"],
            "nome_servidor": info["nome_servidor"],
            "matricula": info["matricula"],
            "documento_validado": documento_validado,
        }

    elif tipo_doc == "DECLARACAO" or tipo_doc == "DECLARACAO_ANO_ANTERIOR_PROMPT":
        dado = {
            "documento": "DECLARAÇÃO DE DISPONIBILIDADE ORÇAMENTÁRIA E FINANCEIRA",
            "nup": info["nup"],
            "numero_loa": info["numero_loa"],
            "data_loa": info["data_loa"],
            "recursos_suficientes": info["recursos_suficientes"],
            "repercussao_financeira": info["repercussao_financeira"],
            "nome_ordenador_despesas": info["nome_ordenador_despesas"],
            "nome_assinante_documento": info["nome_assinante_documento"],
            "data_declaracao": info["data_declaracao"],
            "data_assinatura": info["data_assinatura"],
            # "codigo_validacao": info["codigo_validacao"],
            # "assinatura_validada": assinatura_validada,
            "documento_validado": documento_validado,
        }

    elif tipo_doc == "PARECER_CEPRO":

        # Filtra cada item da lista de matrícula, mantendo apenas letras e números
        matriculas_filtradas = [
            re.sub(r'[^A-Za-z0-9]', '', m) for m in info.get("matricula", [])
        ]
        dado = {
            "documento": "PARECER SEDUC/CEPRO",
            "nome_servidor": info["nome_servidor"],
            "matricula": matriculas_filtradas,
            "titulacao_almejada": info["titulacao_almejada"],
            "reconhecimento_curso": info["reconhecimento_curso"],
            "requisitos_exigidos": info["requisitos_exigidos"],
            "diploma_em_confeccao": info["diploma_em_confeccao"],
            "documento_validado": documento_validado,
        }
    
    elif tipo_doc == "DOE":
        dado = {
        "documento": "DIÁRIO OFICIAL DO ESTADO",
        "nome_servidor": info["nome_servidor"],
        "matricula": info["matricula"],
        "data_estabilidade": info["data_estabilidade"],
        "assunto": info["assunto"],
        "documento_validado": documento_validado,
        }

    elif tipo_doc == "DECLARACAO_CONCLUSAO_CURSO":
        dado = {
            "documento": "DECLARAÇÃO DE CONCLUSÃO DE CURSO",
            "nome_servidor": info["nome_servidor"],
            "titulacao": info["titulacao"],
            "requisitos_conclusao": info["requisitos_conclusao"],
            "documento_validado": documento_validado,
        }

    elif tipo_doc == "DIPLOMA":
        dado = {
            "documento": "DIPLOMA",
            "nome_servidor": info["nome_servidor"],
            "titulacao": info["titulacao"],
            "assinatura_eletronica": info["assinatura_eletronica"],
            "documento_validado": documento_validado,
        }

    elif tipo_doc == "PARECER_ASJUR_01":
        numero_parecer = info.get("numero_parecer", "")
        if numero_parecer.endswith("/SEDUC/ASJUR"):
                # remove o sufixo
                novo_valor = numero_parecer.rsplit("/", 2)[0]
                info["numero_parecer"] = novo_valor
        dado = {
            "documento": "PARECER_ASJUR",
            "numero_parecer": info["numero_parecer"],
            "nome_servidor": info["nome_servidor"],
            "matricula": info["matricula"],
            "documento_validado": documento_validado
        }

    elif tipo_doc == "PARECER_ASJUR_PAGS_FINAIS":
        dado = {
            "cumprimento_exigencias": info["cumprimento_exigencias"]
        }

    elif tipo_doc == "REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT":
        dado = {
            "documento": "REPERCUSSÃO FINANCEIRA",
            "tabela_1_valores": info["tabela_1_valores"],
            "documento_validado": documento_validado
        }

    elif tipo_doc == "REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT":
        
        info["tabela_2_valores"] = agregar_por_ano(info["tabela_2_valores"])
        print(info["nome_servidor"])
        dado = {
            "matricula": info["matricula"],
            "nome_servidor": info["nome_servidor"],
            "tabela_2_valores": info["tabela_2_valores"],
        }
        
    else:
        return None
    
    return dado