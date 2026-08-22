import os
from mcp.server.fastmcp import FastMCP
from github import Github
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# 1. Initialize the MCP Server
# This creates a server named "GitHubHelper"
mcp = FastMCP("GitHubHelper")


# 2. Define your tool
# The decorator tells the MCP server to expose this function to the AI.
@mcp.tool()
def create_github_issue(repo_name: str, title: str, body: str) -> str:
    """
    Creates a new issue in a GitHub repository.

    Args:
        repo_name: The repository name in format 'username/repo'
        title: The title of the issue
        body: The main text content of the issue
    """
    # We use an environment variable so the token isn't hardcoded
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable is missing."

    try:
        # Authenticate and create the issue
        g = Github(token)
        repo = g.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body)

        return f"Success! Created issue: {issue.html_url}"
    except Exception as e:
        return f"Failed to create issue: {str(e)}"


# 3. Run the server
if __name__ == "__main__":
    print("Starting the FastMCP server...")
    print("GitHub Token:", os.environ.get("GITHUB_TOKEN"))
    mcp.run()
