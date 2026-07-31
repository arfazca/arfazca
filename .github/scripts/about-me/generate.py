#!/usr/bin/env python3
"""
Populates the dynamic fields (Uptime + GitHub Stats) in about-dark.svg /
about-light.svg using the GitHub GraphQL API, then writes the populated
files back out for the workflow to push to the `generated` branch.

Structure/technique adapted from Andrew Grant's
https://github.com/Andrew6rant/Andrew6rant today.py (MIT-style personal
profile generator pattern) - trimmed to just what this card needs: no
per-user archive of deleted repos, single owner instead of multi-account.
"""
import datetime
import hashlib
import os
import shutil
import time

import requests
from dateutil import relativedelta
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "cache")

HEADERS = {"authorization": "token " + os.environ["ACCESS_TOKEN"]}
USER_NAME = os.environ.get("USER_NAME", "arfazca")
BIRTHDAY = datetime.datetime(2002, 6, 15)

RETRYABLE_STATUSES = {502, 503, 504}
MAX_RETRIES = 5


def graphql_post(query, variables):
    """POST to the GraphQL API, retrying transient 502/503/504s with backoff.

    GitHub's GraphQL backend returns these under load on large commit-history
    walks (documented upstream in Andrew6rant/Andrew6rant's today.py) - not a
    logic error, just needs a retry.
    """
    last = None
    for attempt in range(MAX_RETRIES):
        r = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=HEADERS,
        )
        if r.status_code == 200:
            return r
        last = r
        if r.status_code not in RETRYABLE_STATUSES or attempt == MAX_RETRIES - 1:
            break
        sleep_for = 5 * (2**attempt)
        print(f"GraphQL {r.status_code}, retrying in {sleep_for}s (attempt {attempt + 1}/{MAX_RETRIES})")
        time.sleep(sleep_for)
    return last


def simple_request(name, query, variables):
    r = graphql_post(query, variables)
    if r.status_code == 200:
        return r
    raise Exception(name, "failed", r.status_code, r.text)


def uptime_string():
    diff = relativedelta.relativedelta(datetime.datetime.today(), BIRTHDAY)
    def plural(n):
        return "s" if n != 1 else ""
    return "{} year{}, {} month{}, {} day{}".format(
        diff.years, plural(diff.years),
        diff.months, plural(diff.months),
        diff.days, plural(diff.days),
    )


def user_getter(username):
    query = """
    query($login: String!){
        user(login: $login) { id }
    }"""
    r = simple_request("user_getter", query, {"login": username})
    return r.json()["data"]["user"]["id"]


def repos_and_stars(owner_affiliation, cursor=None, stars=0, count=0):
    query = """
    query ($aff: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $aff) {
                totalCount
                edges { node { ... on Repository { nameWithOwner stargazers { totalCount } } } }
                pageInfo { endCursor hasNextPage }
            }
        }
    }"""
    r = simple_request(
        "repos_and_stars", query, {"aff": owner_affiliation, "login": USER_NAME, "cursor": cursor}
    )
    data = r.json()["data"]["user"]["repositories"]
    total = data["totalCount"]
    for e in data["edges"]:
        node = e.get("node") or {}
        stargazers = node.get("stargazers") or {}
        stars += stargazers.get("totalCount", 0)
    count = total
    if data["pageInfo"]["hasNextPage"]:
        return repos_and_stars(owner_affiliation, data["pageInfo"]["endCursor"], stars, count)
    return count, stars


def repo_edges_for_loc(owner_affiliation, cursor=None, edges=None):
    edges = edges or []
    query = """
    query ($aff: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 60, after: $cursor, ownerAffiliations: $aff) {
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            defaultBranchRef { target { ... on Commit { history { totalCount } } } }
                        }
                    }
                }
                pageInfo { endCursor hasNextPage }
            }
        }
    }"""
    r = simple_request(
        "repo_edges_for_loc", query, {"aff": owner_affiliation, "login": USER_NAME, "cursor": cursor}
    )
    data = r.json()["data"]["user"]["repositories"]
    edges += data["edges"]
    if data["pageInfo"]["hasNextPage"]:
        return repo_edges_for_loc(owner_affiliation, data["pageInfo"]["endCursor"], edges)
    return edges


