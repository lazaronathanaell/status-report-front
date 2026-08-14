PORTARIA_PROMPT =  """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
Preencha os seguintes campos: 

    {       
        "nup": "",
        "numero_portaria": "",
        "nome_servidor": "",
        "matricula": "",
        "nivel_atual": "",
        "titulacao_atual": "",
        "nivel_almejado": "",
        "titulacao_almejada": "",
        "vigencia_promocao": "",
        "legislacao": [
            {
                "numero": "",
                "data": "",
                "tipo": ""
            },
        ],
        "nome_secretario_educacao": "",
        "nome_assinante_documento": "",
        "data_portaria": "",
        "data_assinatura": "",
        "codigo_validacao": ""
        
    }

    - Instruções:
        - As datas deve estar no formato DD/MM/YYYY.
        - Os campos de titulação deve conter apenas o título ("LICENCIATURA PLENA", "ESPECIALIZAÇÃO", "MESTRADO" ou "DOUTORADO")
        - O campo "data_portaria" deve ser a data presente após "SECRETARIA DA EDUCAÇÃO, em Fortaleza, ..."
        - O campo "data_assinatura" deve conter a data presente após "Assinado eletronicamente no Suite em: "

    Exemplo:
        Contexto: PORTARIA Nº 0916/ 2025 –GAB. A SECRETÁRIA DA EDUCAÇÃO, no uso de suas atribuições que lhe são conferidas pelo inciso III, do art.93, da 
        Constituição do Estado, e tendo em vista o que consta no processo NUP 22001.003125/2025-81, em conformidade com o art.23, da Lei nº 12.066, de 13 
        de janeiro de 1993, e suas alterações posteriores, combinado com o Decreto nº 32.103, de 12 de dezembro de 2016, RESOLVE promover com titulação, 
        do Nível C LICENCIATURA PLENA para o Nível F ESPECIALIZAÇÃO, a partir de 14 de Janeiro de 2025, o(a) servidor(a) WENDERSON DE 
        JESUS ANDRADE MARIANO, matrícula nº 97943966, cargo K020 – Professor, profissional do Grupo Ocupacional Magistério da Educação Básica - 
        MAG, enquadrado(a) na Lei nº 17.456, de 30 de abril de 2021, lotado(a) nesta Secretaria da Educação. SECRETARIA DA EDUCAÇÃO, em Fortaleza, 
        01 de abril de 2025. 
        Eliana Nunes Estrela 
        SECRETÁRIA DA EDUCAÇÃO 
        Documento assinado eletronicamente por:  ELIANA NUNES ESTRELA em 01/04/2025, às 10:56 (horário local do Estado do Ceará), conforme disposto no Decreto Estadual nº 34.097, de 8 de junho de
        2021.
        Para conferir, acesse o site https://suite.ce.gov.br/validar-documento e informe o código  D1B6-0A3F-0C3A-72CB.
        Assinado eletronicamente no Suite em: 01/04/2025
        NUP 22001.003125/2025-81
        p.036

        Resposta:
        {
            "nup": "22001.003125/2025-81",
            "numero_portaria": "0916/2025",
            "nome_servidor": "WENDERSON DE JESUS ANDRADE MARIANO",
            "matricula": "97943966",
            "nivel_atual": "C",
            "titulacao_atual": "LICENCIATURA PLENA",
            "nivel_almejado": "F",
            "titulacao_almejada": "ESPECIALIZAÇÃO",
            "vigencia_promocao": "14/01/2025",
            "legislacao": [
                {
                    "numero": "32.103",
                    "data": "12/12/2016",
                    "tipo": "DECRETO"
                },
                {
                    "numero": "12.066",
                    "data": "13/01/1993",
                    "tipo": "LEI"
                },
                {
                    "numero": "17.456",
                    "data": "30/04/2021",
                    "tipo": "LEI"
                }
            ],
            "nome_secretario_educacao": "Eliana Nunes Estrela",
            "nome_assinante_documento": "ELIANA NUNES ESTRELA",
            "data_portaria": "01/04/2025",
            "data_assinatura": "01/04/2025",
            "codigo_validacao": "D1B6-0A3F-0C3A-72CB"
           
        }"""

