import gitlab
import requests
from gitlab.exceptions import GitlabGetError
from gitlab import Gitlab


class GL:
    def __init__(self, token) -> None:
        self.token = token
        self.gitlab = Gitlab(private_token=token)
        self.gitlab.auth()
        self._getRepos()

    @property
    def userName(self):
        return self.gitlab.user.username

    def _getRepos(self):
        """
        Finds all public GitLab repositories of authenticated user.
        """
        self._repos = self.gitlab.projects.list(
            visibility="public",
            archived=False,
            owned=True,
            all=True,
        )

    @property
    def repos(self):
        return self._repos

    def findRepo(self, repoName):
        for gitlabRepo in self.repos:
            if self.getRepoName(gitlabRepo) == repoName:
                return gitlabRepo

        return None

    def getRepoName(self, repo):
        return repo.path.lower()

    def repoExists(self, repoName):
        """
        Checks if a repository with a given slug exists among the public GitLab repositories.
        """

        return any(self.getRepoName(repo) == repoName.lower() for repo in self.repos)

    def getMirrors(self, repo):
        """
        Finds all configured mirrors of GitLab repository.
        """

        return repo.remote_mirrors.list(all=True)

    def githubMirrorExists(self, mirrors, name):
        for mirror in mirrors:
            url = mirror.url
            if not url:
                continue
            if url.lower().endswith(f"github.com/{self.userName.lower()}/{name}.git"):
                return True

        return False

    def getRepoByShorthand(self, shorthand):
        if "/" not in shorthand:
            namespace, project = self.userName, shorthand
        else:
            namespace, project = shorthand.rsplit("/", maxsplit=1)

        projectId = "/".join([namespace, project])
        try:
            return self.gitlab.projects.get(id=projectId)
        except GitlabGetError as e:
            raise SystemExit(e)

    def createRepo(self, name, description):
        return self.gitlab.projects.create(
            name=name,
            description=description,
            visibility="public",
        )

    def createMirror(self, gitlabRepo, mirrorUrl):
        """Creates a pull mirror of GitHub repository"""
        self.gitlab.projects.update(
            id=gitlabRepo.id,
            mirror=True,
            import_url=mirrorUrl,
            only_mirror_protected_branches=True,
        )
