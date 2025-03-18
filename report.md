# Repolinter Report

*This report was generated automatically by the Repolinter.*

This Repolinter run generated the following results:
| ❗  Error | ❌  Fail | ⚠️  Warn | ✅  Pass | Ignored | Total |
|---|---|---|---|---|---|
| 0 | 0 | 6 | 9 | 0 | 15 |

- [Warning](#user-content-warning)
  - [⚠️ `binary-document`](#user-content--binary-document)
  - [⚠️ `font-file`](#user-content--font-file)
  - [⚠️ `third-party-image`](#user-content--third-party-image)
  - [⚠️ `general-logo`](#user-content--general-logo)
  - [⚠️ `prohibited-license`](#user-content--prohibited-license)
  - [⚠️ `hidden-or-generated-file`](#user-content--hidden-or-generated-file)
- [Passed](#user-content-passed)
  - [✅ `binary-exec-lib`](#user-content--binary-exec-lib)
  - [✅ `binary-archive`](#user-content--binary-archive)
  - [✅ `amazon-logo`](#user-content--amazon-logo)
  - [✅ `dataset`](#user-content--dataset)
  - [✅ `dockerfile`](#user-content--dockerfile)
  - [✅ `dockerfile-download-statement`](#user-content--dockerfile-download-statement)
  - [✅ `internal-url`](#user-content--internal-url)
  - [✅ `third-party-license-file`](#user-content--third-party-license-file)
  - [✅ `large-file`](#user-content--large-file)

## Warning <a href="#user-content-warning" id="user-content-warning">#</a>

<details>
<summary>Click to see rules</summary>

### ⚠️ `binary-document` <a href="#user-content--binary-document" id="user-content--binary-document">#</a>

Found files. (`AOS-RAG-architecture.pptx`). For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Binary-Document.

### ⚠️ `font-file` <a href="#user-content--font-file" id="user-content--font-file">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Font-File. Found files. Below is a list of files or patterns that failed:

- `frontend/public/vite.svg`
- `frontend/src/assets/react.svg`

### ⚠️ `third-party-image` <a href="#user-content--third-party-image" id="user-content--third-party-image">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Third-Party-Image. Found files. Below is a list of files or patterns that failed:

- `frontend/public/vite.svg`
- `frontend/src/assets/react.svg`

### ⚠️ `general-logo` <a href="#user-content--general-logo" id="user-content--general-logo">#</a>

Found files. (`frontend/src/components/LogoutButton.tsx`). For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Third-Party-Image/#HLogos.

### ⚠️ `prohibited-license` <a href="#user-content--prohibited-license" id="user-content--prohibited-license">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Prohibited-License/. Below is a list of files or patterns that failed:

- `my-cdk-project/package-lock.json`: Contains 'GPL-3' on line 4298, context:
	|      "license": "(MIT OR GPL-3.0-or-later)",.
- `my-cdk-project/package-lock.json`: Contains 'GPL-3' on line 6922, context:
	|      "license": "(MIT OR GPL-3.0-or-later)",.

### ⚠️ `hidden-or-generated-file` <a href="#user-content--hidden-or-generated-file" id="user-content--hidden-or-generated-file">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Hidden-Generated-File. Found files. Below is a list of files or patterns that failed:

- `frontend/.env`
- `frontend/.gitignore`
- `my-cdk-project/.env`
- `my-cdk-project/.gitignore`
- `my-cdk-project/.npmignore`

</details>

## Passed <a href="#user-content-passed" id="user-content-passed">#</a>

<details>
<summary>Click to see rules</summary>

### ✅ `binary-exec-lib` <a href="#user-content--binary-exec-lib" id="user-content--binary-exec-lib">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Binary-Exe-Lib. Did not find a file matching the specified patterns. All files passed this test.

### ✅ `binary-archive` <a href="#user-content--binary-archive" id="user-content--binary-archive">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Binary-Archive. Did not find a file matching the specified patterns. All files passed this test.

### ✅ `amazon-logo` <a href="#user-content--amazon-logo" id="user-content--amazon-logo">#</a>

No file matching hash found. For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Amazon-Logo.

### ✅ `dataset` <a href="#user-content--dataset" id="user-content--dataset">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Dataset. Did not find a file matching the specified patterns. All files passed this test.

### ✅ `dockerfile` <a href="#user-content--dockerfile" id="user-content--dockerfile">#</a>

Did not find a file matching the specified patterns. (`**/*docker*`). For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Dockerfile.

### ✅ `dockerfile-download-statement` <a href="#user-content--dockerfile-download-statement" id="user-content--dockerfile-download-statement">#</a>

Did not find content matching specified patterns. For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Dockerfile-Download-Statement/.

### ✅ `internal-url` <a href="#user-content--internal-url" id="user-content--internal-url">#</a>

Did not find content matching specified patterns. For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Internal-URL.

### ✅ `third-party-license-file` <a href="#user-content--third-party-license-file" id="user-content--third-party-license-file">#</a>

For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Third-Party-License-File/. Did not find a file matching the specified patterns. All files passed this test.

### ✅ `large-file` <a href="#user-content--large-file" id="user-content--large-file">#</a>

No file larger than 500000 bytes found.. For more information please visit https://w.amazon.com/bin/view/Open_Source/Tools/Repolinter/Ruleset/Large-File.

</details>