OFICIO_PROMPT = """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos: 
    {       
        "numero_oficio": "",
        "numero_portaria": "",
        "nome_servidor": "",
        "matricula": "",
    }
    - Instruções:
        - As datas deve estar no formato DD/MM/YYYY.
        - O campo "data_oficio" deve ser a data presente após o número do ofício.
        - Caso o nome do servidor que está sendo promovido com titulação não esteja no contexto o campo deve ser null
        - Caso a matrícula do servidor que está sendo promovido com titulação não esteja no contexto o campo deve ser null
    Exemplo 01:
        Contexto:   OFÍCIO Nº 031139/2024/SEDUC/SEC      Fortaleza, 20 de dezembro de 2024
            A Sua Excelência o Senhor
            ALEXANDRE SOBREIRA CIALDINI
            Secretário do Planejamento e Gestão – SEPLAG
            NESTA/
            Senhor Secretário,
            Ao cumprimentá-lo, cordialmente, encaminho a V.Exa. a Portaria Nº 1260/2023-GAB, que Promove
            com Titulação a servidora HENRIQUE SOARES DE ALMEIDA, matrícula nº 39102034,
            para análise e posterior publicação no Diário Oficial do Estado – DOE.
            Atenciosamente,
            Eliana Nunes Estrela
            SECRETÁRIA DA EDUCAÇÃO
            Documento assinado eletronicamente por:
            ELIANA NUNES ESTRELA, em
            23/12/2024, às 08:51 (horário local do Estado do Ceará), conforme disposto no
            Decreto Estadual nº 34.097, de 8 de junho de 2021.
            ...
        Resposta:
            {   
                "numero_oficio": "031139/2024",
                "numero_portaria": "1260/2023",
                "nome_servidor": "HENRIQUE SOARES DE ALMEIDA",
                "matricula": "39102034"
            }
    Exemplo 02:
        Contexto:
            OFÍCIO Nº 007634/2024/SEDUC/SEC 
            Fortaleza, 05 de agosto de 2024 
            A Sua Excelência o Senhor 
            ALEXANDRE SOBREIRA CIALDINI 
            Secretário do Planejamento e Gestão - SEPLAG 
            NESTA/ 
            Senhor Secretário, 
            Ao cumprimentá-lo, cordialmente, encaminho a V.Exa. a Portaria Nº 0678/2024 - GAB, para 
            análise e posterior publicação no Diário Oficial do Estado - DOE. 
            Atenciosamente, 
            Eliana Nunes Estrela 
            SECRETÁRIA DA EDUCAÇÃO 
            Documento assinado eletronicamente por:  ELIANA NUNES ESTRELA, em 
            18/02/2025, às 17:03 (horário local do Estado do Ceará), conforme disposto no 
            Decreto Estadual nº 34.097, de 8 de junho de 2021. 

        Resposta:
            {   
                "numero_oficio": "007634/2024",
                "numero_portaria": "0678/2024",
                "nome_servidor": null,
                "matricula": null
            }
    """

