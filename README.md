# GitHub Actions Workflow Smell Detector

A small, rule-based detector for **GitHub Actions workflow smells** focused on three high-impact issues:

1. **S1 – Floating action tags**  
   Using `uses: owner/repo@main` or other branch-like refs instead of a pinned tag or commit SHA.

2. **S2 – Missing timeouts**  
   Jobs without `timeout-minutes`, which can lead to stuck or overly long CI runs.

3. **S3 – Broad permissions**  
   Workflows or jobs that grant the `GITHUB_TOKEN` unnecessary `write` permissions (e.g., `issues: write`, `pull-requests: write`, `contents: write`).

This repository contains the **prototype CLI tool** and simple scripts used in a research study on GitHub Actions workflow smells for the MS Software Engineering course *Software Systems Design & Architecture* (NUST College of E&ME).

---

## 1. Features (Current Prototype)

- Scans all `.yml` / `.yaml` files under `.github/workflows/` for a given repository.
- Applies **three simple static rules** (S1–S3) to detect potential workflow smells.
- Prints per-finding lines with:
    - Smell ID (S1, S2, S3),
    - File path,
    - Job name (if applicable),
    - A short explanation.
- Prints a **summary table** with total counts for each smell.
- Designed to be **small, explainable, and easy to extend**, not to cover every possible smell.

---

## 2. Installation

### 2.1. Clone this repository

```bash
git clone https://github.com/usmansadiq786/gha-workflow-smells.git
cd gha-workflow-smells
```

### 2.2. Python environment

You can use system Python or create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate   # on macOS / Linux
# .\venv\Scripts\activate  # on Windows PowerShell
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Basic Usage

The main entrypoint is the CLI script:

```bash
python gha_smell_detector.py /path/to/local/repo
```

Example:

```bash
python gha_smell_detector.py ./repos/numpy
```

Sample output (simplified):

```text
[S2_MISSING_TIMEOUT] /path/to/repo/.github/workflows/tests.yml :: job:tests :: job has no timeout-minutes
[S3_BROAD_PERMISSIONS] /path/to/repo/.github/workflows/publish.yml :: job:publish :: job permissions={'contents': 'write', 'id-token': 'write'}

Summary:
  S1_FLOATING_TAG: 7
  S2_MISSING_TIMEOUT: 48
  S3_BROAD_PERMISSIONS: 5

Basic Fix Suggestions:
  S1_FLOATING_TAG      -> Pin action to a stable tag or commit SHA
  S2_MISSING_TIMEOUT   -> Add 'timeout-minutes: <value>' at job level
  S3_BROAD_PERMISSIONS -> Restrict permissions to minimum required scopes
```

You can run the tool on any local Git repository that uses GitHub Actions.

---

## 4. Reproducing the Research Dataset

The research study includes a pilot dataset of public open-source repositories
(for example: `django/django`, `pallets/flask`, `greyli/flask-extension-status`,
`numpy/numpy`, `psf/requests`, `jssaggu/springboot-tutorial`, `actions/starter-workflows`).

These repositories are listed in:

```text
data/repo_list.txt
```

Each line contains a GitHub `<owner>/<repo>` pair, e.g.:

```text
django/django
pallets/flask
greyli/flask-extension-status
numpy/numpy
psf/requests
jssaggu/springboot-tutorial
actions/starter-workflows
```

### 4.1. Clone pilot repositories

Use the helper script:

```bash
chmod +x scripts/clone_repos.sh
./scripts/clone_repos.sh
```

This will:

- Create a `./repos` directory (if it doesn’t exist),
- Change into `repos/`,
- Clone each public GitHub repository listed in `data/repo_list.txt` using HTTPS.

> All repositories are public and cloned over HTTPS. No tokens or credentials are required.

### 4.2. Run the detector on all repos

You can use:

```bash
chmod +x scripts/run_detector_on_all_repos.sh
./scripts/run_detector_on_all_repos.sh
```

Otherwise, a simple Bash loop also works:

```bash
for d in ./repos/*; do
  if [ -d "$d/.git" ]; then
    echo "=== Scanning $d ==="
    python gha_smell_detector.py "$d"
    echo
  fi
done
```

You can redirect the output into a file for further analysis:

```bash
./scripts/run_detector_on_all_repos.sh > results_output.txt
# or, for a single repo:
python gha_smell_detector.py ./repos/numpy > results_numpy.txt
```

---

## 5. Smell Definitions and Rules

The prototype currently checks three smells:

- **S1 – Floating action tags**
    - Detects `uses: owner/repo@ref` where `ref` looks like a branch (`main`, `master`, other branch names) or is missing.
    - Also flags paths like `uses: ./.github/some-action` as internal, unpinned actions.
    - Suggestion: pin to a stable tag (e.g., `@v3`) or a commit SHA.

- **S2 – Missing timeouts**
    - Detects jobs that do not declare the `timeout-minutes` field.
    - Suggestion: add `timeout-minutes: <value>` at the job level (e.g., 10–30 minutes, depending on the project).

- **S3 – Broad permissions**
    - Detects workflows or jobs with a `permissions:` block that sets any scope to `write` or `write-all` (for example: `issues: write`, `pull-requests: write`, `contents: write`, `security-events: write`).
    - Suggestion: use the least privilege needed (typically read-only for most CI jobs).

> Important: Some detections are intentional (for example, issue-locking or release workflows need write access). The tool therefore reports potential smells, not guaranteed mistakes.

---

## 6. Limitations

This is an early-stage research prototype, not a production security scanner:

- Focuses on only three smells (S1–S3).
- Does not yet compute precision / recall against a fully manually-labelled dataset.
- Does not understand the full project context (for example, whether a broad permission is justified in a release workflow).
- Handles standard GitHub-hosted workflows; self-hosted or highly dynamic patterns may require further work.

Despite these limitations, the tool is useful as a baseline and as a teaching / research artifact for configuration smells in GitHub Actions.

---

## 7. Research Context and Citation

This tool is part of a master's-level research project on “Detecting Critical Workflow Smells in GitHub Actions: A Rule-Based Baseline”.

If you use this repository in academic work, please cite it as:

```bibtex
@misc{sadiq2025ghasmelldetector,
  author       = {Sadiq, Usman},
  title        = {gha-workflow-smells: A Rule-Based Detector for GitHub Actions Workflow Smells},
  year         = {2025},
  howpublished = {GitHub repository},
  url          = {https://github.com/usmansadiq786/gha-workflow-smells},
  note         = {Accessed 07 Dec. 2025}
}
```

The corresponding paper cites this repository as the replication package for scripts and dataset reconstruction.

---

## 8. Contributing / Future Work

Planned or possible enhancements:

- Extend to more smells (e.g., redundant matrix configurations, unsafe cache usage).
- Add basic configuration options (ignore lists, per-project policies).
- Integrate as a pre-commit hook or GitHub Action.
- Combine this rule-based detector with LLM-assisted suggestions for fixes and PR descriptions.

At this stage, contributions are welcome in the form of:

- Bug reports / false-positive examples,
- Suggestions for additional smells,
- Small PRs improving rule coverage or documentation.

---

## 9. License

This project is open source.  
See [LICENSE](./LICENSE) for details.
