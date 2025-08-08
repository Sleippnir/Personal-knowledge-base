import fitz  # PyMuPDF
import yaml
from pkm_gardener.types import ProcessingJob
from pkm_gardener.utils.llm import get_llm_vision_suggestions, get_llm_suggestions
from pkm_gardener.utils.frontmatter import validate_and_normalize_metadata

def process(job: ProcessingJob, destination_folders_relative: list) -> ProcessingJob:
    """
    Processes image or PDF files.
    - For images, it uses a multimodal LLM to generate metadata.
    - For PDFs, it extracts text and uses a text-based LLM to generate metadata.
    """
    try:
        if job.file_type == "image":
            print(f"Processing image file: {job.original_filename}")
            with open(job.original_filepath, 'rb') as f:
                image_bytes = f.read()

            yaml_frontmatter_str, suggested_folder_absolute = get_llm_vision_suggestions(image_bytes, destination_folders_relative)

        elif job.file_type == "pdf":
            print(f"Processing PDF file: {job.original_filename}")
            doc = fitz.open(job.original_filepath)
            pdf_text = ""
            for page in doc:
                pdf_text += page.get_text()
            doc.close()

            if not pdf_text.strip():
                job.status = "failure"
                job.error_message = "PDF contains no extractable text."
                return job

            # Treat the extracted text as a normal text file
            yaml_frontmatter_str, suggested_folder_absolute = get_llm_suggestions(pdf_text, destination_folders_relative)

        else:
            job.status = "failure"
            job.error_message = f"Unsupported file type in vision_processor: {job.file_type}"
            return job

        # Common logic for parsing and updating the job
        parsed_yaml = yaml.safe_load(yaml_frontmatter_str.replace("---\n", "").replace("---", ""))

        job.metadata_str = yaml_frontmatter_str
        job.metadata = validate_and_normalize_metadata(parsed_yaml)
        job.suggested_folder_path = suggested_folder_absolute

        # For vision-processed files, we'll use the original filename for now
        job.suggested_filename = job.original_filename
        job.summary = job.metadata.get('summary', '')

        job.status = "success"

    except Exception as e:
        job.status = "failure"
        job.error_message = f"Vision processing failed: {e}"
        print(f"Error processing {job.original_filename}: {e}")

    return job
