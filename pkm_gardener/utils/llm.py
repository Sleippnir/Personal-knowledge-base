import google.generativeai as genai
import yaml
import re
from pkm_gardener.config import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

def get_llm_suggestions(
    file_content: str, destination_folders_relative: list
) -> tuple[dict, str, str, str]:
    """
    Uses the Gemini API to get YAML frontmatter, a suggested filename, folder, and summary.
    Returns a tuple of: (parsed_metadata, suggested_filename, suggested_folder_relative, summary)
    """
    print("\n--- Sending to LLM ---")

    prompt = f"""You are an expert librarian. Your task is to analyze the provided content of a note and generate four items:
1. A valid YAML frontmatter block based on the rules below.
2. A one-sentence summary of the content.
3. A suggested relative folder path from the provided list.
4. A suggested filename in kebab-case (e.g., `deep-learning-cheatsheet.md`).

Return these four items, each on a new line, in the following strict order:
```
---
<yaml-keys-and-values>
---
This is a one-sentence summary of the note content.
relative/path/to/folder
suggested-filename.md
```

**YAML Rules:**
- **status**: `active-tool`, `learning`, `archived`, or `triage`.
- **priority**: `P1`, `P2`, `P3`, or `P4`.
- **type**: `repo`, `paper`, `tutorial`, `cheatsheet`, `SOP`, `course`, or `website`.
- **tags**: A list of 3-5 relevant lowercase, kebab-case tags.
- **source**: The primary URL if the content is from a webpage, otherwise empty.

**Folder Rules:**
- **01_Projects**: For content related to a specific, time-bound goal.
- **02_Areas**: For content related to an ongoing responsibility.
- **03_Resources**: The default destination for general knowledge and reference material.
- **Ambiguity**: If categorization is unclear, set status to `triage`, add `#needs-review` tag, and use `00_Inbox` as the folder.

**Content to Analyze:**
```
{file_content}
```

**List of Valid Destination Folders:**
{destination_folders_relative}

Do not add any explanation. Output only the four requested items, each on its own line, in the specified order.
"""

    try:
        response = model.generate_content(prompt)
        llm_output = response.text.strip()
        print("--- LLM Raw Response ---")
        print(llm_output)

        match = re.search(
            r'^---\n(.*?)\n---\n(.*?)\n(.*?)\n(.*?)$', llm_output, re.DOTALL
        )
        if not match:
            raise ValueError("LLM output did not match the expected 4-part format.")

        yaml_body = match.group(1).strip()
        summary = match.group(2).strip()
        suggested_folder_relative = match.group(3).strip()
        suggested_filename = match.group(4).strip()

        parsed_yaml = yaml.safe_load(yaml_body)
        if not isinstance(parsed_yaml, dict):
            raise ValueError("LLM output YAML is not a valid dictionary.")

        # Validate folder
        valid_folders = set(d.lower() for d in destination_folders_relative)
        valid_folders.add("00_inbox") # Add inbox as a valid destination
        if suggested_folder_relative.lower() not in valid_folders:
            print(f"Warning: Invalid folder '{suggested_folder_relative}'. Defaulting to 00_Inbox.")
            print(f"Warning: Invalid folder '{suggested_folder_relative}'. Defaulting to 00_inbox.")
            suggested_folder_relative = "00_inbox"
            parsed_yaml['status'] = 'triage'
            if 'tags' not in parsed_yaml or not isinstance(parsed_yaml['tags'], list):
                parsed_yaml['tags'] = []
            if '#needs-review' not in parsed_yaml['tags']:
                parsed_yaml['tags'].append('#needs-review')

        return parsed_yaml, suggested_filename, suggested_folder_relative, summary

    except Exception as e:
        print(f"Error during LLM call or parsing: {e}")
        fallback_yaml = {
            'status': 'triage',
            'priority': 'P3',
            'type': 'unknown',
            'tags': ['#needs-review'],
            'source': ''
        }
        # Return a tuple that matches the function's type hint
        return fallback_yaml, "unnamed-file.md", "00_Inbox", "Could not be processed."
