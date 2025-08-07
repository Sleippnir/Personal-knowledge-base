import os
from pkm_gardener.config import INBOX_PATH
from pkm_gardener.orchestrator import ProcessingJob

def find_new_files() -> list[ProcessingJob]:
    """
    Scans the inbox and creates processing jobs for new files.
    """
    jobs = []
    for file_name in os.listdir(INBOX_PATH):
        file_path = os.path.join(INBOX_PATH, file_name)
        if os.path.isfile(file_path):
            # Determine file type (simple for now, can be expanded)
            _, ext = os.path.splitext(file_name)
            file_type = "text" # Default to text
            if ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"]:
                file_type = "image"
            elif ext.lower() == ".pdf":
                file_type = "pdf"

            # Read content (for text files)
            content = ""
            if file_type == "text":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading file {file_name}: {e}")
                    continue # Skip this file if it can't be read

            jobs.append(ProcessingJob(
                original_filepath=file_path,
                original_filename=file_name,
                content=content,
                file_type=file_type
            ))
    return jobs