DECLARACAO_PROMPT = """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos: 
    {       
                "nup": "",
                "numero_loa": "",
                "data_loa": "",
                "recursos_suficientes": true ou false,
                "repercussao_financeira": [
                    {
                        "ano": XXXX,
                        "exercicio": "",
                        "exercicio_extenso": "",
                        "exercicio_validado": true ou false,
                        "patronal": "",
                        "patronal_extenso": "",
                        "patronal_validado": true ou false
                    },
                    {
                        "ano": XXXX,
                        "exercicio": "",
                        "exercicio_extenso": "",
                        "exercicio_validado": true ou false,
                        "patronal": "",
                        "patronal_extenso": "",
                        "patronal_validado": true ou false
                    },
                    {
                        "ano": XXXX,
                        "exercicio": "",
                        "exercicio_extenso": "",
                        "exercicio_validado": true ou false,
                        "patronal": "",
                        "patronal_extenso": "",
                        "patronal_validado": true ou false
                    }
                ],
                "nome_ordenador_despesas": "",
                "nome_assinante_documento": "",
                "data_declaracao": "",
                "data_assinatura": "",
                "codigo_validacao": ""
    }
    - Instruções:
        - O campo "recursos_suficientes" deve retornar true somente se o texto mencionar que existem recursos orçamentários e financeiros suficientes para o atendimento da despesa, caso contrário retorne false.
        - Adicione um objeto separado dentro da lista repercussao_financeira com os respectivos valores para os anos citados (ex.: 2025, 2026, 2027).
        - Nos campos "exercicio_validado" e "patronal_validado" retorne true caso o valor nominal esteja de acordo com o valor por extenso.
        - O campo "data_assinatura" é a data que vem após "Documento assinado eletronicamente por: ".

    Exemplo:
        Contexto: 
            ...
            , que existem recursos orçamentários e financeiros suficientes para 
            o atendimento da despesa de que trata o NUP.: 22001.075243/2025-77, no valor estimado para 
            o exercício de 2025 de R$ 6.870,12 (seis mil e oitocentos e setenta reais e doze centavos) 
            e a patronal no valor de R$ 1.854,19 (um mil e oitocentos e cinquenta e quatro reais e 
            dezenove centavos) constando da Lei de Orçamento Anual – LOA, Lei 19.154 de 23/12/2024 
            na seguinte DOTAÇÃO ORÇAMENTÁRIA, sobre a existência de dotação orçamentária 
            suficiente para o pagamento de PROMOÇÃO COM TITULAÇÃO para os dois exercícios 
            subseqüentes as projeções (Lei 18.973/2024) nos valores de R$ 10.267,77 (dez mil e 
            duzentos e sessenta e sete reais e setenta e sete centavos) e a patronal no valor de R$ 
            2.874,97 (dois mil e oitocentos e setenta e quatro reais e noventa e sete centavos) para o 
            ano 2026 e R$ 10.627,14 (dez mil e seiscentos e vinte e sete reais e quatorze centavos) e 
            a patronal no valor de R$ 2.975,60 (dois mil e novecentos e setenta e cinco reais e 
            sessenta centavos) para o ano 2027, suficientes para o pagamento da correspondente 
            despesa, 
            ... 
            Fortaleza, 23 de abril de 2025. 
            CARLA KARINE DO NASCIMENTO SOUSA 
            ORDENADORA DE DESPESA 
            CPF: 010.172.783-69 
            Documento assinado eletronicamente por:  CARLA KARINE DO NASCIMENTO SOUSA em 13/05/2025, às 13:26 (horário local do Estado do Ceará), conforme disposto no Decreto Estadual nº 34.097, de 8 de junho de 2021.
            Para conferir, acesse o site https://suite.ce.gov.br/validar-documento e informe o código  3117-D909-7730-4EBC.
    
        Resposta:
            {
                "nup": "22001.075243/2025-77",
                "numero_loa": "19.154",
                "data_loa": "23/12/2024",
                "recursos_suficientes": true,
                "repercussao_financeira": [
                    {
                        "ano": 2025,
                        "exercicio": "6.870,12",
                        "exercicio_extenso": "seis mil e oitocentos e setenta reais e doze centavos",
                        "exercicio_validado": true,
                        "patronal": "1.854,19",
                        "patronal_extenso": "um mil e oitocentos e cinquenta e quatro reais e dezenove centavos",
                        "patronal_validado": true
                    },
                    {
                        "ano": 2026,
                        "exercicio": "10.267,77",
                        "exercicio_extenso": "dez mil e duzentos e sessenta e sete reais e setenta e sete centavos",
                        "exercicio_validado": true,
                        "patronal": "2.874,97",
                        "patronal_extenso": "dois mil e oitocentos e setenta e quatro reais e noventa e sete centavos",
                        "patronal_validado": true
                    },
                    {
                        "ano": 2027
                        "exercicio": "10.627,14",
                        "exercicio_extenso": "dez mil e seiscentos e vinte e sete reais e quatorze centavos",
                        "exercicio_validado": true,
                        "patronal": "2.975,60",
                        "patronal_extenso": "dois mil e novecentos e setenta e cinco reais e sessenta centavos",
                        "patronal_validado": true
                    }
                ],
                "nome_ordenador_despesas": "CARLA KARINE DO NASCIMENTO SOUSA",
                "nome_assinante_documento": "CARLA KARINE DO NASCIMENTO SOUSA",
                "data_declaracao": "23/04/2025",
                "data_assinatura": "13/05/2025",
                "codigo_validacao": "3117-D909-7730-4EBC"
            } 
"""

