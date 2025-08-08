import google.generativeai as genai
import yaml
import os
from PIL import Image
import io

from pkm_gardener.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, PKM_ROOT, INBOX_PATH

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

def get_llm_vision_suggestions(image_bytes: bytes, destination_folders_relative: list) -> tuple[str, str]:
    """
    Uses the Gemini API to get YAML frontmatter and a suggested destination folder for an image.
    """
    print("\n--- Sending Image to LLM ---")

    image = Image.open(io.BytesIO(image_bytes))

    prompt = f"""You are an expert librarian. Your task is to analyze the provided image and generate a YAML frontmatter block and suggest a destination folder.

Here are the strict rules for generating the YAML frontmatter. Base your answers on the content of the image (e.g., screenshots of code, diagrams, photos).

1.  **status**: `learning` if it's a diagram or screenshot for study, `archived` for photos or references. Default to `triage`.
2.  **priority**: Default to `P3` unless the image contains text that indicates urgency.
3.  **type**: `screenshot`, `diagram`, `photo`, `illustration`.
4.  **tags**: Generate a list of 3-5 tags describing the key objects, concepts, or text in the image.
5.  **summary**: A concise, one-sentence description of what the image shows.
6.  **source**: Leave empty unless the image is a screenshot of a website with the URL visible.

Here is an example of a perfect output for an image of a Python code screenshot:
```
---
status: learning
priority: P3
type: screenshot
tags: [python, pandas, data-manipulation]
summary: A screenshot of Python code demonstrating how to use the a Pandas DataFrame.
source: ""
---
03_Resources/Resources_Software_Development
```

The list of possible destination folders (relative paths from PKM_ROOT) is:
{destination_folders_relative}

Your output must be ONLY the YAML block, followed by a newline, and then the relative path to the suggested destination folder. Do NOT include any other text or explanation.
"""

    try:
        response = model.generate_content([prompt, image])
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
        if not is_safe_path(suggested_path_relative) and suggested_path_relative != "00_Inbox":
            print(f"Warning: LLM suggested an invalid or unsafe path: {suggested_path_relative}. Defaulting to 00_Inbox.")
            suggested_path_relative = "00_Inbox"
            parsed_yaml['status'] = 'triage'
            if 'tags' in parsed_yaml and isinstance(parsed_yaml['tags'], list):
                if '#needs-review' not in parsed_yaml['tags']:
                    parsed_yaml['tags'].append('#needs-review')
            else:
                parsed_yaml['tags'] = ['#needs-review']

        # Reconstruct YAML string in case of modifications
        final_yaml_str = "---\n" + yaml.dump(parsed_yaml, default_flow_style=False) + "---\n"

        return final_yaml_str, os.path.join(PKM_ROOT, suggested_path_relative)

    except Exception as e:
        print(f"Error during LLM call or parsing: {e}")
        print("Defaulting to triage and inbox.")
        # Fallback for errors or ambiguous cases
        default_yaml = """---\nstatus: triage\npriority: P3\ntype: image\ntags: ["#needs-review"]\nsource: ""\n---\n"""
        return default_yaml, INBOX_PATH

def is_safe_path(suggested_path: str) -> bool:
    """
    Validates that the suggested path is safe and conforms to the PKM structure.
    - It must be a subdirectory of one of the main P.A.R.A. folders.
    - It must not contain any directory traversal components.
    """
    allowed_bases = ["01_Projects", "02_Areas", "03_Resources"]

    # Normalize path to resolve `.` or `..` and platform-specific separators
    normalized_path = os.path.normpath(suggested_path)

    # After normalization, a safe path on POSIX systems won't start with '/' or '..'.
    # This check helps prevent directory traversal.
    if os.path.isabs(normalized_path) or normalized_path.startswith(".."):
        return False

    # Check if the path starts with one of the allowed base directories
    for base in allowed_bases:
        if normalized_path.startswith(base):
            return True

    return False

def get_llm_suggestions(file_content: str, destination_folders_relative: list) -> tuple[str, str]:
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

5.  **summary**: A concise, one-sentence summary of the note's core content. This should be a string, not a list.

6.  **source**: If the file content is derived from a web page, the primary URL **must** be placed in this field. If the note is original thought, this field will be left empty.

Here is an example of a perfect output:
```
---
status: learning
priority: P2
type: tutorial
tags: [python, data-science, pandas]
summary: A tutorial on using the Pandas library for data manipulation in Python.
source: "https://realpython.com/pandas-guide/"
---
03_Resources/Resources_Software_Development
```

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

4.  **Creating New Subfolders**:
    -   If the note covers a new, specific topic that doesn't fit well into any of the existing folders, you are encouraged to **suggest a new, descriptive subfolder**.
    -   The new subfolder **must** be created inside one of the three main parent directories (e.g., `03_Resources/Resources_New_Topic`, `01_Projects/Project_New_Thing`).
    -   The subfolder name should be in `PascalCase` and be descriptive. For example, if a note is about "Quantum Computing," a good suggestion would be `03_Resources/Resources_Quantum_Computing`.

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
        if not is_safe_path(suggested_path_relative) and suggested_path_relative != "00_Inbox":
            print(f"Warning: LLM suggested an invalid or unsafe path: {suggested_path_relative}. Defaulting to 00_Inbox.")
            suggested_path_relative = "00_Inbox"
            parsed_yaml['status'] = 'triage'
            if 'tags' in parsed_yaml and isinstance(parsed_yaml['tags'], list):
                if '#needs-review' not in parsed_yaml['tags']:
                    parsed_yaml['tags'].append('#needs-review')
            else:
                parsed_yaml['tags'] = ['#needs-review']
        
        # Reconstruct YAML string in case of modifications
        final_yaml_str = "---\n" + yaml.dump(parsed_yaml, default_flow_style=False) + "---\n" # Added newline for consistency
        
        return final_yaml_str, os.path.join(PKM_ROOT, suggested_path_relative)

    except Exception as e:
        print(f"Error during LLM call or parsing: {e}")
        print("Defaulting to triage and inbox.")
        # Fallback for errors or ambiguous cases
        default_yaml = """---\nstatus: triage\npriority: P3\ntype: unknown\ntags: ["#needs-review"]\nsource: ""\n---\n""" # Added newline for consistency
        return default_yaml, INBOX_PATH