def recursive_loc(owner, repo_name, owner_id, addition_total=0, deletion_total=0, my_commits=0, cursor=None):
    query = """
    query ($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            edges {
                                node { ... on Commit { additions deletions } author { user { id } } }
                            }
                            pageInfo { endCursor hasNextPage }
                        }
                    }
                }
            }
        }
    }"""
    r = graphql_post(query, {"repo_name": repo_name, "owner": owner, "cursor": cursor})
    if r.status_code != 200:
        if r.status_code == 403:
            raise Exception("Secondary rate limit hit while walking commit history")
        raise Exception("recursive_loc failed", r.status_code, r.text)
    branch = r.json()["data"]["repository"]["defaultBranchRef"]
    if branch is None:
        return 0, 0, 0
    history = branch["target"]["history"]
    for node in history["edges"]:
        author = node["node"]["author"] or {}
        if author.get("user") == owner_id:
            my_commits += 1
            addition_total += node["node"]["additions"]
            deletion_total += node["node"]["deletions"]
    if not history["edges"] or not history["pageInfo"]["hasNextPage"]:
        return addition_total, deletion_total, my_commits
    return recursive_loc(
        owner, repo_name, owner_id, addition_total, deletion_total, my_commits, history["pageInfo"]["endCursor"]
    )


def cached_loc_and_commits(owner_id):
    """
    Walks every owned/collaborator/org-member repo, caching per-repo commit
    totals + LOC in cache/<sha256(username)>.txt so re-runs only re-walk
    repos whose commit count has changed. Mirrors Andrew6rant's cache_builder.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    raw_edges = repo_edges_for_loc(["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"])
    edges = [e for e in raw_edges if e.get("node")]  # drop repos the token can't see fully
    filename = os.path.join(CACHE_DIR, hashlib.sha256(USER_NAME.encode()).hexdigest() + ".txt")

    try:
        with open(filename) as f:
            cached_lines = f.readlines()
    except FileNotFoundError:
        cached_lines = []

    cache = {}
    for line in cached_lines:
        parts = line.split()
        if len(parts) == 5:
            cache[parts[0]] = parts[1:]

    # Per-repo cache hits are keyed by hash + remote commit count below, so a
    # changed repo list (additions/deletions) doesn't need to invalidate
    # everything - this also makes the partial-flush-on-crash below useful,
    # since a re-run can pick up exactly where it left off.

    def flush(lines):
        with open(filename, "w") as f:
            f.writelines(lines)

    loc_add = loc_del = total_commits = 0
    new_lines = []
    for e in edges:
        node = e["node"]
        name = node["nameWithOwner"]
        h = hashlib.sha256(name.encode()).hexdigest()
        branch_ref = node["defaultBranchRef"]
        target = (branch_ref or {}).get("target") or {}
        history = target.get("history")
        remote_commit_count = history["totalCount"] if history else 0

        if h in cache and int(cache[h][0]) == remote_commit_count:
            commit_count, my_commits, add, dele = cache[h]
        else:
            owner, repo_name = name.split("/", 1)
            try:
                add, dele, my_commits = recursive_loc(owner, repo_name, owner_id) if history else (0, 0, 0)
            except Exception:
                flush(new_lines)  # save whatever we already walked before re-raising
                raise
            commit_count = remote_commit_count

        new_lines.append(f"{h} {commit_count} {my_commits} {add} {dele}\n")
        flush(new_lines)  # cheap at this repo count, and survives a hard kill/timeout
        loc_add += int(add)
        loc_del += int(dele)
        total_commits += int(my_commits)

    return loc_add, loc_del, total_commits


def find_and_replace(root, element_id, new_text):
    el = root.find(f".//*[@id='{element_id}']")
    if el is not None:
        el.text = new_text


def set_value(root, element_id, new_text):
    if isinstance(new_text, int):
        new_text = "{:,}".format(new_text)
    find_and_replace(root, element_id, str(new_text))


def overwrite(path, values):
    # Dot-leader lengths are baked into the template by build_svg.py, sized
    # from each row's key so every row's value starts in the same column
    # regardless of how long the live value is - nothing to recompute here.
    tree = etree.parse(path)
    root = tree.getroot()
    set_value(root, "age_data", values["age"])
    set_value(root, "repo_data", values["repos"])
    set_value(root, "contrib_data", values["contrib_repos"])
    set_value(root, "star_data", values["stars"])
    set_value(root, "commit_data", values["commits"])
    set_value(root, "loc_data", values["loc_total"])
    set_value(root, "loc_add", values["loc_add"])
    set_value(root, "loc_del", values["loc_del"])
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main():
    owner_id = {"id": user_getter(USER_NAME)}
    age = uptime_string()
    repos, stars = repos_and_stars(["OWNER"])
    _, contrib_repos = repos_and_stars(["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"])
    loc_add, loc_del, commits = cached_loc_and_commits(owner_id)

    values = {
        "age": age,
        "repos": repos,
        "contrib_repos": contrib_repos,
        "stars": stars,
        "commits": commits,
        "loc_add": loc_add,
        "loc_del": loc_del,
        "loc_total": loc_add - loc_del,
    }

    for mode in ("dark", "light"):
        template = os.path.join(HERE, f"about-{mode}.template.svg")
        out = os.path.join(HERE, f"about-{mode}.svg")
        shutil.copyfile(template, out)
        overwrite(out, values)
        print("updated", out)

    print(values)


if __name__ == "__main__":
    main()