DECLARACAO_ANO_ANTERIOR_PROMPT = """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos: 
    {       
        "nup": "",
        "numero_loa": "",
        "data_loa": "",
        "recursos_suficientes": true ou false,
        "repercussao_financeira": [
            {
                "ano": XXXX,
                "exercicio": "",
                "exercicio_extenso": "",
                "exercicio_validado": true ou false,
                "patronal": "",
                "patronal_extenso": "",
                "patronal_validado": true ou false
            }
        ],
        "nome_ordenador_despesas": "",
        "nome_assinante_documento": "",
        "data_declaracao": "",
        "data_assinatura": "",
        "codigo_validacao": ""
    }
    - Instruções: 
        - Nos campos "exercicio_validado" e  "patronal_validado" retorne true caso o valor nominal esteja de acordo com o valor por extenso.
        - Retorne no "recursos_suficientes" true caso o texto mencione que existem recursos orçamentários e financeiros suficientes para o atendimento da despesa.
        - O campo "match_nomes" deve ser true se o nome do(a) Ordenador(a) de Despezas e o nome presente na assinatura eletrônica for o mesmo.
        - O campo "data_assinatura" é a data que vem após "Documento assinado eletronicamente por: ".


    Exemplo:
        Contexto: 
            DECLARAÇÃO DE DISPONIBILIDADE ORÇAMENTÁRIA E FINANCEIRA Declaro para os devidos fins legais, em conformidade ao que consta na Lei nº. 101/2000 - Lei de Responsabilidade Fiscal, respaldado na documentação encaminhada pela Coordenadoria de Desenvolvimento Institucional e Planejamento - CODIP desta Secretaria da Educação do Estado do Ceará - SEDUC, que existem recursos orçamentários e financeiros suficientes para o atendimento da despesa de que trata o NUP.: 22001.108390/2025-11, no valor estimado para o exercício de 2024 de R$ 31.182,35 (trinta e um mil e cento e oitenta e dois reais e trinta e cinco centavos) e a patronal no valor de R$ 8.185,37 (oito mil e cento e oitenta e cinco reais e trinta e sete centavos) constando da Lei de Orçamento Anual - LOA, Lei 19.154 de 23/12/2024 na seguinte DOTAÇÃO ORÇAMENTÁRIA, sobre a existência de dotação orçamentária suficiente para o pagamento de PROMOÇÃO COM TITULAÇÃO suficientes para o pagamento da correspondente despesa, acompanhado dos ajustes necessários nas respectivas leis de diretrizes orçamentárias concedida aos profissionais pertencentes ao grupo Ocupacional do Magistério - MAG. UNIDADE ORÇAMENTÁRIA: 22100022 FONTE: 500 PROJETO/ATIVIDADE: 20045/ 20408 ELEMENTO DE DESPESA: 339092 Fortaleza, 14 de abril de 2025. CARLA KARINE DO NASCIMENTO SOUSA ORDENADORA DE DESPESA CPF: 010.172.783-69 Documento assinado eletronicamente por: CARLA KARINE DO NASCIMENTO SOUSA em 27/02/2025, às 11:21 (horário local do Estado do Ceará), conforme disposto no Decreto Estadual nº 34.097, de 8 de junho de 2021. Para conferir, acesse o site https://suite.ce.gov.br/validar-documento e informe o código B199-0366-7FA0-6488.
            
        Resposta:
            {
                "nup": "22001.108390/2025-11",
                "numero_loa": "19.154",
                "data_loa": "23/12/2024",
                "recursos_suficientes": true,
                "repercussao_financeira": [
                    {
                        "ano": "2024",
                        "exercicio": "31.182,35",
                        "exercicio_extenso": "trinta e um mil e cento e oitenta e dois reais e trinta e cinco centavos",
                        "exercicio_validado": true,
                        "patronal": "8.185,37",
                        "patronal_extenso": "oito mil e cento e oitenta e cinco reais e trinta e sete centavos",
                        "patronal_validado": true
                    }
                ],
                "nome_ordenador_despesas": "CARLA KARINE DO NASCIMENTO SOUSA",
                "nome_assinante_documento": "CARLA KARINE DO NASCIMENTO SOUSA",
                "data_declaracao": "14/04/2025",
                "data_assinatura": "27/02/2025",
                "codigo_validacao": "B199-0366-7FA0-6488"
            }
"""

