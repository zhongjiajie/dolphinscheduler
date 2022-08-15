import requests
import json
from typing import Dict, List

def get_total(url: str, headers: dict, param: dict) -> List[Dict]:
    total = []
    while True:
        param["page"] = param.setdefault("page", 0) + 1
        resp = requests.get(url=url, headers=headers, params=param)
        data = json.loads(resp.content).get("items")
        if not data:
            return total
        total.extend(data)

def pr_by_milestone(token: str):
    url = "https://api.github.com/search/issues"
    params = {
        "q": "repo:apache/dolphinscheduler is:pr is:merged milestone:3.0.1"
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {token}",
    }
    total = get_total(url=url, headers=headers, param=params)
    print(len(total))


def pr_by_issue_milestone(token: str):
    url = "https://api.github.com/search/issues"
    params = {
        "q": "repo:apache/dolphinscheduler is:issue milestone:3.0.1"
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {token}",
    }
    total = get_total(url=url, headers=headers, param=params)
    print(len(total))


if __name__ == "__main__":
    access_token = "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"
    pr_by_milestone(token=access_token)
    pr_by_issue_milestone(token=access_token)

