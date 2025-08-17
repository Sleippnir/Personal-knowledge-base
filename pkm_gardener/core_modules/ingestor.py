import os
import magic
from pkm_gardener.config import INBOX_PATH
from pkm_gardener.types import ProcessingJob

def get_file_type(file_path: str) -> str:
    """
    Determines the file type using python-magic.
    """
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    if mime_type.startswith("image"):
        return "image"
    elif mime_type == "application/pdf":
        return "pdf"
    elif mime_type == "text/csv":
        return "csv"
    elif mime_type.startswith("text"):
        return "text"
    else:
        return "document"

def find_new_files() -> list[ProcessingJob]:
    """
    Scans the inbox and creates processing jobs for new files.
    """
    jobs = []
    if not os.path.exists(INBOX_PATH):
        os.makedirs(INBOX_PATH)

    for file_name in os.listdir(INBOX_PATH):
        if file_name.startswith('.'):
            continue
        file_path = os.path.join(INBOX_PATH, file_name)
        if os.path.isfile(file_path):
            file_type = get_file_type(file_path)

            content = b''
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {file_name}: {e}")
                continue

            jobs.append(ProcessingJob(
                original_filepath=file_path,
                original_filename=file_name,
                content=content,
                file_type=file_type
            ))
    return jobs