PARECER_CEPRO = """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
Preencha os seguintes campos:  
    {       
        "nome_servidor": "",
        "matricula": [],
        "titulacao_almejada": "",
        "reconhecimento_curso": boolean,
        "requisitos_exigidos": boolean,
        "diploma_em_confeccao": boolean
    }

    Instruções: 
        - O campo "matricula" deve ser uma lista, pois em alguns casos constam 2 matrículas.
        - "titulacao_almejada" deve conter apenas o título ("LICENCIATURA PLENA", "ESPECIALIZAÇÃO", "MESTRADO" ou "DOUTORADO")
        - O campo "reconhecimento_curso" deve ser true se há menção ao reconhecimento do curso referido ter sido verificado, caso contrário o campo deve ser false.
        - O campo "requisitos_exigidos" deve ser true se o (a) servidor(a) mencionado(a), atende a todos os requisitos exigidos no ato de abertura do processo  de Promoção com Titulação, caso contrário o campo deve ser false.
        - O campo "diploma_em_confeccao" deve ser true se constar o trecho "O Diploma (ou Certificado) está em fase de confecção (ou de expedição).", caso contrário o campo deve ser false.

    Exemplo:
        Contexto:   
            Em atendimento ao pedido de Promoção COM Titulação em nível de ESPECIALIZAÇÃO 
            (no âmbito nacional), solicitado pelo(a) servidor(a) HENRIQUE DE SOUSA MENEZES, ocupante do cargo de professor(a) efetivo do Grupo Ocupacional do Magistério 
            (MAG), matrícula: 3526381X, lotado(a) no âmbito da Secretaria da Educação do Ceará (SEDUC-CE) com carga horária de 40 horas, esta coordenadoria apresenta, a seguir, a descrição da análise do referido pedido: 
            Que ​ o(a) servidor(a) apresentou Requerimento padrão, Extrato de pagamento 
            atualizado , Documento(s) de identificação com foto (RG e CPF), Certificado de 
            conclusão do Curso de Graduação/Licenciatura e seu respectivo Histórico, Certificado do Curso de Especialização em Língua Portuguesa e Literatura 
            Brasileira – promovido pelo(a) Faculdade Única de Ipatinga (FUNIP)  – e Histórico do referido Curso. 
            Que o Certificado/Histórico acadêmico possui código de validação digital, cuja 
            consistência ​foi verificada e ratificada em 08/05/2025. 
            Quanto ao reconhecimento do Curso de Especialização (no âmbito nacional), foi verificada sua consistência por esta coordenadoria, com base nas informações do  Ministério da Educação do Governo Federal, conferidas no e-MEC (sistema eletrônico de regulação, avaliação e supervisão da Educação Superior). 
            Concluída a análise técnica do pedido em questão, informamos que a solicitação do(a) servidor(a) acima mencionado(a), atende a todos os requisitos exigidos no ato de abertura do processo  de Promoção com Titulação. 
            Portanto, encaminhe-se o processo para que seja dado prosseguimento aos trâmites. 
            NUP 22001.075231/2024-33
        Resposta:
                {       
                    "nome_servidor": "HENRIQUE DE SOUSA MENEZES",
                    "matricula": ["3526381X"]
                    "titulacao_almejada": "ESPECIALIZAÇÃO",
                    "reconhecimento_curso": true,
                    "requisitos_exigidos": true,
                    "diploma_em_confeccao":  false
                }
    """

