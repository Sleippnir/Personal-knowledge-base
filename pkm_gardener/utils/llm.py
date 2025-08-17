import google.generativeai as genai
import yaml
import re
from pkm_gardener.config import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

def get_llm_suggestions(
    file_content: str, destination_folders_relative: list
) -> tuple[dict, str, str, str, str]:
    """
    Uses the Gemini API to get YAML frontmatter, a suggested filename, folder, and summary.
    Returns a tuple of: (parsed_metadata, title, suggested_filename, suggested_folder_relative, summary)
    """
    print("\n--- Sending to LLM ---")

    prompt = f"""You are an expert librarian and metadata specialist. Your task is to analyze the provided content and generate five items in a strict, specific format.

**Instructions:**
1.  **Generate YAML Frontmatter:** Create a valid YAML block with detailed metadata.
2.  **Generate a Title:** Create a concise, descriptive title for the content.
3.  **Generate a Summary:** Write a one-paragraph summary of the content.
4.  **Suggest a Folder:** Suggest a relative folder path from the provided list. If no suitable folder exists, suggest a new, logical folder path within the PARA structure (e.g., `01_Projects/New-Project-Name`).
5.  **Suggest a Filename:** Suggest a filename in kebab-case (e.g., `deep-learning-cheatsheet.md`).

**Return these five items, each on a new line, in the following strict order:**
```
---
<yaml-keys-and-values>
---
Title of the Note
A one-paragraph summary of the note content.
relative/path/to/folder
suggested-filename.md
```

**YAML Rules:**
- **`title`**: A concise, descriptive title.
- **`status`**: `active-tool`, `learning`, `archived`, or `triage`.
- **`priority`**: `P1`, `P2`, `P3`, or `P4`.
- **`type`**: `repo`, `paper`, `tutorial`, `cheatsheet`, `SOP`, `course`, `website`, `image`, `pdf`, `csv`, or `document`.
- **`tags`**: A list of 5-7 relevant lowercase, kebab-case tags.
- **`source`**: The primary URL if the content is from a webpage, otherwise empty.
- **`entities`**: A list of key people, organizations, or topics mentioned.
- **`confidence_score`**: A value from 0.0 to 1.0 indicating your confidence in the generated metadata.

**Folder Rules:**
- **`01_Projects`**: For content related to a specific, time-bound goal.
- **`02_Areas`**: For content related to an ongoing responsibility.
- **`03_Resources`**: The default destination for general knowledge and reference material.
- **Prioritize Existing Folders**: First, try to place the file in one of the existing folders.
- **Create New Folders**: If no existing folder is a good match, create a new, descriptive folder within the most appropriate PARA category.

**Content to Analyze:**
```
{file_content}
```

**List of Valid Destination Folders:**
```
{destination_folders_relative}
```

Do not add any explanation. Output only the five requested items, each on its own line, in the specified order.
"""

    try:
        response = model.generate_content(prompt)
        llm_output = response.text.strip()
        print("--- LLM Raw Response ---")
        print(llm_output)

        match = re.search(
            r'^---\n(.*?)\n---\n(.*?)\n(.*?)\n(.*?)\n(.*?)$', llm_output, re.DOTALL
        )
        if not match:
            raise ValueError("LLM output did not match the expected 5-part format.")

        yaml_body = match.group(1).strip()
        title = match.group(2).strip()
        summary = match.group(3).strip()
        suggested_folder_relative = match.group(4).strip()
        suggested_filename = match.group(5).strip()

        parsed_yaml = yaml.safe_load(yaml_body)
        if not isinstance(parsed_yaml, dict):
            raise ValueError("LLM output YAML is not a valid dictionary.")

        return parsed_yaml, title, suggested_filename, suggested_folder_relative, summary

    except Exception as e:
        print(f"Error during LLM call or parsing: {e}")
        fallback_yaml = {
            'status': 'triage',
            'priority': 'P3',
            'type': 'unknown',
            'tags': ['#needs-review'],
            'source': '',
            'entities': [],
            'confidence_score': 0.0,
            'title': 'Untitled'
        }
        return fallback_yaml, "Untitled", "unnamed-file.md", "00_Inbox", "Could not be processed."
