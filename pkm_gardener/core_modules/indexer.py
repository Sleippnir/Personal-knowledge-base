from pkm_gardener.orchestrator import ProcessingJob
import os

def update_index(job: ProcessingJob):
    """
    Updates a central index file with information about the processed note.
    For simplicity, this example appends to a markdown file.
    """
    index_file_path = os.path.join(job.suggested_folder_path, "_index.md") # Example index file

    # Ensure the directory exists
    os.makedirs(os.path.dirname(index_file_path), exist_ok=True)

    with open(index_file_path, 'a', encoding='utf-8') as f:
        f.write(f"- [[{job.suggested_filename}]] (Priority: {job.metadata.get('priority', 'N/A')}, Type: {job.metadata.get('type', 'N/A')}) - {job.summary}\n")