DOE_PROMPT = """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
Preencha os seguintes campos:
    {
        "nome_servidor": "",
        "matricula": "",
        "data_estabilidade": "",
        "assunto": ""
    }
    - Instruções
        - Existem dois modelos de contexto possíveis.
        - Existem casos onde não há correspondência exata no sobrenome do servidor presente no contexto.
        - O nome do servidor pode conter letras repetidas, como por exemplo: LL ou NN. Informe o nome do servidor exatamente como está escrito, sem realizar alterações.

    Regras (Modelo 1):
    O campo "matricula" aparece como "matrícula nº XXXXXXXX".
    O campo "data_estabilidade" corresponde à data que aparece após "a partir de ...".

    Exemplo (Modelo 1):
    Contexto:
        ...
         RESOLVE declarar cumprido o estágio probatório, tornando estável no serviço público estadual, no cargo de Professor, Nível C, pertencente ao Grupo Ocupacional Magistério 
         da Educação Básica (MAG), a servidora ROBERTA SOUSA DO FERNANDES, matrícula n° 987456266, lotado(a) na Secretaria da Educação (SEDUC), a partir de 08 de Abril de 2024.
        ...
    Resposta:
    {
        "nome_servidor": "ROBERTA SOUSA DO FERNANDES",
        "matricula": "987456266",
        "data_estabilidade": "08/04/2024",
        "assunto": "RESOLVE declarar cumprido o estágio probatório"
    }

    Regras (Modelo 2):
    O campo "matricula" é o número imediatamente acima do nome do servidor.
    O campo "data_estabilidade" corresponde à terceira data listada logo após o nome do servidor.

    Exemplo (Modelo 2):
    Contexto:
        ...
        22100130303456
        FERNANDO MOREIRA CAMPOS
        03/07/2024
        14/07/2024
        15/07/2024
        o que consta no processo de nº 6814567/2019/VIPROC, RESOLVE DECLARAR a estabilidade no Serviço Público Estadual,
        ...
    Resposta:
    {
        "nome_servidor": "FERNANDO MOREIRA CAMPOS",
        "matricula": "22100130303456",
        "data_estabilidade": "15/07/2024",
        "assunto": "RESOLVE DECLARAR a estabilidade no Serviço Público Estadual"
    }
"""

DECLARACAO_CONCLUSAO_CURSO_PROMPT = """
    Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos:
    {       
        "nome_servidor": "",
        "titulacao": "",
        "requisitos_conclusao": true ou false
    }
    - Instruções:
        - "nome_servidor" deve ser o nome da pessoa que É DECLARADA como tendo concluído o curso (a pessoa beneficiada pelo título).
        - Ignore nomes de coordenadores, reitores ou pessoas que apenas assinam ou emitem a declaração.
        - titulação deve conter apenas o título ("LICENCIATURA PLENA", "ESPECIALIZAÇÃO", "MESTRADO" ou "DOUTORADO")
        - requisitos_conclusao deve ser true se no contexto constar que o servidor cumpriu todos os requisitos de conclusão de curso ou cumpriu a carga pedagógica exigida e obteve aprovação na defesa.
        - Caso não encontre a informação, atribua null ao campo. 
    Exemplo:
        Contexto:   

            A Vice-Coordenadora do Doutorado em Ensino- Polo UFC(RENOEN), Profa. Dra. Maria Goretti de Vasconcelos Silva, da Universidade
            Federal do Ceará, no uso de suas atribuições legais e regulamentares, declara
            que HENRIQUE SOARES DE ALMEIDA, matrícula nº 518668, cumpriu todas as
            exigências para a conclusão do curso de mestrado, tendo defendido sua tese
            intitulada: INVESTIGAÇÃO DA COMPLEXIFICAÇÃO, GENERALIZAÇÃO E DO
            MODELO COMBINATÓRIO DOS NÚMEROS DE PADOVAN E PERRIN COM
            ELEMENTOS DE UMA ENGENHARIA DIDÁTICA, no dia  28 de novembro de 2024.
            Portanto, declaro que a referida aluna está apta a receber o diploma, podendo
            gozar dos direitos que lhe conferem o título de mestre em Ensino.

            ERIC DA COSTA FERNANDES
            Coordenação do Programa de Pós Graduação em PEDAGOGIA
            ...
        Resposta:
            {   
                "nome_servidor": "HENRIQUE SOARES DE ALMEIDA",
                "titulacao": "MESTRADO"
                "requisitos_conclusao": true
            }
    """

