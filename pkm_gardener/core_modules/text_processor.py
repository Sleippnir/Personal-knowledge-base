from pkm_gardener.types import ProcessingJob
from pkm_gardener.utils.llm import get_llm_suggestions
from pkm_gardener.utils.frontmatter import validate_and_normalize_metadata
import os


def process(job: ProcessingJob, destination_folders_relative: list) -> ProcessingJob:
    """
    Processes a text-based file by getting suggestions from the LLM.
    """
    try:
        yaml_frontmatter_str, suggested_folder_absolute = get_llm_suggestions(job.content, destination_folders_relative)
        
        # Parse the YAML string back into a dictionary
        import yaml
        parsed_yaml = yaml.safe_load(yaml_frontmatter_str.replace("---\n", "").replace("---", ""))
        
        job.metadata_str = yaml_frontmatter_str
        job.metadata = validate_and_normalize_metadata(parsed_yaml)
        job.suggested_folder_path = suggested_folder_absolute
        
        # Extract suggested filename and summary from metadata if available
        # For now, we'll use the original filename, but this can be enhanced later
        job.suggested_filename = job.original_filename
        job.summary = job.metadata.get('summary', '')
        
        job.status = "success"

    except Exception as e:
        job.status = "failure"
        job.error_message = f"Text processing failed: {e}"
        print(f"Error processing {job.original_filename}: {e}")

    return job
