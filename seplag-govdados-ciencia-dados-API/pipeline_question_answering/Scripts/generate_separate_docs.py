import os
import json
from PyPDF2 import PdfReader, PdfWriter

# === Caminhos ===
raw_dir = "../data/raw"
output_root = "../../docs/docs_separados/OUTUBRO"
index_path = os.path.join("..", "Scripts", "index.json")

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

# === Processa cada NUP ===

index = index['OUTUBRO']

for nup, doc_map in index.items():
    pdf_path = os.path.join(raw_dir, f"{nup}.pdf")
    if not os.path.exists(pdf_path):
        print(f"[⚠️] PDF não encontrado: {pdf_path}")
        continue

    reader = PdfReader(pdf_path)
    out_dir = os.path.join(output_root, nup)
    os.makedirs(out_dir, exist_ok=True)

    doc_map = agrupar_repercussao(doc_map)

    for doc_name, pages in doc_map.items():
        writer = PdfWriter()

        if (doc_name in ["nome", "matricula", "data" ]):
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

        output_file = os.path.join(out_dir, f"{doc_name}.pdf")
        with open(output_file, "wb") as f_out:
            writer.write(f_out)

        print(f"✅ Gerado: {output_file}")


print("🏁 Finalizado com sucesso!")
