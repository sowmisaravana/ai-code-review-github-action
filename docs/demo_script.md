# Demo Script & Verification Guide

Follow this guide to verify the AI Code Reviewer works as expected, both locally on your machine and integrated within GitHub Actions.

## Part 1: Local Verification (Dry-Run Mode)

You can run the review agent locally using Python. The `--dry-run` flag instructs the script to scan local files, analyze them using the Gemini API, and output the comments directly to the terminal without attempting to call GitHub APIs.

### Prerequisites
1. Install Python 3.8+.
2. Obtain a Gemini API Key from [Google AI Studio](https://aistudio.google.com/).

### Steps
1. Navigate to the project root directory:
   ```powershell
   cd c:\Users\sowmi\OneDrive\Desktop\Github
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```
4. Set up your Gemini API Key in the shell environment:
   ```powershell
   $env:GEMINI_API_KEY="your-gemini-api-key"
   ```
5. Run the orchestrator script in dry-run mode:
   ```powershell
   python review_agent.py --dry-run
   ```
6. **Expectation:** The script will locate the C# files in `sample-csharp-project/`, call the Gemini API for each, validate the responses, and print the markdown-formatted inline comments and reviews to your terminal.

---

## Part 2: GitHub Action Verification (End-to-End)

To test the system inside a live GitHub repository:

### Step 1: Create a GitHub Repository
1. Initialize a new public/private repository on GitHub.
2. Commit and push the codebase (including `.github/workflows/review.yml`, the Python scripts, prompts, and requirements) to the `main` branch.

### Step 2: Configure Secrets
1. In your GitHub repository, navigate to **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret**.
3. Name: `GEMINI_API_KEY`.
4. Value: Paste your Gemini API key.
5. Click **Add secret**.

### Step 3: Create a Pull Request
1. Create a new branch in your local repository:
   ```bash
   git checkout -b test-ai-reviewer
   ```
2. Make a minor modification to one of the sample C# files (e.g. add a comment or change a variable name in `sample-csharp-project/SOLID/S_SingleResponsibility.cs`). This ensures GitHub registers the file as "changed" in the PR diff.
3. Commit and push the branch:
   ```bash
   git add .
   git commit -m "add sample violations for review"
   git push origin test-ai-reviewer
   ```
4. On GitHub, open a **Pull Request** from `test-ai-reviewer` into `main`.

### Step 4: Verify Results
1. Navigate to the **Actions** tab of your repository. You should see the **AI Code Reviewer** workflow start running.
2. Wait for the run to complete. Check the logs of the "Run Gemini AI Code Review" step to see the orchestrator output, files analyzed, and API responses.
3. Go back to the **Conversation** or **Files changed** tab of the Pull Request.
4. **Expectation:** You will see a detailed review submitted by the GitHub Actions bot containing:
   - A summary comment showing the breakdown of issues (High, Medium, Low).
   - Inline comments on the exact lines in the files (like `NullViolations.cs` or `AsyncViolations.cs`) describing the violations and suggestions.
