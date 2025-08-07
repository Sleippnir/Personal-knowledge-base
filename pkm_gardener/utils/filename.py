import re
import os

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a string to be a valid filename.
    """
    # Replace spaces with hyphens
    filename = filename.replace(" ", "-")
    # Remove characters that are not alphanumeric, hyphens, underscores, or periods
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename)
    # Replace multiple hyphens with a single hyphen
    filename = re.sub(r'-+', '-', filename)
    # Trim leading/trailing hyphens or periods
    filename = filename.strip('.- ')
    return filename

def resolve_filename_conflict(filepath: str) -> str:
    """
    Resolves filename conflicts by appending a number (e.g., file.md -> file-1.md).
    """
    if not os.path.exists(filepath):
        return filepath

    directory, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    i = 1
    while True:
        new_name = f"{name}-{i}{ext}"
        new_filepath = os.path.join(directory, new_name)
        if not os.path.exists(new_filepath):
            return new_filepath
        i += 1
