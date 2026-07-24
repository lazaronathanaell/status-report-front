import os
import json
import requests
from datetime import datetime

# =========================================
# CONFIGURAÇÕES GERAIS
# =========================================
API_BASE = "http://127.0.0.1:8000"
BASE_PDF_DIR = "../../docs/docs_separados/OUTUBRO"
JSON_FILE = "index.json"
DEFAULT_PASSWORD = "123456"  # senha padrão
# =========================================


def formatar_nup(nup_str):
    
    return f"{nup_str[:5]}.{nup_str[5:11]}/{nup_str[11:15]}-{nup_str[15:]}"


def register_user(nup, info):
    """Tenta registrar o usuário. Se já existir, ignora o erro."""
    url = f"{API_BASE}/users/register"
    email = f"{nup}@example.com"

    data = {
        "email": email,
        "password": DEFAULT_PASSWORD,
        "matric": info.get("matricula"),
        "grade": info.get("titulacao_almejada"),
        "actual_grade": info.get("titulacao_atual"),
        "full_name": info.get("nome"),
    }

    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"🆕 Usuário registrado: {email}")
    elif response.status_code == 400 and "já cadastrado" in response.text:
        print(f"ℹ️ Usuário já cadastrado: {email}")
    else:
        print(f"⚠️ Erro ao registrar {email}: {response.text}")
    return email


def login_user(email):
    """Faz login e retorna o token JWT."""
    url = f"{API_BASE}/users/login"
    data = {"email": email, "password": DEFAULT_PASSWORD}

    response = requests.post(url, json=data)
    if response.status_code != 200:
        raise Exception(f"Erro no login para {email}: {response.text}")

    token = response.json()["access_token"]
    return token



def upload_portaria(token, nup, title, file_path, process_date, content_type):
    """Envia o arquivo para a rota /portaria."""
    url = f"{API_BASE}/pdfs/portaria"
    headers = {"Authorization": f"Bearer {token}"}

    # garantir formato ISO
    if isinstance(process_date, str):
        try:
            process_date = datetime.strptime(process_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            pass

    # processamento do nup
    nup = formatar_nup(nup)

    # parâmetros obrigatórios vão pela query
    params = {
        "title": title.upper(),
        "fileNUP": nup,
        "content_type": content_type,
        "process_date": process_date,
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (
                os.path.basename(file_path),
                f,
                "application/pdf"
            )
        }

        response = requests.post(
            url,
            headers=headers,
            params=params,   # ⬅️ AGORA NA QUERY
            files=files       # ⬅️ SOMENTE O ARQUIVO NO MULTIPART
        )

    if response.ok:
        print(f"📄 {title} enviado com sucesso ({nup})")
    else:
        print(f"⚠️ Falha ao enviar {title} ({nup}): {response.status_code}")
        print(response.text)






def main():
    # Carrega o JSON principal
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)
    dados = dados['OUTUBRO']
    
    for nup, info in dados.items():
        print(f"\n➡️ Processando {nup} - {info.get('nome')}")

        # 1️⃣ Registra o usuário
        email = register_user(nup, info)

        # 2️⃣ Faz login
        token = login_user(email)

        # 3️⃣ Localiza pasta e envia PDFs
        pasta_usuario = os.path.join(BASE_PDF_DIR, nup)
        if not os.path.exists(pasta_usuario):
            print(f"❌ Pasta não encontrada: {pasta_usuario}")
            continue

        process_date = info.get("data", datetime.now().isoformat())

        for arquivo in os.listdir(pasta_usuario):
            if arquivo.lower().endswith(".pdf"):
                nome_arquivo = os.path.splitext(arquivo)[0].upper()
                caminho_arquivo = os.path.join(pasta_usuario, arquivo)
                upload_portaria(token, nup, nome_arquivo, caminho_arquivo, process_date, nome_arquivo)


if __name__ == "__main__":
    main()
