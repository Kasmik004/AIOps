import os
import token
from mcp.server.fastmcp import FastMCP
from github import Github, Path
from dotenv import load_dotenv
import subprocess
from pathlib import Path

from github_tools import create_github_issue as create_github_issue_impl

load_dotenv()  # Load environment variables from .env file

# 1. Initialize the MCP Server
# This creates a server named "GitHubHelper"
mcp = FastMCP("GitHubHelper")


# 2. Define your tool
# The decorator tells the MCP server to expose this function to the AI.
@mcp.tool()
def create_github_issue(
    repo_name: str = os.getenv("GITHUB_REPOSITORY")
    or "Kasmik004/unnecessary-agent-to-add-and-multiply",
    title: str = "Issue Test",
    body: str = "This is a test issue.",
) -> str:
    """
    Creates a new issue in a GitHub repository.

    Args:
        repo_name: The repository name in format 'username/repo', defaults to the value from the GITHUB_REPOSITORY environment variable or a fallback repository.
        title: The title of the issue, defaults to "Issue Test"
        body: The main text content of the issue, defaults to "This is a test issue."

    Returns:
        A string indicating the success or failure of the issue creation.
        Example: "Success! Created issue: https://github.com/username/repo/issues/1" or "Failed to create issue: <error message>"

    """
    return create_github_issue_impl(repo_name, title, body)


REPO_DIR = Path(
    "E:\\Self-Learning Agent\\first_steps\\first_steps"
)  # the codebase you ASK about
BRANCH = "main"  # hardcoded — never from the model


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=REPO_DIR, check=True, capture_output=True, text=True)
    return r.stdout.strip()


def check_if_repo_exists() -> bool:
    """Check if the repository exists in the specified directory."""
    return (REPO_DIR / ".git").exists()


def create_graphify_knowledge_graph():
    """Build the Graphify knowledge graph for the codebase."""
    _run(["graphify", ".", "--code-only"])
    _run(["graphify", "cluster-only", "."])
    print("Graphify knowledge graph built successfully.")
    # return f"Knowledge graph built for {sha}: {subj}"

    # _run(["git", "fetch", "origin"])
    # _run(["git", "reset", "--hard", f"origin/{BRANCH}"])
    # _run(["graphify", ".", "--update", "--no-viz", "--directed"])
    # sha = _run(["git", "rev-parse", "--short", "HEAD"])
    # subj = _run(["git", "log", "-1", "--pretty=%s"])
    # return f"Synced to {sha}: {subj} — knowledge graph rebuilt."


@mcp.tool()
def sync_codebase() -> str:
    """Pull latest from origin and rebuild the Graphify knowledge graph.
    Returns the new HEAD commit so you know what's now indexed.

    Args:
        None

    Returns:
        A string indicating the new HEAD commit and its subject line after syncing and rebuilding the knowledge graph.
        Example: "Synced to abc123: Updated README — knowledge graph rebuilt."
    """
    _run(["git", "pull", "origin", BRANCH])
    _run(["graphify", "update", "."])
    sha = _run(["git", "rev-parse", "--short", "HEAD"])
    subj = _run(["git", "log", "-1", "--pretty=%s"])
    return f"Synced to {sha}: {subj} — knowledge graph rebuilt."


# 3. Run the server
if __name__ == "__main__":
    mcp.run()
    print("GitHubHelper MCP server is running")

    if not os.environ.get("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN environment variable is missing.")
    # print(pull())
    # print(check_if_repo_exists())
    # create_graphify_knowledge_graph()
