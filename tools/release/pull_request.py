import requests
import json
import os
from typing import Dict, List, Set, Optional


def get_single(url: str, headers: dict, param: Optional[dict] = None) -> requests.Response:
    resp = requests.get(url=url, headers=headers, params=param)
    if not resp.ok:
        raise ValueError("Requests error with", resp.reason)
    return resp


def get_total(url: str, headers: dict, param: Optional[dict] = None) -> List[Dict]:
    total = []
    while True:
        param["page"] = param.setdefault("page", 0) + 1
        resp = get_single(url, headers, param)
        data = json.loads(resp.content).get("items")
        if not data:
            return total
        total.extend(data)


class PR:
    """Pull request to filter the by specific condition

    :param token: token to request GitHub API entrypoint.
    """

    def __init__(self, token: str, repo: Optional[str] = "apache/dolphinscheduler"):
        self.token = token
        self.repo = repo
        self.url = "https://api.github.com/search/issues"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {token}",
        }

    def all_merged(self, milestone: str) -> Set[Dict]:
        """Get all merged pull request by specific milestone.

        :param milestone: query by specific milestone.
        """
        from_pr = self._pr_by_milestone(milestone=milestone)
        from_issue = self._pr_by_issue_milestone(milestone=milestone)
        from_pr |= from_issue
        return from_pr

    def _pr_by_milestone(self, milestone: str) -> Set[Dict]:
        """Get merged pull request by its associated milestone.

        :param milestone: query by specific milestone.
        """
        params = {
            "q": f"repo:{self.repo} "
                 "is:pr "
                 "is:merged "
                 f"milestone:{milestone}"
        }
        prs = get_total(url=self.url, headers=self.headers, param=params)
        return {pr.get("html_url") for pr in prs}

    def _pr_by_issue_milestone(self, milestone: str) -> Set[Dict]:
        """Get merged pull request by its associated issue's milestone.

        :param milestone: query by specific milestone.
        """
        params = {
            "q": f"repo:{self.repo} "
                 "is:issue "
                 "is:closed "
                 f"milestone:{milestone}"
        }
        issues = get_total(url=self.url, headers=self.headers, param=params)

        issue_prs = set()
        # Get issue related PR
        for issue in issues:
            url_issue_detail = f"https://api.github.com/repos/{self.repo}/issues/{issue.get('number')}"
            issue_detail = get_single(url=url_issue_detail, headers=self.headers)
            associate_pr = json.loads(issue_detail.content).get("pull_request").get("html_url")
            issue_prs.add(associate_pr)

        return issue_prs


if __name__ == "__main__":
    # TODO remove this config
    access_token = os.environ.get("GH_ACCESS_TOKEN") or "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"
    milestone = os.environ.get("GH_REPO_MILESTONE") or "3.0.1"
    pr = PR(token=access_token)
    merged_pr = pr.all_merged(milestone)
    print(merged_pr)
