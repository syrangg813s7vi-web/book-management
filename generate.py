#!/usr/bin/env python3
"""Generate books.json and index.html from GitHub repos tagged with 'book' topic."""

import json
import os
import sys
from datetime import datetime, timezone

import requests

OWNER = "syrangg813s7vi-web"
TOPIC = "book"
BOOKS_JSON = "books.json"
INDEX_HTML = "index.html"
TEMPLATE_HTML = "template.html"


def fetch_all_repos(token: str) -> list[dict]:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{OWNER}/repos"
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def is_book_repo(repo: dict) -> bool:
    topics = repo.get("topics", [])
    return TOPIC in topics and not repo.get("archived", False)


def check_pages(repo_name: str, token: str) -> str | None:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/repos/{OWNER}/{repo_name}/pages"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("html_url")
    return None


def collect_books(token: str) -> list[dict]:
    repos = fetch_all_repos(token)
    books = []
    for repo in repos:
        if not is_book_repo(repo):
            continue
        pages_url = check_pages(repo["name"], token)
        books.append({
            "name": repo["name"],
            "description": repo.get("description") or "",
            "pages_url": pages_url,
            "repo_url": repo["html_url"],
            "updated_at": repo["updated_at"],
        })
    books.sort(key=lambda b: b["updated_at"], reverse=True)
    return books


def render_index(books: list[dict], template_path: str) -> str:
    with open(template_path, encoding="utf-8") as f:
        template = f.read()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = template.replace("{{BOOKS_JSON}}", json.dumps(books, ensure_ascii=False))
    html = html.replace("{{GENERATED_AT}}", generated_at)
    return html


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching repos for {OWNER}...")
    books = collect_books(token)
    print(f"Found {len(books)} book repo(s).")

    with open(BOOKS_JSON, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"Written {BOOKS_JSON}")

    html = render_index(books, TEMPLATE_HTML)
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written {INDEX_HTML}")


if __name__ == "__main__":
    main()
