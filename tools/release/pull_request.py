# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Tool for cherry-pick merged pull requests."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import requests


def get_single(url: str, headers: dict, param: Optional[dict] = None) -> Dict:
    """Get single response dict from HTTP requests by given condition.

    :param url: URL to requests GET method.
    :param headers: headers for HTTP requests.
    :param param:  param for HTTP requests.
    """
    resp = requests.get(url=url, headers=headers, params=param)
    if not resp.ok:
        raise ValueError("Requests error with", resp.reason)
    return json.loads(resp.content)


def get_total(url: str, headers: dict, param: Optional[dict] = None) -> List[Dict]:
    """Get all response dict from HTTP requests by given condition, change page number until no data return.

    :param url: URL to requests GET method.
    :param headers: headers for HTTP requests.
    :param param:  param for HTTP requests.
    """
    total = []
    while True:
        param["page"] = param.setdefault("page", 0) + 1
        content_dict = get_single(url, headers, param)
        data = content_dict.get("items")
        if not data:
            return total
        total.extend(data)


class PullRequest:
    """Pull request to filter the by specific condition.

    :param token: token to request GitHub API entrypoint.
    """

    def __init__(self, token: str, repo: Optional[str] = "apache/dolphinscheduler"):
        self.token = token
        self.repo = repo
        self.url_search = "https://api.github.com/search/issues"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {token}",
        }

    def all_merged_detail(
        self, milestone: str, order: Optional[bool] = True
    ) -> List[Tuple]:
        """Get all merged pull detail, including issue number, SHA, merge time by specific milestone.

        :param milestone: query by specific milestone.
        :param order: Whether sorting according the merged time.
        """
        detail = []
        numbers = self.all_merged_number(milestone)
        for number in numbers:
            url_pr = f"https://api.github.com/repos/{self.repo}/pulls/{number}"
            pr_dict = get_single(url=url_pr, headers=self.headers)
            sha = pr_dict.get("merge_commit_sha")
            merged_at = datetime.strptime(
                pr_dict.get("merged_at"), "%Y-%m-%dT%H:%M:%SZ"
            )
            detail.append((number, sha, merged_at))
        if order:
            detail.sort(key=lambda i: i[2])
        return detail

    def all_merged_number(self, milestone: str) -> Set[Dict]:
        """Get all merged pull request by specific milestone.

        :param milestone: query by specific milestone.
        """
        from_pr = self._pr_by_milestone(milestone=milestone)
        from_issue = self._pr_by_issue_milestone(milestone=milestone)
        from_pr |= from_issue
        return from_pr

    def _pr_by_milestone(self, milestone: str) -> Set[Dict]:
        """Get merged pull request number by its associated milestone.

        :param milestone: query by specific milestone.
        """
        params = {"q": f"repo:{self.repo} is:pr is:merged milestone:{milestone}"}
        prs = get_total(url=self.url_search, headers=self.headers, param=params)
        return {pr.get("number") for pr in prs}

    def _pr_by_issue_milestone(self, milestone: str) -> Set[Dict]:
        """Get merged pull request number by its associated issue's milestone.

        :param milestone: query by specific milestone.
        """
        params = {"q": f"repo:{self.repo} is:issue is:closed milestone:{milestone}"}
        issues = get_total(url=self.url_search, headers=self.headers, param=params)

        issue_prs = set()
        # Get issue related PR
        for issue in issues:
            # TODO: currently I can only find timeline to get ref PR from issue
            url_issue_timeline = (
                f"https://api.github.com/repos/{self.repo}/issues"
                f"/{issue.get('number')}/timeline"
            )

            timeline_dict = get_single(url=url_issue_timeline, headers=self.headers)
            for timeline in timeline_dict:
                if (
                    timeline.get("event") == "cross-referenced"
                    and timeline.get("source").get("type") == "issue"
                    and "pull_request" in timeline.get("source").get("issue")
                    and timeline.get("source")
                    .get("issue")
                    .get("pull_request")
                    .get("merged_at")
                    is not None
                ):
                    pr_number = timeline.get("source").get("issue").get("number")
                    issue_prs.add(pr_number)

        return issue_prs


if __name__ == "__main__":
    access_token = os.environ.get("GH_ACCESS_TOKEN")
    milestone = os.environ.get("GH_REPO_MILESTONE")
    pr = PullRequest(token=access_token)
    merged_pr = pr.all_merged_detail(milestone)
    for mpr in merged_pr:
        print(f"git cherry-pick -x {mpr[1]}")
