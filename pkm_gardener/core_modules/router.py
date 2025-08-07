import os
import shutil
from pkm_gardener.orchestrator import ProcessingJob
from pkm_gardener.config import DRY_RUN
from pkm_gardener.utils.filename import resolve_filename_conflict

def file_note(job: ProcessingJob):
    """
    Prepends frontmatter and moves the file to its final destination.
    """
    if job.status != "success":
        print(f"Skipping file operation for {job.original_filename} due to non-success status.")
        return

    original_full_path = job.original_filepath
    destination_folder = job.suggested_folder_path
    new_filename = job.suggested_filename

    if not destination_folder or not new_filename:
        print(f"Error: Missing destination folder or new filename for {job.original_filename}.")
        job.status = "failure"
        job.error_message = "Missing destination path or filename."
        return

    # Ensure destination directory exists
    if not DRY_RUN:
        os.makedirs(destination_folder, exist_ok=True)

    # Construct the full path for the new file
    new_full_path_potential = os.path.join(destination_folder, new_filename)
    new_full_path = resolve_filename_conflict(new_full_path_potential)

    print(f"Action: Prepending frontmatter to {job.original_filename}")
    print(f"Action: Moving {job.original_filename} to {new_full_path}")

    if not DRY_RUN:
        # 1. Prepend YAML frontmatter to the content
        final_content = job.metadata_str + "\n\n" + job.content.decode('utf-8') if isinstance(job.content, bytes) else job.metadata_str + "\n\n" + job.content

        # Write to a temporary file first to avoid data loss
        temp_file_path = original_full_path + ".tmp"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        # Move the temporary file to the original location (overwriting it)
        shutil.move(temp_file_path, original_full_path)

        # 2. Move the file to the suggested destination
        shutil.move(original_full_path, new_full_path)
        print("File operations completed.")
    else:
        print("DRY_RUN is active. No file operations performed.")

    job.status = "success"
