import os
import shutil

from pkm_gardener.config import INBOX_PATH, RESOURCES_PATH, AREAS_PATH, PROJECTS_PATH, DRY_RUN
from pkm_gardener.core_modules import ingestor, text_processor, vision_processor, indexer, router
from pkm_gardener.types import ProcessingJob

def get_destination_folders():
    """Returns a list of all possible destination folders (relative to PKM_ROOT)."""
    resource_folders = [os.path.join("03_Resources", d) for d in os.listdir(RESOURCES_PATH) if os.path.isdir(os.path.join(RESOURCES_PATH, d))]
    area_folders = [os.path.join("02_Areas", d) for d in os.listdir(AREAS_PATH) if os.path.isdir(os.path.join(AREAS_PATH, d))]
    project_folders = [os.path.join("01_Projects", d) for d in os.listdir(PROJECTS_PATH) if os.path.isdir(os.path.join(PROJECTS_PATH, d))]
    
    # Add the base paths themselves
    resource_folders.append("03_Resources")
    area_folders.append("02_Areas")
    project_folders.append("01_Projects")

    return resource_folders + area_folders + project_folders

def run_pipeline():
    """
    Manages the overall workflow of the application.
    """
    print("Starting PKM Gardener pipeline...")

    destination_folders_relative = get_destination_folders()
    print(f"Available destination folders: {destination_folders_relative}")

    jobs = ingestor.find_new_files()

    if not jobs:
        print("Inbox is empty. Nothing to process.")
        return

    print(f"Found {len(jobs)} files to process.")

    for job in jobs:
        print(f"--- Processing: {job.original_filename} ---")
        try:
            if job.file_type == "text":
                processed_job = text_processor.process(job, destination_folders_relative)
            elif job.file_type == "image" or job.file_type == "pdf":
                processed_job = vision_processor.process(job) # Placeholder for vision processing
            else:
                job.status = "failure"
                job.error_message = f"Unsupported file type: {job.file_type}"
                processed_job = job

            if processed_job.status == "success":
                # Store the YAML string from LLM for router
                processed_job.metadata_str = processed_job.metadata.get('yaml_string_from_llm', '') 
                indexer.update_index(processed_job)
                router.file_note(processed_job)
            else:
                print(f"Job for {processed_job.original_filename} failed: {processed_job.error_message}")
                # If processing failed, move the file back to inbox or a failed folder
                if not DRY_RUN:
                    # Optionally, move to a 'failed' subfolder in inbox or just leave it
                    pass # For now, leave it in inbox if failed

        except Exception as e:
            job.status = "failure"
            job.error_message = f"An unexpected error occurred during processing: {e}"
            print(f"An unexpected error occurred for {job.original_filename}: {e}")
        finally:
            print(f"Finished processing {job.original_filename}. Status: {job.status}")

    print("PKM Gardener pipeline finished.")