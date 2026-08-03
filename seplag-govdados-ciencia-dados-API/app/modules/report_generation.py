import os
import json



## constante nao utilizada
DOCS_NAMES = [ 'PARECER_CEPRO','DOE','REPERCUSSAO_FINANCEIRA','DECLARAÇÃO DE DISPONIBILIDADE ORÇAMENTÁRIA E FINANCEIRA',
             'PARECER_ASJUR','OFICIO'
             ]


## funcao ainda nao utilizada. discutir depois
def checar_docs_ausentes(jsons_concatenados, docs_names = DOCS_NAMES):
    resultado = {}
    for doc in docs_names:
        resultado[doc] = doc in jsons_concatenados
    return resultado


def generate_docs_list(dados):
    linhas = []
    #if dados.get('REQUERIMENTO'):
    linhas.append(f"● Requerimento assinado pelo(a) servidor(a) retro.;")
    if dados.get('PARECER_CEPRO'):
        if(dados['PARECER_CEPRO']['diploma_em_confeccao']==False):
            linhas.append(f"● Diploma no grau de {dados['PARECER_CEPRO']['titulacao_almejada']}")
        else:  ## declaracao ou certidao?
            linhas.append(f"● Certidão que declara a obtenção de todos os requisitos para a concessão do grau de {dados['PARECER_CEPRO']['titulacao_almejada']}")
    if dados.get('PARECER_CEPRO'):
        linhas.append(f"● Parecer da CEPRO/SEDUC favorável à autenticidade da documentação apresentada e, consequentemente, à promoção com titulação do servidor.;")
    if dados.get('DOE'):
        linhas.append(f"● Cópia do Ato que declara o cumprimento do estágio probatório pelo servidor.;")
    if dados.get('PARECER_ASJUR'):
        linhas.append(f"● Parecer Jurídico da ASJUR/SEDUC nº {dados['PARECER_ASJUR']['numero_parecer']}, manifestando-se pela regularidade do rito e da Portaria em questão.;")
    if dados.get('OFICIO'):
        linhas.append(f"● Ofício nº {dados['OFICIO']['numero_oficio']}, solicitando a análise do presente objeto.")
        
    return '\n'.join(linhas)



def fill_template_report_positive(json_final, docs_list, template_path='../../templates/report_template.md'):
    portaria = json_final.get('PORTARIA', {})
    with open(template_path, encoding='utf-8') as f:
        template = f.read()
    filled = template.format(
        data='null',
        nome_do_servidor=portaria.get('nome_servidor', 'null'),
        nup=portaria.get('nup', 'null'),
        matricula=portaria.get('matricula', 'null'),
        titulacao_atual=portaria.get('titulacao_atual', 'null'),
        titulacao_pos_promocao=portaria.get('titulacao_almejada', 'null'),
        data_vigencia=portaria.get('vigencia_promocao', 'null'),
        numero_da_portaria=portaria.get('numero_portaria', 'null'),
        folha_portaria=portaria.get('folha_portaria', 'null'),
        docs_list=docs_list
        
    )
    return filled


def fill_template_report_negative(json_final, validation_analysis, template_path='../../templates/report_template_negative.md'):
    portaria = json_final.get('PORTARIA', {})
    with open(template_path, encoding='utf-8') as f:
        template = f.read()
    filled = template.format(
        data='null',
        nome_do_servidor=portaria.get('nome_servidor', 'null'),
        nup=portaria.get('nup', 'null'),
        matricula=portaria.get('matricula', 'null'),
        titulacao_atual=portaria.get('titulacao_atual', 'null'),
        titulacao_pos_promocao=portaria.get('titulacao_almejada', 'null'),
        data_vigencia=portaria.get('vigencia_promocao', 'null'),
        numero_da_portaria=portaria.get('numero_portaria', 'null'),
        folha_portaria=portaria.get('folha_portaria', 'null'),
        validation_analysis=validation_analysis
        
    )
    return filled













