import os
import sys
import json
import argparse
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load modules
from github_handler import GithubHandler
from gemini_client import GeminiCodeReviewer
from formatter import format_comment_body, format_review_summary

# Configure logging to stdout for GitHub Action logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CodeReviewer.Orchestrator")

def parse_args():
    parser = argparse.ArgumentParser(description="AI Code Reviewer Agent using Gemini")
    parser.add_argument("--dry-run", action="store_true", help="Print findings to stdout without posting to GitHub")
    return parser.parse_args()

def get_pr_number() -> int:
    """Retrieves the PR number from environment variables or event payload."""
    pr_num_env = os.getenv("GITHUB_PR_NUMBER")
    if pr_num_env:
        try:
            return int(pr_num_env)
        except ValueError:
            logger.warning(f"Invalid GITHUB_PR_NUMBER: {pr_num_env}. Trying event payload.")
            
    # Try parsing GITHUB_EVENT_PATH
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, "r", encoding="utf-8") as f:
                event_data = json.load(f)
            if "pull_request" in event_data:
                pr_num = event_data["pull_request"].get("number")
                if pr_num:
                    return int(pr_num)
            elif "number" in event_data:
                return int(event_data["number"])
        except Exception as e:
            logger.error(f"Error parsing GitHub event file: {str(e)}")
            
    raise ValueError("Pull Request number could not be determined. Please set GITHUB_PR_NUMBER.")

def main():
    # Load .env file for local development
    load_dotenv()
    
    args = parse_args()
    
    logger.info("Starting AI C# Code Reviewer Orchestrator...")
    
    # Validate environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    repository = os.getenv("GITHUB_REPOSITORY")
    
    if not gemini_key:
        logger.error("GEMINI_API_KEY is not set.")
        sys.exit(1)
        
    if not github_token and not args.dry_run:
        logger.error("GITHUB_TOKEN is not set and --dry_run is not enabled.")
        sys.exit(1)
        
    if not repository and not args.dry_run:
        logger.error("GITHUB_REPOSITORY is not set and --dry_run is not enabled.")
        sys.exit(1)

    # Resolve PR number
    pr_number = None
    if not args.dry_run:
        try:
            pr_number = get_pr_number()
            logger.info(f"Review target repository: {repository}, PR: {pr_number}")
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
            
    # Initialize clients
    try:
        reviewer = GeminiCodeReviewer(api_key=gemini_key)
        github_handler = None if args.dry_run else GithubHandler(token=github_token)
    except Exception as e:
        logger.error(f"Failed to initialize clients: {str(e)}")
        sys.exit(1)

    # 1. Fetch changed files and their code content
    changed_files_data = []
    
    if args.dry_run:
        logger.info("Dry_run mode: Looking for C# files locally in workspace...")
        # Local search for C# files to test locally
        for root, _, files in os.walk("."):
            # Skip virtual environments and hidden directories
            if any(part in root.split(os.sep) for part in [".venv", "venv", ".git", ".github"]):
                continue
            for file in files:
                if file.endswith(".cs"):
                    file_path = os.path.join(root, file).replace("\\", "/")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        # For dry run, we treat all lines in the file as changed
                        changed_files_data.append((file_path, content, set()))
                        logger.info(f"Found local C# file for review: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to read local file {file_path}: {str(e)}")
        if not changed_files_data:
            logger.warning("No C# files found in local directory. Add some .cs files to test.")
    else:
        # Fetch from GitHub
        try:
            pr = github_handler.get_pull_request(repository, pr_number)
            changed_files_data = github_handler.fetch_pr_files(pr)
        except Exception as e:
            logger.error(f"Failed to fetch PR details from GitHub: {str(e)}")
            sys.exit(1)

    # Filter out empty files or unsupported statuses
    if not changed_files_data:
        logger.info("No C# files modified in this PR. Skipping analysis.")
        sys.exit(0)

    logger.info(f"Found {len(changed_files_data)} C# files to review.")
    
    all_findings: List[Dict[str, Any]] = []
    pr_comments: List[Dict[str, Any]] = []

    # 2. Review each C# file
    for filename, content, changed_lines in changed_files_data:
        logger.info(f"Running AI analysis on {filename}...")
        try:
            result = reviewer.analyze_file(filename, content)
            findings = result.get("findings", [])
            logger.info(f"Gemini analysis returned {len(findings)} findings for {filename}.")
            
            for finding in findings:
                # Add file path context if missing
                finding["file"] = filename
                all_findings.append(finding)
                
                line = finding.get("line")
                
                # In dry-run, we keep all findings regardless of line modifications.
                # In standard PR review, we only post inline comments on lines modified/added in the PR.
                if args.dry_run:
                    pr_comments.append({
                        "path": filename,
                        "line": line,
                        "body": format_comment_body(finding)
                    })
                else:
                    if line in changed_lines:
                        pr_comments.append({
                            "path": filename,
                            "line": line,
                            "body": format_comment_body(finding)
                        })
                        logger.info(f"Match: keeping finding on line {line} for {filename}.")
                    else:
                        logger.info(
                            f"Filtered: skipping finding on line {line} for {filename} (not in PR changed lines)."
                        )
                        
        except Exception as e:
            logger.error(f"Error reviewing file {filename}: {str(e)}")
            # Continue reviewing other files even if one fails

    # 3. Format and submit results
    summary_markdown = format_review_summary(all_findings, len(changed_files_data))
    
    if args.dry_run:
        logger.info("\n=== DRY RUN REVIEW SUMMARY ===")
        print(summary_markdown)
        logger.info("\n=== DRY RUN INLINE COMMENTS ===")
        for comment in pr_comments:
            print(f"\nFile: {comment['path']}, Line: {comment['line']}")
            print(comment["body"])
            print("-" * 40)
    else:
        try:
            pr = github_handler.get_pull_request(repository, pr_number)
            github_handler.post_pr_review(
                pr=pr, 
                comments=pr_comments, 
                summary_body=summary_markdown
            )
            logger.info("AI review completed and posted to GitHub.")
        except Exception as e:
            logger.error(f"Failed to post AI review: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
