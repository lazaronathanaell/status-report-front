import logging
import fitz
from fitz import Document
from io import BytesIO
from typing import Optional

from .image_extract import is_page_scanned, extract_ocr_from_page

def extract_text_from_page(page: fitz.Page) -> str:
    return f'{page.get_text()}\f'

def extract_text(file_bytes: bytes) -> str:
    doc = Document(stream=BytesIO(file_bytes), filetype="pdf")
    text = "".join([f'{page.get_text()}\f' for page in doc])
    doc.close()
    return text
    
def check_hybrid_pdf_and_extract(file_bytes: bytes, num_pages: Optional[int] = None, image_doc: bool = False) -> tuple[str, list[dict]]:
    
    file_stream = BytesIO(file_bytes)
    page_statuses = []
    all_extracted_text = []
    
    try:
        doc = fitz.open(stream=file_stream, filetype="pdf")
    except Exception as e:
        return ("", [{"error": f"Erro ao abrir o documento: {e}"}])
    
     # Determina quantas páginas processar
    total_pages = len(doc)
    pages_to_process = min(num_pages, total_pages) if num_pages is not None else total_pages

    for page_num in range(pages_to_process):
        page = doc[page_num]
        page_index = page_num + 1

        try:
            if image_doc:
                is_scanned = True
            else:
                is_scanned = is_page_scanned(page)
            
            
            if is_scanned:
                
                extracted_page_text_image = extract_ocr_from_page(file_bytes, page_num)
                extracted_page_text =  extract_text_from_page(page).strip()

                extracted_page_text_raw = f"{extracted_page_text}\n{extracted_page_text_image}"

                page_type = "Imagem"
            else:
                extracted_page_text_raw = extract_text_from_page(page).strip()
                page_type = "Texto Selecionável"

            
            all_extracted_text.append(f"{extracted_page_text_raw}\f")
            
            status = {
                "page_num": page_index,
                "type": page_type,
            }
            page_statuses.append(status)

        except Exception as e:
            logging.error(f"Erro inesperado ao processar a página {page_index}: {e}")
            all_extracted_text.append(f"ERRO_PAGINA_{page_index}\f")
            page_statuses.append({"page_num": page_index, "error": f"Erro de extração: {e}"})
            
    doc.close()
    
    final_text = "".join(all_extracted_text).rstrip('\f')
    
    return (final_text, page_statuses)