import os
import token
from mcp.server.fastmcp import FastMCP
from github import Github
from dotenv import load_dotenv

from github_tools import create_github_issue as create_github_issue_impl

load_dotenv()  # Load environment variables from .env file

# 1. Initialize the MCP Server
# This creates a server named "GitHubHelper"
mcp = FastMCP("GitHubHelper")


# 2. Define your tool
# The decorator tells the MCP server to expose this function to the AI.
@mcp.tool()
def create_github_issue(
    repo_name: str = os.getenv("GITHUB_REPOSITORY"),
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


# 3. Run the server
if __name__ == "__main__":
    mcp.run()

    if not os.environ.get("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN environment variable is missing.")
