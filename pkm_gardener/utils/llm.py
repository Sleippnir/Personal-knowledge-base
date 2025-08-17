import google.generativeai as genai
import yaml
import re
from pkm_gardener.config import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

def get_llm_suggestions(
    file_content: str, destination_folders_relative: list
) -> tuple[dict, str, str, str, str, str]:
    """
    Uses the Gemini API to get YAML frontmatter, a suggested filename, folder, and summary.
    Returns a tuple of: (parsed_metadata, title, suggested_filename, suggested_folder_relative, summary, status)
    """
    print("\n--- Sending to LLM ---")

    prompt = f"""You are an expert librarian and metadata specialist. Your task is to analyze the provided content and generate four items in a strict, specific format.

**Instructions:**
1.  **Generate YAML Frontmatter:** Create a valid YAML block with detailed metadata, including a `title`.
2.  **Generate a Summary:** Write a one-paragraph summary of the content.
3.  **Suggest a Folder:** Suggest a relative folder path from the provided list. If no suitable folder exists, suggest a new, logical folder path within the PARA structure (e.g., `01_Projects/New-Project-Name`).
4.  **Suggest a Filename:** Suggest a filename in kebab-case (e.g., `deep-learning-cheatsheet.md`).

**Return these four items, each on a new line, in the following strict order:**
```
---
<yaml-keys-and-values>
---
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

Do not add any explanation. Output only the four requested items, each on its own line, in the specified order.
"""

    try:
        response = model.generate_content(prompt)
        llm_output = response.text.strip()
        print("--- LLM Raw Response ---")
        print(llm_output)

        # More robust parsing
        # 1. Find the YAML block
        yaml_match = re.search(r'^---\s*\n(.*?)\n\s*---', llm_output, re.DOTALL)
        if not yaml_match:
            raise ValueError("LLM output did not contain a valid YAML block.")

        yaml_body = yaml_match.group(1).strip()
        parsed_yaml = yaml.safe_load(yaml_body)
        if not isinstance(parsed_yaml, dict):
            raise ValueError("LLM output YAML is not a valid dictionary.")

        # 2. Get the rest of the content and split into parts
        rest_of_output = llm_output[yaml_match.end():].strip()
        parts = [line.strip() for line in rest_of_output.split('\n') if line.strip()]

        if len(parts) != 3:
            raise ValueError(f"Expected 3 parts after YAML (summary, folder, filename), but got {len(parts)}: {parts}")

        summary = parts[0]
        suggested_folder_relative = parts[1]
        suggested_filename = parts[2]

        # 3. Get title from YAML
        title = parsed_yaml.get('title', 'Untitled')

        return parsed_yaml, title, suggested_filename, suggested_folder_relative, summary, "success"

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
        return fallback_yaml, "Untitled", "unnamed-file.md", "00_Inbox", "Could not be processed.", "failure"
