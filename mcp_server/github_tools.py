from github import Github
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

token = os.getenv("GITHUB_TOKEN")

g = Github(token)


def create_github_issue(
    repo_name: str,
    title: str,
    body: str,
) -> str:
    """
    Creates a new issue in a GitHub repository.

    Args:
        repo_name: The repository name in format 'username/repo'
        title: The title of the issue
        body: The main text content of the issue
    """
    try:
        # Authenticate and create the issue
        repo = g.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body)

        return f"Success! Created issue: {issue.html_url}"
    except Exception as e:
        print(f"Failed to create issue: {str(e)}")
        return f"Failed to create issue: {str(e)}"
