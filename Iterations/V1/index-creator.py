import os
import time
import logging
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up APIs
GITHUB_API_URL = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
client = OpenAI(api_key=OPENAI_API_KEY)

def get_all_repositories(repo_type='all'):
    all_repos = []
    page = 1
    while True:
        try:
            response = requests.get(
                f"{GITHUB_API_URL}?page={page}&per_page=100&type={repo_type}",
                headers={"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
            )
            response.raise_for_status()
            repos = response.json()
            if not repos:
                break
            all_repos.extend(repos)
            page += 1
            logger.info(f"Fetched page {page-1} with {len(repos)} repositories")
            time.sleep(1)  # Simple rate limiting
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repositories: {e}")
            break
    return all_repos

def generate_index(repos):
    repo_list = "\n".join([f"- {repo['name']}: {repo['description'] or 'No description'}" for repo in repos])
    prompt = f"Generate a markdown index for the following GitHub repositories:\n\n{repo_list}\n\nPlease organize them by category and add a brief description for each category."
    
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
        logger.error(f"Error generating index: {e}")
        return None

def main():
    if not all([GITHUB_USERNAME, GITHUB_TOKEN, OPENAI_API_KEY]):
        raise ValueError("Missing required environment variables. Please check your .env file.")

    repos = get_all_repositories(repo_type='all')  # Change to 'public' or 'private' if needed
    logger.info(f"Found {len(repos)} repositories")

    index = generate_index(repos)
    if index:
        filename = "github_repo_index.md"
        with open(filename, "w") as f:
            f.write(index)
        logger.info(f"Index generated and saved to {filename}")

        # Verify file contents
        with open(filename, "r") as f:
            content = f.read()
        logger.info(f"File contents ({len(content)} characters):")
        logger.info(content[:500] + "..." if len(content) > 500 else content)
    else:
        logger.error("Failed to generate index")

if __name__ == "__main__":
    main()