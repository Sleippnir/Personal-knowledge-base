import os
import pandas as pd
import io

from pkm_gardener.types import ProcessingJob
from pkm_gardener.utils.llm import get_llm_suggestions
from pkm_gardener.utils.frontmatter import validate_and_normalize_metadata
from pkm_gardener.config import PKM_ROOT

def get_csv_summary(csv_bytes: bytes) -> str:
    """
    Generates a summary of a CSV file.
    """
    df = pd.read_csv(io.BytesIO(csv_bytes))
    summary = f"CSV file with {df.shape[0]} rows and {df.shape[1]} columns. "
    summary += f"Columns: {', '.join(df.columns)}. "
    summary += f"First 5 rows:\n{df.head().to_string()}"
    return summary

def process(job: ProcessingJob, destination_folders_relative: list) -> ProcessingJob:
    """
    Processes a document file (e.g., CSV).
    """
    content_for_llm = ""
    try:
        if job.file_type == "csv":
            content_for_llm = get_csv_summary(job.content)
        else:
            # For other document types, just use the raw content if it's not too large
            if len(job.content) < MAX_DOCUMENT_SIZE_FOR_PROCESSING: # Simple size check
                content_for_llm = job.content.decode('utf-8', errors='ignore')
            else:
                content_for_llm = f"Document of type {job.file_type} is too large to process."

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
        job.error_message = f"Document processing failed: {e}"
        print(f"Error processing {job.original_filename}: {e}")

    return job
