import pytesseract

from pdf2image import convert_from_path

from PIL import Image


# Windows Tesseract path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_with_ocr(
    pdf_path: str
):

    extracted_text = ""

    try:

        # Convert PDF pages to images
        images = convert_from_path(
            pdf_path
        )

        # OCR each page
        for index, image in enumerate(images):

            text = pytesseract.image_to_string(
                image,
                config="--oem 3 --psm 6"
            )

            extracted_text += (
                f"\n\n--- PAGE {index + 1} ---\n\n"
            )

            extracted_text += text

    except Exception as e:

        print(
            "OCR extraction failed:",
            e
        )

    return extracted_text