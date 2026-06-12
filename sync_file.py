import requests
import os
import argparse
import logging
import base64
from dotenv import load_dotenv
from setup_logging import setup_logging

def get_repo_details(org:str, prefix=None, path=None):
	# noinspection GrazieInspection
	"""
			Get repository names for a GitHub organization, optionally filtered by name prefix.

			Description
			- Calls the GitHub REST API to list repositories for the given organization.
			- Paginates through results (100 repos per page) until no more repos are returned.
			- Optionally filters returned repository names by the provided `prefix`.
			- Returns a list of repository names (strings).

			Important notes
			- This function expects a valid GitHub token to be available in the environment
			  variable `GH_TOKEN`. The token must have scope to read the organization's
			  repositories if they are private.
			- The function uses a simple pagination loop and stops when an empty page is
			  returned by the API.
			- On HTTP errors the function prints a single message and stops pagination,
			  returning any repositories collected before the failure. It does not raise
			  exceptions for HTTP error responses (but network exceptions from requests
			  may propagate).
			- The `path` parameter is accepted for API-compatibility but is unused here.

			Parameters
			- org (str): GitHub organization name (required).
			- prefix (str | None): If provided, only repository names that start with this
			  prefix are included in the returned list.
			- path (unused): Present for API compatibility with other functions; ignored.

			Returns
			- list[str]: List of repository names (may be empty).
		"""
	logger = logging.getLogger(__name__)
	# GitHub endpoint for listing repos under an organization
	repo_url = f"https://api.github.com/orgs/{org}/repos"

	headers = {
		"Accept": "application/vnd.github+json",
		"Authorization": f"Bearer {os.getenv('GH_TOKEN')}",
		"X-GitHub-Api-Version": "2022-11-28"
	}
	params = {
		'sort': 'created',
		'per_page': 100,
		'page': 1
	}

	all_repositories = []
	# Paginate through all pages
	while True:
		# Make the GET request with query parameters
		response = requests.get(url=repo_url, headers=headers, params=params)

		# Check the response status code
		if response.status_code == 200:
			# Parse the JSON response
			repositories = response.json()
			if not repositories:
				break
			all_repositories.extend(repositories)
			params["page"] += 1
		else:
			print(f"Failed to fetch repositories: {response.status_code}")
			break

	repo_names = []

	for repo in all_repositories:
		if prefix:
			if repo['name'].startswith(prefix):
				repo_names.append(repo['name'])
		else:
			repo_names.append(repo['name'])

	if prefix:
		logger.info(f"Found {len(repo_names)} repos in {org} with prefix {prefix}")
	else:
		logger.info(f"Found {len(repo_names)} repos in {org}")
	return repo_names


# noinspection GrazieInspection
def sync_files(org: str, repo_name: str, path: str, file: str):
	"""
	Sync files across repositories using GitHub API, preserving source directory hierarchy

	Example: path='b' and file='a' will create/update 'b/a' in the target repo.

	:param org: GitHub organization name
	:param repo_name: Name of the repository
	:param path: Local file path (directory) that should be preserved in the repo
	:param file: File name to sync
	:return: None
	"""
	logger = logging.getLogger(__name__)

	constructed_path = os.path.join(path, file)
	if not os.path.isfile(constructed_path):
		logger.error(f"File {constructed_path} does not exist. Skipping sync for repo {repo_name}.")
		raise FileNotFoundError(f"File {constructed_path} does not exist.")

	# Read the source file
	try:
		with open(constructed_path, 'r', encoding='utf-8') as f:
			file_content = f.read()
	except Exception as e:
		logger.error(f"Failed to read file {constructed_path}: {str(e)}")
		raise

	# Encode file content to base64
	encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')

	# Determine repo path to preserve directory hierarchy
	# If `path` is absolute, convert to relative path from cwd; remove leading './' or '/'
	repo_path_raw = os.path.join(path, file)
	if os.path.isabs(repo_path_raw):
		try:
			repo_path_raw = os.path.relpath(repo_path_raw, start=os.getcwd())
		except Exception:
			# fallback to file name only
			repo_path_raw = file
	# Normalize and convert to posix style for GitHub
	repo_path = os.path.normpath(repo_path_raw).replace('\\', '/')
	repo_path = repo_path.lstrip('./').lstrip('/')

	# GitHub API headers
	headers = {
		"Accept": "application/vnd.github+json",
		"Authorization": f"Bearer {os.getenv('GH_TOKEN')}",
		"X-GitHub-Api-Version": "2022-11-28"
	}

	# Check if file exists in repo to get its SHA
	get_url = f"https://api.github.com/repos/{org}/{repo_name}/contents/{repo_path}"
	sha = None

	try:
		response = requests.get(url=get_url, headers=headers)
		if response.status_code == 200:
			sha = response.json().get('sha')
			logger.info(f"File {repo_path} already exists in {repo_name}, will update.")
		elif response.status_code == 404:
			logger.info(f"File {repo_path} does not exist in {repo_name}, will create.")
		else:
			logger.error(f"Error checking file in {repo_name}: {response.status_code} - {response.text}")
			return
	except Exception as e:
		logger.error(f"Failed to check file in {repo_name}: {str(e)}")
		return

	# Prepare the update payload
	payload = {
		"message": f"Sync {repo_path} from source",
		"content": encoded_content,
		"committer": {
			"name": "File Sync Bot",
			"email": "sync@bot.local"
		}
	}

	if sha:
		payload["sha"] = sha

	# Upload/update file in repository
	try:
		response = requests.put(url=get_url, headers=headers, json=payload)
		if response.status_code in [200, 201]:
			logger.info(f"Successfully synced {repo_path} to {repo_name}")
		else:
			logger.error(f"Failed to sync {repo_path} to {repo_name}: {response.status_code} - {response.text}")
	except Exception as e:
		logger.error(f"Exception while syncing {repo_path} to {repo_name}: {str(e)}")
		raise
	

