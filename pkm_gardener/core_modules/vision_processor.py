import os
import fitz # PyMuPDF
import io
from PIL import Image
import google.generativeai as genai

from pkm_gardener.types import ProcessingJob
from pkm_gardener.utils.llm import get_llm_suggestions
from pkm_gardener.utils.frontmatter import validate_and_normalize_metadata
from pkm_gardener.config import PKM_ROOT, GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel("gemini-pro-vision")

def get_image_description(image_bytes: bytes) -> str:
    """
    Gets a description of an image using the Gemini Vision API.
    """
    image = Image.open(io.BytesIO(image_bytes))
    response = vision_model.generate_content(["Describe this image for a PKM system.", image])
    return response.text.strip()

def get_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF file.
    """
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def process(job: ProcessingJob, destination_folders_relative: list) -> ProcessingJob:
    """
    Processes an image or PDF file.
    """
    content_for_llm = ""
    try:
        if job.file_type == "image":
            content_for_llm = get_image_description(job.content)
        elif job.file_type == "pdf":
            content_for_llm = get_pdf_text(job.content)
        else:
            job.status = "failure"
            job.error_message = f"Unsupported file type for vision processor: {job.file_type}"
            return job

        (
            parsed_metadata,
            title,
            suggested_filename,
            suggested_folder_relative,
            summary,
        ) = get_llm_suggestions(content_for_llm, destination_folders_relative)

        job.metadata = validate_and_normalize_metadata(parsed_metadata)
        job.metadata['title'] = title

        job.suggested_filename = suggested_filename
        job.suggested_folder_path = os.path.join(PKM_ROOT, suggested_folder_relative)
        job.summary = summary
        job.status = "success"

    except Exception as e:
        job.status = "failure"
        job.error_message = f"Vision processing failed: {e}"
        print(f"Error processing {job.original_filename}: {e}")

    return job
