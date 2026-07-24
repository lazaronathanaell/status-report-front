from pdf2image import convert_from_bytes
import pytesseract
from io import BytesIO
import fitz
import logging
from PIL import Image, ImageFilter, ImageOps
from typing import Optional

Image.MAX_IMAGE_PIXELS = 500000000 # Aumenta para 500 milhões de pixels

def is_page_scanned(page: fitz.Page, text_area_threshold: float = 0.05) -> bool:
    """
    Verifica se uma página de PDF é possivelmente escaneada.
    
    Critério:
    Calcula a razão entre a área ocupada por blocos de texto e a área total da página.
    Se essa razão for menor que o threshold informado, considera-se que a página é escaneada.

    Args:
        page (fitz.Page): Página do PDF carregada via PyMuPDF.
        text_area_threshold (float): Proporção mínima aceitável de área coberta por texto 
            para considerar que a página não é escaneada. Default: 0.05 (5%).

    Returns:
        bool: 
            True  -> Página provavelmente escaneada (baixa cobertura de texto).
            False -> Página contém texto extraível.
    """

    # Obtém a área total da página. Usar abs() evita problemas com retângulos invertidos.
    total_page_area = abs(page.rect)
    text_area = 0.0

    # Segurança: se a página tiver área inválida, assume-se como escaneada.
    if total_page_area == 0:
        logging.warning("Página com área zero detectada — marcada como escaneada por segurança.")
        return True 

    # Extrai blocos de texto detectados pelo PyMuPDF.
    blocks = page.get_text("blocks")

    for block in blocks:
        text_content = block[4]

        # Considera apenas blocos que realmente possuem texto (evita contagem de blocos vazios).
        if text_content.strip():
            rect = fitz.Rect(block[:4])  # Coordenadas do bloco de texto
            text_area += abs(rect)       # Soma área ocupada pelo bloco

    # Calcula porcentagem da página coberta por texto.
    text_coverage_ratio = text_area / total_page_area

    logging.debug(
        f"Texto detectado na página: {text_coverage_ratio:.3%} "
        f"(Threshold: {text_area_threshold:.0%})"
    )

    # Retorna True se área de texto está abaixo do threshold.
    return text_coverage_ratio < text_area_threshold


def extract_ocr_from_page(file_bytes: bytes, page_num: int) -> str:
    """
    Extrai texto de uma página de PDF usando OCR (Tesseract).
    
    Converte a página para imagem (600 DPI), aplica pré-processamento básico 
    (escala de cinza) e executa OCR.

    Args:
        file_bytes (bytes): Arquivo PDF em bytes.
        page_num (int): Índice da página (base 0) a ser processada.

    Returns:
        str: Texto extraído pela OCR. Retorna string vazia em caso de erro ou ausência de texto.
    """
    try:
        # Converte uma única página do PDF para imagem.
        images = convert_from_bytes(
            pdf_file=file_bytes, 
            dpi=600,
            first_page=page_num + 1,  # PyMuPDF é 0-based; convert_from_bytes é 1-based
            last_page=page_num + 1,
            fmt='jpeg',
            thread_count=1  # Reduz risco de race conditions; pode ser ajustado para performance
        )
        
        if not images:
            logging.warning(f"Nenhuma imagem gerada para a página {page_num + 1}.")
            return ""

        img = images[0]

        rotate_degrees = detect_rotation_angle(img)

        img = img.rotate(-rotate_degrees, expand=True)
        logging.info(f"Página {page_num + 1} rotacionada em {rotate_degrees}°.")
        
        # Suave para reduzir ruído (blur leve)
        img = img.filter(ImageFilter.MedianFilter(size=5))

        # Pré-processamento mínimo para melhorar OCR: converte para tons de cinza
        img_grayscale = img.convert("L")

        #img_equalized = ImageOps.equalize(img_grayscale)
        
        # Executa OCR usando idioma português
        ocr_text = pytesseract.image_to_string(img_grayscale, lang='por')

        logging.info(f"OCR extraído da página {page_num + 1}: {ocr_text}")

        return ocr_text.strip()

    except Exception as e:
        logging.error(f"Erro ao aplicar OCR na página {page_num + 1}: {e}")
        return ""

def detect_rotation_angle(img: Image.Image) -> int:
    """
    Detecta o ângulo de rotação necessário para a imagem ficar na orientação correta.
    
    Args:
        img (PIL.Image.Image): Imagem para análise de orientação.

    Returns:
        int: Ângulo de rotação (0, 90, 180 ou 270) necessário para corrigir a imagem.
    """
    try:
        # Tesseract OSD funciona melhor em escala de cinza e com DPI decente, mas
        # uma imagem PIL normal também funciona bem para detecção básica.
        
        # OSD pode consumir recursos, usaremos uma versão reduzida da imagem se ela for muito grande.
        # Mas para o OCR de alta qualidade, o DPI 600 já é bom.

        # Retorna um dicionário contendo 'orientation' (o ângulo que a imagem está)
        # e 'rotate' (o ângulo para corrigir).
        osd = pytesseract.image_to_osd(img)
        
        # A informação que queremos é o ângulo que Tesseract sugere aplicar.
        # No OSD, o campo 'rotate' é o valor em graus (0, 90, 180, 270)
        # que a imagem precisa ser girada no sentido anti-horário (contra-relógio) para ficar correta.
        
        # O resultado do OSD é uma string, e precisamos extrair o valor de 'Rotate'
        # Exemplo de saída: "Page number: 0\nOrientation in degrees: 90\nRotate: 270\n..."
        
        rotation_line = next((line for line in osd.split('\n') if line.startswith('Rotate:')), None)
        
        if rotation_line:
            # Extrai o número do valor "Rotate: X"
            angle = int(rotation_line.split(':')[1].strip())
            return angle
        
        return 0 # Padrão: 0 graus, se não detectar nada

    except Exception as e:
        logging.warning(f"Erro na detecção automática de rotação (OSD): {e}. Usando rotação 0.")
        return 0
