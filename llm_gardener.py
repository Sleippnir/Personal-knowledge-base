import os
import shutil
import google.generativeai as genai
import yaml
import re

# --- Configuration ---
# NOTE: Using raw strings (r"...") for Windows paths is a good practice
# to avoid issues with backslashes.
PKM_ROOT = r"D:\PKM"
INBOX_PATH = os.path.join(PKM_ROOT, "00_Inbox")
RESOURCES_PATH = os.path.join(PKM_ROOT, "03_Resources")
AREAS_PATH = os.path.join(PKM_ROOT, "02_Areas")

# --- Gemini API Configuration ---
# IMPORTANT: For production, load API_KEY from environment variables for security.
# Example: API_KEY = os.getenv("GEMINI_API_KEY")
from config import GEMINI_API_KEY
API_KEY = GEMINI_API_KEY
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- Functions ---

def get_inbox_files():
    """Returns a list of files in the inbox directory."""
    return [f for f in os.listdir(INBOX_PATH) if os.path.isfile(os.path.join(INBOX_PATH, f))]

def get_destination_folders():
    """Returns a list of all possible destination folders (relative to PKM_ROOT)."""
    resource_folders = [os.path.join("03_Resources", d) for d in os.listdir(RESOURCES_PATH) if os.path.isdir(os.path.join(RESOURCES_PATH, d))]
    area_folders = [os.path.join("02_Areas", d) for d in os.listdir(AREAS_PATH) if os.path.isdir(os.path.join(AREAS_PATH, d))]
    project_folders = [os.path.join("01_Projects", d) for d in os.listdir(os.path.join(PKM_ROOT, "01_Projects")) if os.path.isdir(os.path.join(PKM_ROOT, "01_Projects", d))]
    return resource_folders + area_folders + project_folders

def get_llm_suggestions(file_content, destination_folders_relative):
    """
    Uses the Gemini API to get YAML frontmatter and a suggested destination folder.
    """
    print("\n--- Sending to LLM ---")

    # Construct the detailed prompt based on the guidelines
    prompt = f"""You are an expert librarian. Your task is to analyze the provided content of a note and generate a YAML frontmatter block and suggest a destination folder.

Here are the strict rules for generating the YAML frontmatter:

1.  **status**:
    -   `active-tool`: If the content is primarily a link to or description of a tool, software, or immediately usable online utility (e.g., a link to Excalidraw, a color-picker website).
    -   `learning`: If the content is a tutorial, online course, research paper, or book that requires dedicated time to study and absorb.
    -   `archived`: If the content is a reference, completed meeting notes, or background information that does not require immediate action or study but is valuable for future retrieval.
    -   `triage`: This is the default status for any new item. It will remain if the final categorization is ambiguous.

2.  **priority**:
    -   `P1` (Critical): If the content contains explicit keywords like "urgent," "deadline," "critical," or is directly related to a known, active `P1` project.
    -   `P2` (High): If the content related to core professional responsibilities, important but not urgent tasks, or topics you have explicitly defined as a current focus.
    -   `P3` (Medium): This is the default priority for general knowledge, resources, tutorials, and interesting articles that are for future learning.
    -   `P4` (Low): If assigned to non-essential updates, interesting but tangential links, or items for long-term, "someday/maybe" review.

3.  **type**: Determine by scanning for structural clues:
    -   `repo`: If a `github.com`, `gitlab.com`, etc., link is the primary content.
    -   `paper`: If the document includes an "Abstract," "Introduction," "Conclusion," or citations.
    -   `tutorial`: If the content includes "step-by-step," "how-to," "guide," or is structured as a sequence of instructions.
    -   `cheatsheet` or `SOP`: If the content is a dense list of commands, functions, or procedural steps.
    -   `course`: If it links to a learning platform (e.g., Coursera, Udemy, Hugging Face Courses) or describes a curriculum.
    -   `website`: If it is a link to a general-purpose website or tool.

4.  **tags**: Generate a list of 3-5 tags by extracting key technologies (e.g., `Python`, `Docker`, `Obsidian`), concepts (e.g., `information-architecture`, `machine-learning`), and proper nouns from the text. Normalize them to lowercase and use hyphens for multi-word tags.

5.  **source**: If the file content is derived from a web page, the primary URL **must** be placed in this field. If the note is original thought, this field will be left empty.

Here are the strict rules for suggesting the destination folder:

1.  **01_Projects**:
    -   **Criteria**: The content is directly and explicitly required to achieve a **specific, time-bound goal with a defined outcome**.
    -   **Indicators**: The content mentions a known project name, a specific deadline, or phrases like "project plan," "sprint tasks," "Q3 report requirements."

2.  **02_Areas**:
    -   **Criteria**: The content relates to an **ongoing standard of performance or a long-term responsibility** in your life or work. It does not have a specific end date.
    -   **Indicators**: Keywords like "professional development," "performance review," "weekly planning," "personal finance," "health and fitness."

3.  **03_Resources**:
    -   **Criteria**: This is the **default destination** for any content saved for its topic value. If the information is not tied to a specific project or ongoing area of responsibility, it is a resource.
    -   **Indicators**: Tutorials, papers, articles, and general notes on topics of interest (e.g., notes on a new programming language, an article about history, a collection of design patterns).

If a file cannot be categorized with high confidence according to the rules above, the `status` field in the frontmatter will be set to `triage`, and the tag `#needs-review` will be added to the `tags` list. In this case, the destination folder should be `00_Inbox`.

The content of the note is:
```
{file_content}
```

The list of possible destination folders (relative paths from PKM_ROOT) is:
{destination_folders_relative}

Your output must be ONLY the YAML block, followed by a newline, and then the relative path to the suggested destination folder (e.g., `01_Projects/Project_Q4_Report`). Do NOT include any other text or explanation.
"""
    
    try:
        response = model.generate_content(prompt)
        llm_output = response.text.strip()
        print("--- LLM Raw Response ---")
        print(llm_output)

        # Split the output into YAML and path
        parts = llm_output.split('\n', 1)
        if len(parts) < 2:
            raise ValueError("LLM output format incorrect: missing newline separator.")
        
        yaml_str = parts[0].strip()
        suggested_path_relative = parts[1].strip()

        # Attempt to parse YAML to validate
        parsed_yaml = yaml.safe_load(yaml_str)
        if not isinstance(parsed_yaml, dict):
            raise ValueError("LLM output YAML is not a valid dictionary.")

        # Validate suggested path
        if suggested_path_relative not in destination_folders_relative and suggested_path_relative != "00_Inbox":
            print(f"Warning: LLM suggested an invalid path: {suggested_path_relative}. Defaulting to 00_Inbox.")
            suggested_path_relative = "00_Inbox"
            parsed_yaml['status'] = 'triage'
            if 'tags' in parsed_yaml and isinstance(parsed_yaml['tags'], list):
                if '#needs-review' not in parsed_yaml['tags']:
                    parsed_yaml['tags'].append('#needs-review')
            else:
                parsed_yaml['tags'] = ['#needs-review']
        
        # Reconstruct YAML string in case of modifications
        final_yaml_str = "---\n" + yaml.dump(parsed_yaml, default_flow_style=False) + "---"
        
        return final_yaml_str, os.path.join(PKM_ROOT, suggested_path_relative)

    except Exception as e:
        print(f"Error during LLM call or parsing: {e}")
        print("Defaulting to triage and inbox.")
        # Fallback for errors or ambiguous cases
        default_yaml = """---
status: triage
priority: P3
type: unknown
tags: ["#needs-review"]
source: ""
---"""
        return default_yaml, INBOX_PATH

