
# 🧠 My Personal Knowledge Management (PKM) System

This repository serves as a single source of truth for all my notes, projects, and resources. It is a living system designed for fast retrieval and active knowledge development, managed primarily with [Obsidian](https://obsidian.md/) and version-controlled with Git.

## ## Core Philosophy

The system is built on a customized **P.A.R.A.** (Projects, Areas, Resources, Archives) method. The primary goal is to separate **actionable information** (active projects and responsibilities) from **reference material** (a general knowledge library), ensuring clarity and focus.

---

## ## 📂 Directory Structure

The repository is organized into four top-level folders, each with a distinct purpose:

* **`00_Inbox`**: The **capture point**. All new, unsorted notes, links, and documents land here first before being processed.
* **`01_Projects`**: Holds materials for **active work** with a specific goal and a defined end date. This is for things I am actively *building*.
* **`02_Areas`**: Contains information related to my **ongoing responsibilities** and standards that don't have a deadline. This is for things I am actively *maintaining*.
* **`03_Resources`**: My **personal library**. This is the default home for any useful information, tool, or topic of interest that isn't tied to a specific project or area. This is for things I am *referencing*.

---

## ## ⚙️ How It Works: The Workflow

1.  **Capture**: New information is captured frictionlessly into the `00_Inbox`.
2.  **Process ("Gardening")**: On a regular basis, I review items in the `Inbox`.
3.  **Define & File**: During the review, I add a metadata block to the top of each note and move it to its permanent home in `Projects`, `Areas`, or `Resources`.

---

## ## Metadata Standard

Every processed note contains a YAML frontmatter block at the top to power search and filtering.

### ### Metadata Template:
```yaml
---
status: triage
priority: P3
type: 
tags: []
source: ""
---
````

- **status**: The current state of the note (`triage`, `learning`, `active-tool`, `archived`).
    
- **priority**: The importance level (`P1` to `P4`).
    
- **type**: The kind of information (`paper`, `tutorial`, `repo`, `cheatsheet`, etc.).
    
- **tags**: A list of relevant keywords for searching.
    
- **source**: The original URL, if applicable.
    

---

## ## File Naming Convention

The standard convention is a guideline for clarity while Browse:

**`Topic-or-Project_Descriptor.md`**

- _Example:_ `Docker-Tutorial_Digital-Ocean-Guide.md`
    

This standard is flexible. The primary goal is for the filename to be identifiable, while the metadata handles the complex sorting and filtering.
