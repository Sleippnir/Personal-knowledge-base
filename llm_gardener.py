import os
import shutil
import google.generativeai as genai
import yaml
import re
import string
# --- Gemini API Configuration ---
# The application will first try to load the API key from the `GEMINI_API_KEY` environment variable.
# If it's not found, it will fall back to importing it from `api.py`.
# This file is git-ignored for security.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        from api import GEMINI_API_KEY as key_from_file
        GEMINI_API_KEY = key_from_file
    except (ImportError, AttributeError):
        pass

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please set it as an environment variable or in `api.py`.")

# --- Configuration ---
PKM_ROOT = "."  # Obsidian vault root
INBOX_PATH = os.path.join(PKM_ROOT, "00_Inbox")
RESOURCES_PATH = os.path.join(PKM_ROOT, "03_Resources")
AREAS_PATH = os.path.join(PKM_ROOT, "02_Areas")
PROJECTS_PATH = os.path.join(PKM_ROOT, "01_Projects")

DRY_RUN = False

genai.configure(api_key=GEMINI_API_KEY) # type: ignore
model = genai.GenerativeModel('gemini-pro') # type: ignore


def get_inbox_files():
    return [
        f for f in os.listdir(INBOX_PATH)
        if os.path.isfile(os.path.join(INBOX_PATH, f)) and f.lower().endswith(('.md', '.txt'))
    ]

def get_destination_folders():
    def rel_paths(base_path, prefix):
        return [
            os.path.join(prefix, d)
            for d in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, d))
        ]
    return rel_paths(RESOURCES_PATH, "03_Resources") + \
           rel_paths(AREAS_PATH, "02_Areas") + \
           rel_paths(PROJECTS_PATH, "01_Projects")

def sanitize_filename(filename):
    valid_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c if c in valid_chars else '-' for c in filename)
    filename = filename.lower().replace(' ', '-')
    if not filename.endswith(('.md', '.txt')):
        filename += '.md'
    return filename.strip('-')


def get_llm_suggestions(file_content, destination_folders_relative):
    print("\n--- Sending to LLM ---")

    prompt = f"""You are an expert librarian. Your task is to analyze the provided content of a note and generate:

1. A valid YAML frontmatter block enclosed in `---` delimiters
2. A relative folder path from the list below
3. A suggested filename using kebab-case (e.g., `deep-learning-cheatsheet.md`)

Return these **in order**, separated by newlines, like so:

```
---
<yaml-keys>
---
relative/path/to/folder
suggested-filename.md
```

The content of the note is:
```
{file_content}
```

List of valid destination folders (relative to PKM_ROOT):
{destination_folders_relative}

Do not add any explanation or commentary. Output only the YAML, then folder, then filename.
"""

    try:
        response = model.generate_content(prompt)
        llm_output = response.text.strip()

        print("--- LLM Raw Response ---")
        print(llm_output)

        match = re.search(r'^---\n(.*?)\n---\n(.*?)\n(.*?)$', llm_output, re.DOTALL)
        if not match:
            raise ValueError("LLM output missing expected format.")

        yaml_body = match.group(1).strip()
        suggested_path_relative = match.group(2).strip()
        suggested_filename = match.group(3).strip()

        parsed_yaml = yaml.safe_load(yaml_body)
        if not isinstance(parsed_yaml, dict):
            raise ValueError("YAML is not a valid dictionary.")

        # Fill in missing fields
        defaults = {
            'status': 'triage',
            'priority': 'P3',
            'type': 'unknown',
            'tags': ['#needs-review'],
            'source': ''
        }
        for k, v in defaults.items():
            parsed_yaml.setdefault(k, v)

        # Normalize tags
        if isinstance(parsed_yaml.get('tags'), list):
            tags = [tag.lower().replace(" ", "-") for tag in parsed_yaml['tags']]
            parsed_yaml['tags'] = sorted(set(tags))

        # Validate folder
        folder_set = set(d.lower() for d in destination_folders_relative)
        if suggested_path_relative.lower() not in folder_set:
            print(f"Warning: Invalid folder '{suggested_path_relative}'. Defaulting to 00_Inbox.")
            suggested_path_relative = "00_Inbox"
            parsed_yaml['status'] = 'triage'
            if '#needs-review' not in parsed_yaml['tags']:
                parsed_yaml['tags'].append('#needs-review')

        yaml_str = "---\n" + yaml.dump(parsed_yaml, sort_keys=False, default_flow_style=False, allow_unicode=True).strip() + "\n---"
        return yaml_str, os.path.join(PKM_ROOT, suggested_path_relative), sanitize_filename(suggested_filename)

    except Exception as e:
        print(f"Error during LLM call or parsing: {e}")
        fallback_yaml = """---
status: triage
priority: P3
type: unknown
tags: ["#needs-review"]
source: ""
---"""
        return fallback_yaml, INBOX_PATH, None


def process_inbox():
    inbox_files = get_inbox_files()
    destination_folders_relative = get_destination_folders()

    if not inbox_files:
        print("Inbox is empty. Nothing to process.")
        return

    print(f"Found {len(inbox_files)} file(s) to process.")

    for file_name in inbox_files:
        file_path = os.path.join(INBOX_PATH, file_name)
        print(f"\n--- Processing: {file_name} ---")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"Error reading {file_name}. Skipping.")
            continue

        yaml_frontmatter, destination_folder_absolute, suggested_filename = get_llm_suggestions(content, destination_folders_relative)
        new_content = yaml_frontmatter + "\n\n" + content

        # Determine final filename
        final_filename = suggested_filename if suggested_filename else file_name
        new_file_path = os.path.join(destination_folder_absolute, final_filename)

        print(f"Action: Writing YAML frontmatter and moving to {new_file_path}")

        if DRY_RUN:
            print("[DRY RUN] No changes applied.")
            continue

        temp_file_path = file_path + ".tmp"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        shutil.move(temp_file_path, file_path)
        shutil.move(file_path, new_file_path)
        print("✓ File moved successfully.")


if __name__ == "__main__":
    process_inbox()


### 🔍 Example AI Output Format (strict)

# ```yaml
# ---
# status: learning
# priority: P2
# type: tutorial
# tags:
#   - python
#   - docker
#   - deployment
# source: "https://example.com/deploy-guide"
# ---
# 03_Resources/devops
# docker-deployment-guide.md
# ```

# ---