def process_inbox():
    """
    Processes all files in the inbox.
    """
    inbox_files = get_inbox_files()
    destination_folders_relative = get_destination_folders()
    
    if not inbox_files:
        print("Inbox is empty. Nothing to process.")
        return
        
    print(f"Found {len(inbox_files)} files to process.")
    
    for file_name in inbox_files:
        file_path = os.path.join(INBOX_PATH, file_name)
        
        print(f"\n--- Processing: {file_name} ---")
        
        # 1. Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 2. Get suggestions from the LLM
        yaml_frontmatter, destination_folder_absolute = get_llm_suggestions(content, destination_folders_relative)
        
        # 3. Add the YAML frontmatter to the top of the file
        new_content = yaml_frontmatter + "\n\n" + content
        
        # For safety, we'll write to a new file first, then replace.
        # This is a good practice to avoid data loss if something goes wrong.
        temp_file_path = file_path + ".tmp"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        # 4. Move the file to the suggested destination
        new_file_path = os.path.join(destination_folder_absolute, file_name)
        
        print(f"Action: Prepending frontmatter to {file_name}")
        print(f"Action: Moving {file_name} to {destination_folder_absolute}")
        
        # --- UNCOMMENT THE FOLLOWING LINES TO ACTUALLY MODIFY FILES ---
        print("Applying changes...")
        shutil.move(temp_file_path, file_path) # This overwrites the original file with the new content
        shutil.move(file_path, new_file_path)
        print("Done.")


# --- Main Execution ---
if __name__ == "__main__":
    # Install required packages if not already installed
    # import subprocess
    # import sys
    # try:
    #     import google.generativeai
    #     import yaml
    # except ImportError:
    #     print("Installing required packages: google-generativeai PyYAML")
    #     subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai", "PyYAML"])
    
    process_inbox()

