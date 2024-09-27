import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up APIs
GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
client = OpenAI(api_key=OPENAI_API_KEY)

def get_all_repositories():
    all_repos = []
    page = 1
    while True:
        response = requests.get(
            f"{GITHUB_API_URL}?page={page}&per_page=100",
            headers={"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        )
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repositories: {response.status_code}")
        repos = response.json()
        if not repos:
            break
        all_repos.extend(repos)
        page += 1
    return all_repos

def generate_index(repos):
    repo_list = "\n".join([f"- {repo['name']}: {repo['description'] or 'No description'} (URL: {repo['html_url']})" for repo in repos])
    prompt = f"""Generate a markdown index for the following GitHub repositories:

{repo_list}

Please group the repositories into categories. If repositories have a similar theme, they should be grouped together. Under a heading. The headings should be H2s.
Additionally, convert the repository names to make them more readable. For example, 'Prompts-And-Outputs' should be converted to 'Prompts And Outputs'.
Each repository should be a link to its GitHub URL.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates well-organized markdown indexes for GitHub repositories."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def main():
    if not all([GITHUB_USERNAME, GITHUB_TOKEN, OPENAI_API_KEY]):
        raise ValueError("Missing required environment variables. Please check your .env file.")

    repos = get_all_repositories()
    print(f"Found {len(repos)} repositories")

    index = generate_index(repos)

    # Create ../Output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Output")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, "github_repo_index.md")
    with open(filename, "w") as f:
        f.write(index)
    print(f"Index generated and saved to {filename}")

    # Verify file contents
    with open(filename, "r") as f:
        content = f.read()
    print(f"File contents ({len(content)} characters):")
    print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    main()