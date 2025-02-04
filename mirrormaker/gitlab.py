import requests

# GitLab user authentication token
token = ""


def get_repos():
    """
    Finds all public GitLab repositories of authenticated user.

    Returns:
     - List of public GitLab repositories.
    """

    url = (
        "https://gitlab.com/api/v4/projects?visibility=public&owned=true&archived=false"
    )
    headers = {"Authorization": f"Bearer {token}"}

    repos = []
    try:
        while url:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            repos.extend(r.json())
            # handle pagination
            url = r.links.get("next", {}).get("url", None)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return repos


def get_user():
    url = "https://gitlab.com/api/v4/user"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return r.json()


def get_repo_by_shorthand(shorthand):
    if "/" not in shorthand:
        user = get_user()["username"]
        namespace, project = user, shorthand
    else:
        namespace, project = shorthand.rsplit("/", maxsplit=1)

    project_id = requests.utils.quote("/".join([namespace, project]), safe="")

    url = f"https://gitlab.com/api/v4/projects/{project_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        print("requestin")
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return r.json()


def get_mirrors(gitlab_repo):
    """
    Finds all configured mirrors of GitLab repository.

    Args:
     - gitlab_repo: GitLab repository.

    Returns:
     - List of mirrors.
    """

    url = f'https://gitlab.com/api/v4/projects/{gitlab_repo["id"]}/remote_mirrors'
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return r.json()


def mirror_target_exists(github_repos, mirrors):
    """
    Checks if any of the given mirrors points to any of the public GitHub repositories.

    Args:
     - github_repos: List of GitHub repositories.
     - mirrors: List of mirrors configured for a single GitLab repository.

    Returns:
     - True if any of the mirror points to an existing GitHub repository, False otherwise.
    """

    for mirror in mirrors:
        if not mirror["url"]:
            continue
        if any(
            mirror["url"].lower().endswith(f'{repo["full_name"].lower()}.git')
            for repo in github_repos
        ):
            return True

    return False


def create_mirror(gitlab_repo, github_token, github_user):
    """
    Creates a push mirror of GitLab repository.

    For more details see:
    https://docs.gitlab.com/ee/user/project/repository/repository_mirroring.html#pushing-to-a-remote-repository-core

    Args:
     - gitlab_repo: GitLab repository to mirror.
     - github_token: GitHub authentication token.
     - github_user: GitHub username under whose namespace the mirror will be created (defaults to GitLab username if not provided).

    Returns:
     - JSON representation of created mirror.
    """

    url = f'https://gitlab.com/api/v4/projects/{gitlab_repo["id"]}/remote_mirrors'
    headers = {"Authorization": f"Bearer {token}"}

    # If github-user is not provided use the gitlab username
    if not github_user:
        github_user = gitlab_repo["owner"]["username"]

    data = {
        "url": f'https://{github_user}:{github_token}@github.com/{github_user}/{gitlab_repo["path"]}.git',
        "enabled": True,
    }

    try:
        r = requests.post(url, json=data, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return r.json()
