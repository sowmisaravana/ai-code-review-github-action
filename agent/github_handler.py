import os
import logging
from typing import Dict, List, Optional, Set, Tuple
from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Commit import Commit

# Configure logging
logger = logging.getLogger("CodeReviewer.GithubHandler")

class GithubHandler:
    """Handles interaction with the GitHub API for retrieving PR data and posting reviews."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is not set.")
        
        # Initialize GitHub client
        self.github = Github(self.token)

    def get_pull_request(self, repository_name: str, pr_number: int) -> PullRequest:
        """Fetches the PullRequest object for the given repository and PR number."""
        try:
            logger.info(f"Connecting to repository: {repository_name}, PR: {pr_number}")
            repo = self.github.get_repo(repository_name)
            return repo.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Failed to fetch PR #{pr_number} from {repository_name}: {str(e)}")
            raise e

    @staticmethod
    def parse_changed_lines(patch: Optional[str]) -> Set[int]:
        """
        Parses a unified diff patch to identify the lines that were added or modified
        in the pull request (new version of the file).
        """
        changed_lines = set()
        if not patch:
            return changed_lines

        current_line = 0
        for line in patch.splitlines():
            if line.startswith("@@"):
                # Parse header, e.g., @@ -10,6 +10,7 @@
                # We want the "+10,7" part (added/modified lines in the new file)
                parts = line.split(" ")
                if len(parts) >= 3:
                    new_file_info = parts[2]  # e.g., "+10,7" or "+10"
                    if new_file_info.startswith("+"):
                        new_file_info = new_file_info[1:]
                    if "," in new_file_info:
                        current_line = int(new_file_info.split(",")[0])
                    else:
                        current_line = int(new_file_info)
            elif line.startswith("+") and not line.startswith("+++"):
                # Line added or modified in the target PR
                changed_lines.add(current_line)
                current_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                # Line deleted, doesn't exist in the target (new) file
                pass
            else:
                # Unchanged context line
                current_line += 1

        return changed_lines

    def fetch_pr_files(self, pr: PullRequest) -> List[Tuple[str, str, Set[int]]]:
        """
        Retrieves all C# files changed in the PR, their contents, and the sets of changed lines.
        Returns a list of tuples: (filename, content, set_of_changed_lines)
        """
        changed_files = []
        
        try:
            files = pr.get_files()
            for file in files:
                # Ignore deleted files and non-C# files
                if file.status == "removed":
                    logger.info(f"Skipping deleted file: {file.filename}")
                    continue
                if not file.filename.endswith(".cs"):
                    continue

                logger.info(f"Processing changed file: {file.filename} (status: {file.status})")
                
                # Extract the lines that were actually changed in this PR
                changed_lines = self.parse_changed_lines(file.patch)
                
                # Fetch file contents
                content = None
                
                # 1. Attempt to read from the local workspace (action runner workspace)
                if os.path.exists(file.filename):
                    try:
                        with open(file.filename, "r", encoding="utf-8") as f:
                            content = f.read()
                        logger.info(f"Read {file.filename} from local workspace.")
                    except Exception as ex:
                        logger.warning(f"Could not read local file {file.filename}: {str(ex)}. Falling back to API.")

                # 2. Fallback to fetching via GitHub API if not available locally
                if content is None:
                    try:
                        repo = pr.base.repo
                        content_file = repo.get_contents(file.filename, ref=pr.head.sha)
                        content = content_file.decoded_content.decode("utf-8")
                        logger.info(f"Fetched {file.filename} content via GitHub API.")
                    except Exception as ex:
                        logger.error(f"Failed to fetch {file.filename} from GitHub API: {str(ex)}")
                        continue

                changed_files.append((file.filename, content, changed_lines))
                
        except GithubException as e:
            logger.error(f"Error fetching PR files: {str(e)}")
            raise e

        return changed_files

    def post_pr_review(
        self, 
        pr: PullRequest, 
        comments: List[Dict[str, any]], 
        summary_body: str
    ) -> None:
        """
        Submits a single Pull Request Review with line-level comments.
        If comments is empty, it posts a generic summary review or just logs.
        """
        try:
            # Get latest commit
            commits = list(pr.get_commits())
            if not commits:
                logger.error("No commits found in Pull Request. Cannot post review.")
                return
            latest_commit = commits[-1]
            
            event = "COMMENT"
            if comments:
                event = "REQUEST_CHANGES"
                logger.info(f"Submitting Pull Request Review (REQUEST_CHANGES) with {len(comments)} comments.")
            else:
                logger.info("Submitting Pull Request Review (APPROVE/COMMENT) with 0 comments.")
                event = "APPROVE"

            # In PyGithub, create_review takes:
            # commit: Commit object or SHA
            # body: Summary markdown
            # event: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
            # comments: list of dicts with keys 'path', 'line', 'body'
            pr.create_review(
                commit=latest_commit,
                body=summary_body,
                event=event,
                comments=comments
            )
            logger.info("Successfully posted review to GitHub.")
            
        except GithubException as e:
            logger.error(f"Failed to post Pull Request Review: {str(e)}")
            
            # Fallback: post a single top-level review comment if line-level draft posting fails
            try:
                logger.warning("Attempting fallback to post a single top-level comment...")
                pr.create_issue_comment(
                    f"### AI Code Review Summary\n\n"
                    f"There was an error posting inline comments, but here is the summary:\n\n"
                    f"{summary_body}"
                )
                logger.info("Successfully posted fallback top-level comment.")
            except Exception as ex:
                logger.error(f"Fallback comment posting also failed: {str(ex)}")
                raise e
