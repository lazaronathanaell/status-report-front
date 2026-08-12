import os
import sys
import json
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

# Configurar caminhos - adiciona o diretório raiz do projeto ao sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent  # Sobe até seplag-govdados-ciencia-dados-API
sys.path.insert(0, str(project_root))

from batch_extract_documents import read_file_bytes, extract_text_from_document, process_documents

# === Caminhos ===
script_dir = os.path.dirname(os.path.abspath(__file__))
preprocess_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(preprocess_dir)
raw_dir = os.path.join(project_root, "data", "raw")
output_root = os.path.join(project_root, "data", "separated_docs")
index_path = os.path.join(preprocess_dir, "index.json")

# === Carrega o índice ===
with open(index_path, "r", encoding="utf-8") as f:
    index = json.load(f)

os.makedirs(output_root, exist_ok=True)

# === Função auxiliar: agrupar páginas de repercussão financeira ===
def agrupar_repercussao(doc_map):
    novas_chaves = {}
    for k, v in doc_map.items():
        if k.startswith("repercussao_financeira_pg"):
            novas_chaves.setdefault("repercussao_financeira", [])
            if isinstance(v, list):
                novas_chaves["repercussao_financeira"].extend(v)
            else:
                novas_chaves["repercussao_financeira"].append(v)
        else:
            novas_chaves[k] = v
    return novas_chaves

# === Processa cada NUP do índice agrupado por mês ===

# medir o tempo total de execução
import time
start_time = time.time()
for month, month_docs in list(index.items()):  # Limita a um mês para teste
    if not isinstance(month_docs, dict):
        continue

    for nup, doc_map in month_docs.items():
        pdf_path = os.path.join(raw_dir, f"{nup}.pdf")
        if not os.path.exists(pdf_path):
            print(f"[⚠️] PDF não encontrado: {pdf_path}")
            continue

        reader = PdfReader(pdf_path)
        out_dir = os.path.join(output_root, nup)
        os.makedirs(out_dir, exist_ok=True)

        for subdir in ["pdfs", "extracted_json", "extracted_md"]:
            os.makedirs(os.path.join(out_dir, subdir), exist_ok=True)

        pdf_dir = os.path.join(out_dir, "pdfs")
        json_dir = os.path.join(out_dir, "extracted_json")
        md_dir = os.path.join(out_dir, "extracted_md")
       

        for doc_name, pages in doc_map.items():
            writer = PdfWriter()

            if (doc_name in ["nome", "matricula", "data" , "titulacao_atual", "titulacao_almejada", "parecer_negativo"]):
                continue

            # Normaliza as páginas para lista contínua
            if isinstance(pages, int):
                pages = [pages]
            elif isinstance(pages, list):
                # Se for uma lista de dois números [início, fim], gera o intervalo completo
                if len(pages) == 2 and all(isinstance(x, int) for x in pages):
                    if(pages[0]<pages[1]):
                        pages = list(range(pages[0], pages[1] + 1))
                    else:
                        pages = [pages]
                # Se for uma lista de várias páginas soltas, deixa como está
            else:
                print(f"[❌] Formato inesperado em {nup} -> {doc_name}: {pages}")
                continue

            for p in pages:
                try:
                    writer.add_page(reader.pages[p - 1])  # índice 0-based
                except IndexError:
                    print(f"[❌] Página {p} não existe em {pdf_path}")
                    continue

            output_file = os.path.join(pdf_dir, f"{doc_name}.pdf")
            with open(output_file, "wb") as f_out:
                writer.write(f_out)

            print(f"✅ Gerado: {output_file}")

            # Processa o documento recém-gerado
            extracted_text, tipo_doc, status_info = extract_text_from_document(
                output_file,
                doc_name,
                nome_servidor=doc_map.get("nome", ""),
            )

            # Salvar o resultado do processamento em um arquivo JSON
            result_data = {
                "nup": nup,
                "content_type": doc_name,
                "arquivo_original": f"{doc_name}.pdf",
                "tipo_documento": tipo_doc,
                "extracted_text": extracted_text,
                "status": status_info,
                "metadata": {
                    "nome_servidor": doc_map.get("nome", ""),
                    "matricula": doc_map.get("matricula", ""),
                    "data": doc_map.get("data", ""),
                    "titulacao_atual": doc_map.get("titulacao_atual", ""),
                    "titulacao_almejada": doc_map.get("titulacao_almejada", ""),
                }
            }

            json_output_file = os.path.join(json_dir, f"{doc_name}.json")
            with open(json_output_file, "w", encoding="utf-8") as f_json:
                json.dump(result_data, f_json, ensure_ascii=False, indent=4)

            for i, text in enumerate(extracted_text):
                md_output_file = os.path.join(md_dir, f"{doc_name}_{i}.md")
                with open(md_output_file, "w", encoding="utf-8") as f_md:
                    if isinstance(text, str):
                        f_md.write(text)



print("🏁 Finalizado com sucesso!")
end_time = time.time()
print(f" Tempo total de execução: {end_time - start_time:.2f} segundos")