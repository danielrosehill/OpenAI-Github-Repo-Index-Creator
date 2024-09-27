import os
import time
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
GITHUB_API_URL = "https://api.github.com"
client = OpenAI(api_key=OPENAI_API_KEY)

def get_all_repositories(include_private=True):
    all_repos = []
    page = 1
    while True:
        try:
            url = f"{GITHUB_API_URL}/user/repos" if include_private else f"{GITHUB_API_URL}/users/{GITHUB_USERNAME}/repos"
            params = {
                "page": page,
                "per_page": 100,
                "type": "all" if include_private else "public"
            }
            headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            repos = response.json()
            if not repos:
                break
            
            all_repos.extend(repos)
            page += 1
            
            # Check for rate limiting
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                if remaining <= 1:
                    reset_time = int(response.headers["X-RateLimit-Reset"])
                    sleep_time = max(reset_time - time.time(), 0) + 1
                    print(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
                    time.sleep(sleep_time)
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            break
    
    return all_repos

def generate_index(repos):
    repo_list = "\n".join([f"- {repo['name']}: {repo['description'] or 'No description'} (URL: {repo['html_url']})" for repo in repos])
    prompt = f"""Generate a markdown index for the following GitHub repositories:

{repo_list}

Please group the repositories into categories.

If repositories have a similar theme, they should be grouped together under a heading. The headings should be H2s.

Organise the categories alphabetically.

Convert the repository names to make them more readable. For example, 'Prompts-And-Outputs' should be converted to 'Prompts And Outputs'.

Each repository should be a link to its GitHub URL.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates well-organized markdown indexes for GitHub repositories."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating index: {e}")
        return None

def main():
    if not all([GITHUB_USERNAME, GITHUB_TOKEN, OPENAI_API_KEY]):
        raise ValueError("Missing required environment variables. Please check your .env file.")
    
    include_private = input("Include private repositories? (y/n): ").lower() == 'y'
    repos = get_all_repositories(include_private)
    print(f"Found {len(repos)} repositories")
    
    index = generate_index(repos)
    if index:
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
    else:
        print("Failed to generate index.")

if __name__ == "__main__":
    main()