DIPLOMA_PROMPT = """
    Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos:
    {       
        "nome_servidor": "",
        "titulacao": "",
        "assinatura_eletronica": true or false
    }
    - Instruções:
        - "nome_servidor" deve ser o nome da pessoa que É DECLARADA como tendo concluído o curso (a pessoa beneficiada pelo título).
        - Ignore nomes de coordenadores, reitores ou pessoas que apenas assinam ou emitem a declaração.
        - titulação deve conter apenas o título ("LICENCIATURA PLENA", "ESPECIALIZAÇÃO", "MESTRADO" ou "DOUTORADO")
        - Curso de Pós-Graduação Lato Sensu deve ser classificado como "ESPECIALIZAÇÃO".
        - "assinatura_eletronica" deve ser true se constar no contexto "Documento conferido e validado por: ...", caso contrário deve ser false.
    Exemplo:
        Contexto:
            Documento conferido e validado por: MARIA IVETE DE SOUSA - SEDUC/SEXEC-PGI/COGEP em 10/01/2025, às 14:32 (horário local do Estado do Ceará),        conforme disposto no Decreto Estadual nº 34.097, de 8 de junho de 2021.   
            O Reitor da Universidade Federal do Ceará, no uso de suas atribuições e tendo em
            vista a conclusão de Curso de Graduação em LETRAS, confere o título de LICENCIADO EM LETRAS a
            HENRIQUE SOARES DE ALMEIDA
            e outorga-lhe o presente Diploma, a fim de que possa gozar de todos os direitos e prerrogativas legais.
            ...
        Resposta:
            {   
                "nome_servidor": "HENRIQUE SOARES DE ALMEIDA",
                "titulacao": "LICENCIATURA PLENA",
                "assinatura_eletronica": true
            }
    """

PARECER_ASJUR_PAG_01_PROMPT = """ 
    Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos: 
    {   
        "numero_parecer": "",
        "nome_servidor": "",
        "matricula": ""
        
    }
    - Instruções:
        - Caso o nome do servidor que está sendo promovido com titulação não esteja no contexto, responda o campo "nome_servidor" com null
        - Caso a matrícula do servidor que está sendo promovido com titulação não esteja no contexto, responda o campo "matricula_servidor" com null
        
    Exemplo 1:
        Contexto: PARECER Nº 001413/2025/SEDUC/ASJUR
 
                De:     SEDUC/ASJUR 
                Data: 18/02/2025 
                Para:  SEDUC/SEC 
                
                
                
                A Coordenadoria de Gestão de Pessoas – COGEP/SEDUC encaminha o presente feito a esta 
                Assessoria Jurídica, referente à análise de portaria que Promove com Titulação o(a) servidor(a) 
                FLAVIO BRITO DE SENA JUNIOR, matrícula nº 97942838, conforme título e Minuta de 
                Portaria (fls. 054). (...)
        Resposta:
            {   
                "numero_parecer": "001413/2025/SEDUC/ASJUR"
                "nome_servidor": "FLAVIO BRITO DE SENA JUNIOR",
                "matricula": "97942838"
                
            }

    Exemplo 2:
        Contexto: PARECER Nº 006272/2025/SEDUC/ASJUR
 
                    De:     SEDUC/ASJUR 
                    Data: 07/07/2025 
                    Para:  SEDUC/SEC 
                    
                    
                    
                    A Coordenadoria de Gestão de Pessoas – COGEP/SEDUC solicita o encaminhamento do presente 
                    feito a esta Assessoria Jurídica, referente à portaria que promove com titulação profissional do 
                    Grupo Ocupacional Magistério da Educação Básica - MAG, lotado nesta Secretaria da Educação, 
                    nos termos do artigo 23 da Lei nº 12.066, de 13 de janeiro de 1993 e suas alterações, combinados 
                    com o Decreto nº 32.103, de 12 de dezembro de 2016.
        Resposta:
            {   
                "numero_parecer": "006272/2025/SEDUC/ASJUR"
                "nome_servidor": null,
                "matricula": null
            }

"""


