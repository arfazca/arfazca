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

import requests
from dateutil import relativedelta
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "cache")

HEADERS = {"authorization": "token " + os.environ["ACCESS_TOKEN"]}
USER_NAME = os.environ.get("USER_NAME", "arfazca")
BIRTHDAY = datetime.datetime(2002, 6, 15)


def simple_request(name, query, variables):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS,
    )
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


def follower_count(username):
    query = """
    query($login: String!){
        user(login: $login) { followers { totalCount } }
    }"""
    r = simple_request("follower_count", query, {"login": username})
    return int(r.json()["data"]["user"]["followers"]["totalCount"])


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
        stars += e["node"]["stargazers"]["totalCount"]
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
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"repo_name": repo_name, "owner": owner, "cursor": cursor}},
        headers=HEADERS,
    )
    if r.status_code != 200:
        if r.status_code == 403:
            raise Exception("Secondary rate limit hit while walking commit history")
        raise Exception("recursive_loc failed", r.status_code, r.text)
    branch = r.json()["data"]["repository"]["defaultBranchRef"]
    if branch is None:
        return 0, 0, 0
    history = branch["target"]["history"]
    for node in history["edges"]:
        if node["node"]["author"]["user"] == owner_id:
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
    edges = repo_edges_for_loc(["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"])
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

    if len(cache) != len(edges):
        cache = {}  # repo count changed - rebuild from scratch

    loc_add = loc_del = total_commits = 0
    new_lines = []
    for e in edges:
        name = e["node"]["nameWithOwner"]
        h = hashlib.sha256(name.encode()).hexdigest()
        branch_ref = e["node"]["defaultBranchRef"]
        remote_commit_count = branch_ref["history"]["totalCount"] if branch_ref else 0

        if h in cache and int(cache[h][0]) == remote_commit_count:
            commit_count, my_commits, add, dele = cache[h]
        else:
            owner, repo_name = name.split("/", 1)
            add, dele, my_commits = recursive_loc(owner, repo_name, owner_id) if branch_ref else (0, 0, 0)
            commit_count = remote_commit_count

        new_lines.append(f"{h} {commit_count} {my_commits} {add} {dele}\n")
        loc_add += int(add)
        loc_del += int(dele)
        total_commits += int(my_commits)

    with open(filename, "w") as f:
        f.writelines(new_lines)

    return loc_add, loc_del, total_commits


def find_and_replace(root, element_id, new_text):
    el = root.find(f".//*[@id='{element_id}']")
    if el is not None:
        el.text = new_text


def justify(root, element_id, new_text, target_len=0):
    if isinstance(new_text, int):
        new_text = "{:,}".format(new_text)
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    pad = max(0, target_len - len(new_text))
    dot_string = {0: "", 1: " ", 2: ". "}.get(pad, " " + "." * pad + " ")
    find_and_replace(root, f"{element_id}_dots", dot_string)


def overwrite(path, values):
    tree = etree.parse(path)
    root = tree.getroot()
    justify(root, "age_data", values["age"])
    justify(root, "repo_data", values["repos"], 6)
    justify(root, "contrib_data", values["contrib_repos"])
    justify(root, "star_data", values["stars"], 14)
    justify(root, "commit_data", values["commits"], 22)
    justify(root, "follower_data", values["followers"], 10)
    justify(root, "loc_data", values["loc_total"], 9)
    justify(root, "loc_add", values["loc_add"])
    justify(root, "loc_del", values["loc_del"], 7)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main():
    owner_id = {"id": user_getter(USER_NAME)}
    age = uptime_string()
    repos, stars = repos_and_stars(["OWNER"])
    _, contrib_repos = repos_and_stars(["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"])
    followers = follower_count(USER_NAME)
    loc_add, loc_del, commits = cached_loc_and_commits(owner_id)

    values = {
        "age": age,
        "repos": repos,
        "contrib_repos": contrib_repos,
        "stars": stars,
        "commits": commits,
        "followers": followers,
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
