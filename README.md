# Limbus Company - JP Translation Revision

This project aims to identify and correct typographical errors and some mistranslations found in the official Japanese localization of **Limbus Company**, and to provide a report documenting those corrections.

- All proofreading is conducted on [ParaTranz](https://paratranz.cn/projects/14860), and the reports are generated based on the results.

- As a by-product, a Mod utilizing the game's **custom language feature** is also provided. This allows project contributors to check the corrections in-game.

## 📄 Deliverables

- `report_general.csv`  
  General proofreading report

- `report_storydata.csv`  
  Proofreading report (story-related)

- `Localize_Fixed/jp_fixed/`  
  Japanese localization files with corrections applied (JP_*.json, identical structure to Localize/jp/)

- `Localize_Fixed/jp_mod/`  
  Custom language Mod built from the above Japanese localization files

## 🛠 Other Contents

- `Localize/kr/, Localize/en/, Localize/jp/`  
  Backups of the official language files

- `paratranz/`  
  Backups of translation files retrieved from ParaTranz

- `Utilities/Importer`  
  Tool for automatically generating reports (uses files from Localize/* and paratranz/*)

- `Utilities/`  
  Python programs for project management and proofreading

---

## 📝 Report Categories

The generated reports (`report_general.csv` / `report_storydata.csv`) classify issues into the following categories:

### ✅ Typo (Typographical errors)
Clear mistakes in the Japanese text. Includes:

- Missing characters
- Extraneous characters
- Typing or conversion errors
- Missing paragraphs
- Misused homophones or kanji
- Incorrect numbers or keywords
- Inconsistent notation
- Other clear errors

### ❓ Possible mistranslation
Japanese translations that appear inconsistent with the original text's meaning or fail to reflect its intent appropriately.

### 💬 Wording fix
Adjustments for clarity, naturalness, or readability in Japanese. Includes:

- Incorrect particles or syntactic structure requiring general revision
- Misused compound words or idioms
- Redundant or repetitive phrasing
- Unnecessarily hard-to-understand translations
- Adding furigana to difficult kanji or expressions where readability is hindered

##### "Typo" always include a suggested correction. Other categories may only note the issue without a suggested revision.
---

### 📚 License
The proofreading reports and related programs in this repository are licensed under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.

This repository is based on the official translation language files of *Limbus Company*. All original texts, translations, and other intellectual property rights belong to Project Moon.

This is an unofficial project and is not endorsed or affiliated with Project Moon. All proposed corrections and derivative content are intended solely to assist in improving the quality of the official translations, and are provided for Project Moon’s reference.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

#### ➕ Additional Permission (CCPlus)

[Project Moon](https://projectmoon.studio) is granted permission to use, modify, and redistribute the contents of this repository without attribution.  
This additional permission is granted specifically to Project Moon, in addition to the rights provided under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.
