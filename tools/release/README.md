# Tools Release

A tools for convenient release DolphinScheduler.

## Prepare

* python: python 3.6 or above
* pip: latest version of pip is better

To install dependence, you should run command

```shell
pip install -r requirements.txt
```

## Pull Requests

This tool find merged pull request with specific milestone, and print the `git cherry-pick -x [SHA]` in the end. You can run below command to do that

```shell
export GH_ACCESS_TOKEN="<YOUR-GITHUB-TOKEN-WITH-REPO-ACCESS>"
export GH_REPO_MILESTONE="<YOUR-MILESTONE>"
python pull_request.py
```
