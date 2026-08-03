from .reconhecimento_genero_model import SexPredictor

def predict_gender(nome: str) -> tuple[str, str]:
    """
    Prediz o gênero de um nome.
    
    Args:
        nome (str): Nome da pessoa
        
    Returns:
        tuple: (sexo_previsto, status)
        - sexo_previsto: 'M' (masculino), 'F' (feminino) ou 'UNISSEX'
        - status: 'CERTO', 'VALIDAR' ou 'CORRIGIR'
    """
    predictor = SexPredictor()
    
    primeiro_nome = predictor.first_name(nome)
    predicao = predictor.classify(primeiro_nome)
    
    if predicao == "U":
        return "UNISSEX", "VALIDAR"
    else:
        return predicao, "CERTO"