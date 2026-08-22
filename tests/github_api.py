from github import Github
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

token = os.getenv("GITHUB_TOKEN")

g = Github(token)

repo_name = (
    os.getenv("GITHUB_REPOSITORY") or "Kasmik004/unnecessary-agent-to-add-and-multiply"
)  # e.g., "username/repo"

repo = g.get_repo(repo_name)

issue_title = "Test Issue from Python"
issue_body = "This is a test issue created from a Python script. Please ignore. This also supports markdown formatting. For example, you can use **bold** or *italic* text."

new_issue = repo.create_issue(title=issue_title, body=issue_body)

print(f"Issue created: {new_issue.title} (#{new_issue.number}) {new_issue.html_url}")
