#!/usr/bin/env python3

import click
from tabulate import tabulate
import glab
import ghub

gh: ghub.GH = None
gl: glab.GL = None


@click.command(context_settings={"auto_envvar_prefix": "MIRRORMAKER"})
@click.option("--github-token", required=True, help="GitHub authentication token")
@click.option("--gitlab-token", required=True, help="GitLab authentication token")
@click.option(
    "--github-user",
    help="GitHub username. If not provided, your GitLab username will be used by default.",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="If enabled, a summary will be printed and no mirrors will be created.",
)
@click.argument("repo", required=False)
def mirrormaker(github_token, gitlab_token, github_user, dry_run, repo=None):
    """
    Set up mirroring of repositories from GitLab to GitHub.

    By default, mirrors for all repositories owned by the user will be set up.

    If the REPO argument is given, a mirror will be set up for that repository
    only. REPO can be either a simple project name ("myproject"), in which case
    its namespace is assumed to be the current user, or the path of a project
    under a specific namespace ("mynamespace/myproject").
    """
    global gh, gl
    gh = ghub.GH(github_token)
    gl = glab.GL(gitlab_token)

    if repo:
        githubRepos = [gh.getRepoByShorthand(repo)]
    else:
        click.echo("Getting your public GitHub repositories")
        githubRepos = gh.repos
        if not githubRepos:
            click.echo("There are no public repositories in your GitHub account.")
            return

    click.echo("Getting your public GitLab repositories")
    gitlabRepos = gl.repos

    actions = findActionsToPerform(gitlabRepos, githubRepos)

    printSummaryTable(actions)

    if dry_run:
        click.echo(
            "Run without the --dry-run flag to create missing repositories and mirrors."
        )
        return
    performActions(actions)

    click.echo("Done!")


def findActionsToPerform(gitlabRepos, githubRepos):
    """
    Goes over provided repositories and figure out what needs to be done to create missing mirrors.

    Args:
     - gitlab_repos: List of GitLab repositories.
     - github_repos: List of GitHub repositories.

    Returns:
     - actions: List of actions necessary to perform on a GitLab repo to create a mirror
                eg: {'gitlab_repo: '', 'create_github': True, 'create_mirror': True}
    """

    actions = []

    with click.progressbar(
        githubRepos, label="Checking GitHub mirrors' status", show_eta=False
    ) as bar:
        for githubRepo in bar:
            action = checkGhubMirrorStatus(githubRepo, gitlabRepos)
            actions.append(action)

    return actions


def checkGhubMirrorStatus(githubRepo, gitlabRepos):
    """
    Checks if given GitHub repository has a mirror created among the given GitLab repositories.

    Args:
     - github_repo: GitHub repository.
     - gitlab_repos: List of GitLab repositories.

    Returns:
     - action: Action necessary to perform
    """
    global gh, gl

    action = {
        "github_repo": githubRepo,
        "gitlab_repo": None,
        "create_gitlab": True,
        "create_mirror": True,
    }

    gitHubRepoName = gh.getRepoName(githubRepo)
    gitlabRepo = gl.findRepo(gitHubRepoName)
    action["gitlab_repo"] = gitlabRepo

    if gitlabRepo:
        action["create_gitlab"] = False
        mirrors = gl.getMirrors(gitlabRepo)
        if gl.githubMirrorExists(mirrors, gitHubRepoName):
            action["create_mirror"] = False

    return action


def printSummaryTable(actions):
    """Prints a table summarizing whether mirrors are already created or missing"""
    global gh

    click.echo("Your mirrors status summary:\n")

    created = click.style("\u2714 created", fg="green")
    missing = click.style("\u2718 missing", fg="red")

    headers = ["GitHub repo", "GitLab repo", "Mirror"]
    summary = []

    for action in actions:
        row = [gh.getRepoName(action["github_repo"])]
        row.append(missing if action["create_gitlab"] else created)
        row.append(missing if action["create_mirror"] else created)
        summary.append(row)

    summary.sort()

    click.echo(tabulate(summary, headers) + "\n")


def performActions(actions):
    """Creates GitLab repositories and mirrors where necessary"""
    global gh, gl

    with click.progressbar(actions, label="Creating mirrors", show_eta=False) as bar:
        for action in bar:
            githubRepo = action["github_repo"]
            githubRepoName = gh.getRepoName(githubRepo)
            if action["create_gitlab"]:
                action["gitlab_repo"] = gl.createRepo(
                    githubRepoName,
                    (
                        githubRepo.description
                        if githubRepo.description
                        else githubRepoName
                    )
                    + " [mirror]",
                )
            if action["create_mirror"]:
                gl.createMirror(
                    action["gitlab_repo"],
                    f"https://{gh.userName}:{gh.token}@github.com/{gh.userName}/{githubRepoName}.git",
                )


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter, unexpected-keyword-arg
    mirrormaker()
