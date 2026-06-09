# 🤖 AI C# Code Reviewer GitHub Action

A production-ready GitHub Action that automatically reviews C# pull requests using Google's Gemini AI. When a PR is opened or updated, the action extracts changed C# files, performs static analysis, and submits structured inline review comments back to the PR.

## Features

- **C# Static Analysis:** Reviews code against SOLID principles, Null Handling guidelines, and Async/Await correctness.
- **Changed-Line Filtering:** Intelligently parses unified git diff patches to ensure inline comments are posted *only* on added or modified lines of code.
- **Agentic Validation Loop:** Automatically validates Gemini's JSON response using Pydantic and executes an auto-correction retry loop if the output format deviates.
- **Consolidated PR Reviews:** Bundles findings into a single consolidated PR review (comments and overall summary) rather than spamming individual comments.
- **Dry-run Mode:** Supports local testing without hitting GitHub API endpoints or creating PRs.

---

## Folder Structure

```
.
├── .github/
│   └── workflows/
│       └── review.yml          # GitHub Action definition
├── agent/
│   ├── formatter.py            # Formats findings to GitHub Markdown
│   ├── gemini_client.py        # Client wrapper with validation & retries
│   ├── github_handler.py       # PyGithub integration and patch parsing logic
│   └── review_agent.py         # Main entry point and orchestrator
├── docs/
│   ├── architecture.md         # Architecture diagrams and design details
│   ├── demo_script.md          # Guide to verify locally and in GitHub
│   └── prompts_used.md         # Prompt design and retry strategy documentation
├── prompts/
│   └── review_prompt.txt       # System instructions template for Gemini
├── sample-csharp-project/       # Demo project containing target C# bugs
│   ├── SOLID/
│   ├── NullHandling/
│   └── AsyncCorrectness/
├── .env.example                # Example environment variables file
├── README.md                   # Setup and usage guide
└── requirements.txt            # Python dependencies
```

---

## Setup & Configuration

### 1. Local Development / Dry Run

To dry-run the analysis locally over the sample files:
1. Clone this repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Gemini API key:
   ```bash
   # Powershell
   $env:GEMINI_API_KEY="your-gemini-api-key"
   # Bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```
4. Run the orchestrator in dry-run mode:
   ```bash
   python agent/review_agent.py --dry-run
   ```

### 2. GitHub Action Integration

To integrate this reviewer into your repository:

1. Add your Gemini API key as a GitHub secret:
   - Go to your repository **Settings** -> **Secrets and variables** -> **Actions**.
   - Create a secret named `GEMINI_API_KEY` containing your Gemini API key.
2. Make sure the Action has correct permissions:
   - By default, GitHub Actions are granted read-only permissions. The review workflow `.github/workflows/review.yml` specifies `permissions: pull-requests: write` and `contents: read` to post comments. Ensure your repository settings allow GitHub Actions to write PR approvals/comments if you run in a locked-down organization.
3. Commit and push the `.github/workflows/review.yml` workflow along with the Python code to your repository's default branch.

---

## Customization

### Configuring the Gemini Model
By default, the Action uses `gemini-1.5-flash` for fast and cost-effective reviews. If you wish to use a more powerful model like `gemini-1.5-pro`, you can set the `GEMINI_MODEL` environment variable in the workflow file:

```yaml
      - name: Run Gemini AI Code Review
        env:
          ...
          GEMINI_MODEL: 'gemini-1.5-pro'
```

---

## Troubleshooting & FAQ

- **Why aren't my comments showing up?**
  The agent filters out comments that do not fall on line numbers modified in the Pull Request. If you are testing, ensure the changes in your C# files are on lines that trigger Gemini findings.
- **Where can I see execution logs?**
  Navigate to the **Actions** tab on your GitHub repository, click on the **AI Code Reviewer** run, and expand the **Run Gemini AI Code Review** step to review details.