def main():
	"""
	Entry point for the CLI.

	This function:
	- Loads environment variables from a .env file (via load_dotenv()).
	- Configures logging (via setup_logging()) and obtains a logger.
	- Parses CLI arguments:
	  --organization : GitHub organization name (required)
	  --prefix       : Optional repository name prefix to filter repositories
	  --path         : Local path containing the file; preserved in the target repo (default: ".")
	  --file         : File name to sync (default: empty string)
	- Logs a compact summary of the requested operation.
	- Fetches repository names using `get_repo_details`.
	- Iterates through each repository and calls `sync_files` to create/update the file,
	  preserving the source directory hierarchy inside the target repository.

	Environment / Preconditions:
	- `GH_TOKEN` environment variable must be set to a GitHub token with repo content write
	  permissions (for private repos or write operations).
	- `setup_logging()` is expected to configure the logging subsystem.
	- `get_repo_details()` and `sync_files()` must be defined in the module.
	- The local file path (os.path.join(path, file)) must exist; otherwise `sync_files` will raise
	  FileNotFoundError and the script may fail for that repo.

	Behavior notes:
	- The `--prefix` argument filters repositories by name prefix (if provided).
	- The script logs info messages for visibility and errors via the configured logger.
	- Currently the script performs real API operations (no dry-run mode).
	- The function does not re-raise exceptions raised inside `sync_files`; they will propagate
	  unless `sync_files` handles them internally.

	Example usage:
	    python sync_file.py --organization my-org --prefix my-prefix --path b --file a

	Returns:
	- None
	"""
	load_dotenv()
	setup_logging()
	logger = logging.getLogger(__name__)

	args = argparse.ArgumentParser(description="Sync files between two directories")
	args.add_argument("--organization", help="GitHub organization name", required=True, type=str)
	args.add_argument("--prefix", help="GitHub repo prefixes to sync", required=False, type=str)
	args.add_argument("--path", help="Path to the file to replicate", required=False, default=".", type=str)
	args.add_argument("--file", help="File to sync", required=False, default="", type=str)
	args = args.parse_args()

	org = args.organization
	prefix = args.prefix
	path = args.path
	file = args.file

	logger.info(f"Starting file sync for organization: {org}")
	logger.info(f"Parameters: prefix={prefix}, path={path}, file={file}")

	# Build parameters for logging
	params = []
	if prefix:
		params.append(f"prefix: {prefix}")
	if path != ".":
		params.append(f"path: {path}")
	if file != "":
		params.append(f"file: {file}")

	# Create logging message
	msg = f"Syncing files for organization: {org}"
	if params:
		msg += " with " + ", ".join(params)
	logger.info(msg)

	repo_names = get_repo_details(org, prefix)

	for repo in repo_names:
		logger.info(f"Syncing file {file} to repo {repo}...")
		sync_files(org=org, file=file, path=path, repo_name=repo)

	logger.info("File sync completed for all repositories.")

if __name__ == "__main__":
	main()