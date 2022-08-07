from pprint import pprint
from github import Github, GithubException


class GH:
    def __init__(self, token: str) -> None:
        self.token = token
        self.github = Github(token)
        self._getRepos()

    @property
    def userName(self):
        return self.github.get_user().login

    def _getRepos(self):
        """
        Finds all public GitHub repositories (which are not forks) of authenticated user.
        """

        loginName = self.userName

        self._repos = []
        for repo in self.github.get_user().get_repos(type="public"):
            if repo.owner.login == loginName and not repo.archived and not repo.fork:
                self._repos.append(repo)

    def getRepoByShorthand(self, shorthand):
        if "/" not in shorthand:
            namespace, project = self.userName, shorthand
        else:
            namespace, project = shorthand.rsplit("/", maxsplit=1)

        projectId = "/".join([namespace, project])
        try:
            return self.github.get_repo(projectId)
        except GithubException as e:
            raise SystemExit(e)

    @property
    def repos(self):
        return self._repos

    def getRepoName(self, repo):
        return repo.name.lower()

    def repoExists(self, repoName):
        return any(self.getRepoName(repo) == repoName.lower() for repo in self.repos)

    def createRepo(self, name, description, homepage):
        """
        Creates GitHub repository based on a metadata from given GitLab repository.
        """

        self.github.get_user().create_repo(
            name,
            description=f"{description} [mirror]",
            private=False,
            has_wiki=False,
            has_projects=False,
            homepage=homepage,
        )