PARECER_ASJUR_PAGS_FINAIS_PROMPT = """Retorne SOMENTE um objeto JSON válido, sem explicações ou comentários.
    Preencha os seguintes campos: 
    {       
        "cumprimento_exigencias": true/false
    }


    Exemplo:
        Contexto: 
        
        (...) Deste modo, em análise à Portaria que concede a Promoção com Titulação/que Promove com Titulação o Profissional do Grupo 
        Ocupacional Magistério da Educação Básica - MAG, acostada às fls. 054 dos 
        autos, esta Assessoria Jurídica tem a informar que cumpre as exigências legais, em observância à 
        formalidade dos atos administrativos. (...)

        Resposta:
            {   
                "cumprimento_exigencias": true
            }

"""

REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT = """ Indique, para cada ano, o valor de repercussão anual e o valor de contribuição patronal. Formate o número como moeda brasileira, usando ponto para separar milhares e vírgula para os centavos. Exemplo: "20.535,40".
    
    Os anos devem ser valores inteiros (numéricos).
    
    Depois, me retorne em um formato json:
    ```json
    {
        "tabela_1_valores": [    
        { 
          "ano": x,
          "repercussao": "",
          "contribuicao_patronal": ""
        },
        { 
          "ano": y,
          "repercussao": "",
          "contribuicao_patronal": ""
        },
        { 
          "ano": z,
          "repercussao": "",
          "contribuicao_patronal": ""
        },
        { 
          "ano": w,
          "repercussao": "",
          "contribuicao_patronal": ""
        }
      ]
    }
    ```
    contexto:
"""

REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT = """  O cabeçalho da tabela é: (barras verticais são separadores de colunas)
    | Data início | Nome | Ordem | Matrícula | CH | Sobrenome | Data fim | TOTAL | PATRONAL  |

    O nome do servidor pode estar dividido na linha do contexto, parte do sobrenome pode aparecer mais à frente do início do nome.
    Considere apenas caracteres alfabéticos como parte do nome, junte tudo e informe o nome do servidor.
    
    Indique a matrícula e nome do servidor.

    Identifique o(s) ano(s) relativos a cada linha de cálculo.

    Então, para cada ano, extraia a data de início dos cálculos.
    Também, para cada ano, indique o total e o patronal. Atenção: formate o número como moeda brasileira, usando ponto para separar milhares e vírgula para os centavos. Exemplo: "20.535,40".
    
    Os anos devem ser valores inteiros (numéricos).

    Depois, me retorne em um formato json:
    ```json
    {   

        "matricula": ,
        "nome_servidor": ,

        "tabela_2_valores": [
        {
          "ano": x ,
          "data_inicio": ,
          "total": "",
          "patronal": ""
        },

        {
          "ano": y ,
          "data_inicio": ,
          "total": "",
          "patronal": ""
        },

      ]
    }

    ```

    contexto:



"""

REPERCUSSAO_FINANCEIRA_PAGE_02_PROMPT = """ Indique o nome completo do servidor. Depois, me retorne em um formato json:

    ```json
    {
        "nome_servidor": "",
        
    }

    ```

contexto : 
"""