import os
import shutil
from pkm_gardener.types import ProcessingJob
from pkm_gardener.config import DRY_RUN
from pkm_gardener.utils.filename import sanitize_filename, resolve_filename_conflict
from pkm_gardener.utils.frontmatter import construct_frontmatter_string


def file_note(job: ProcessingJob):
    """
    Constructs the final note content and moves the file to its destination.
    """
    if job.status != "success":
        print(f"Skipping file operation for {job.original_filename} due to non-success status.")
        return

    if not job.suggested_folder_path or not job.suggested_filename or not job.metadata:
        job.status = "failure"
        job.error_message = "Missing destination path, filename, or metadata for routing."
        print(f"Error: {job.error_message}")
        return

    # 1. Sanitize the filename suggested by the LLM
    sanitized = sanitize_filename(job.suggested_filename)

    # 2. Ensure the destination directory exists
    if not DRY_RUN:
        os.makedirs(job.suggested_folder_path, exist_ok=True)

    # 3. Resolve any filename conflicts in the destination
    final_filepath = resolve_filename_conflict(
        os.path.join(job.suggested_folder_path, sanitized)
    )
    final_filename = os.path.basename(final_filepath)

    # 4. Construct the final content of the note
    frontmatter_str = construct_frontmatter_string(job.metadata)
    # Ensure content is a string for concatenation
    if isinstance(job.content, bytes):
        content_str = job.content.decode('utf-8')
    elif isinstance(job.content, str):
        content_str = job.content
    elif job.content is None:
        job.status = "failure"
        job.error_message = "Missing content for routing."
        print(f"Error: {job.error_message}")
        return
    else:
        job.status = "failure"
        job.error_message = f"Unsupported content type: {type(job.content)}"
        print(f"Error: {job.error_message}")
        return
    final_content = f"{frontmatter_str}\n{content_str}"

    print(f"Action: Routing '{job.original_filename}' to '{final_filepath}'")

    if not DRY_RUN:
        try:
            # 5. Write the new file to the destination
            with open(final_filepath, "w", encoding="utf-8") as f:
                f.write(final_content)

            # 6. Remove the original file from the inbox
            os.remove(job.original_filepath)
            print(f"✓ Successfully moved and wrote '{final_filename}'")

        except Exception as e:
            job.status = "failure"
            job.error_message = f"File routing failed: {e}"
            print(f"Error during file write/remove: {e}")
    else:
        print("[DRY RUN] No file operations performed.")
