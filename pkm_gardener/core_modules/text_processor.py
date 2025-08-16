from pkm_gardener.types import ProcessingJob
from pkm_gardener.utils.llm import get_llm_suggestions
from pkm_gardener.utils.frontmatter import validate_and_normalize_metadata
from pkm_gardener.config import PKM_ROOT
import os


def process(job: ProcessingJob, destination_folders_relative: list) -> ProcessingJob:
    """
    Processes a text-based file by getting suggestions from the LLM and populating the job object.
    """
    if not isinstance(job.content, str):
        job.status = "failure"
        job.error_message = "Content is not text, cannot process with text_processor."
        return job

    try:
        # 1. Get suggestions from the LLM utility
        (
            parsed_metadata,
            suggested_filename,
            suggested_folder_relative,
            summary,
        ) = get_llm_suggestions(job.content, destination_folders_relative)

        # 2. Validate and normalize the metadata
        job.metadata = validate_and_normalize_metadata(parsed_metadata)

        # 3. Populate the job object with the new data
        job.suggested_filename = suggested_filename
        job.suggested_folder_path = os.path.join(PKM_ROOT, suggested_folder_relative)
        job.summary = summary
        job.status = "success"

    except Exception as e:
        job.status = "failure"
        job.error_message = f"Text processing failed: {e}"
        print(f"Error processing {job.original_filename}: {e}")

    return job
