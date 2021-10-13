#!/usr/bin/env python3

"""Miscellaneous functions for handling Alpine containers."""

import json
from urllib.error import HTTPError
# from urllib.parse import urlencode
from urllib.request import Request, urlopen


def list_tags(image_name, repo="library"):
    auth_url = "https://auth.docker.io/token"
    url = f"https://index.docker.io/v2/{repo}/{image_name}/tags/list"
    with urlopen(
        f"{auth_url}?service=registry.docker.io&scope=repository:{repo}/{image_name}:pull"
    ) as response:
        payload = json.loads(response.read())
        token = payload.get("token")
    req = Request(
        url,
        headers={"Authorization": "Bearer " + token},
    )
    with urlopen(req) as response:
        payload = json.loads(response.read())
    return payload.get("tags")


def tag_exists(repo, image_name, tag):
    url = f"https://hub.docker.com/v2/repositories/{repo}/{image_name}/tags/{tag}/"
    exists = False
    try:
        with urlopen(url) as response:
            if response.status == 200:
                exists = True
    except HTTPError as e:
        if e.code == 404:
            exists = False
        else:
            raise
    return exists


def latest_alpine_version():
    version = ""
    mirror = "https://dl-cdn.alpinelinux.org/alpine"
    url = f"{mirror}/latest-stable/releases/x86_64/latest-releases.yaml"
    with urlopen(url) as response:
        for line in response:
            row = line.decode()
            if "version" in row:
                version = row.split(":")[-1].strip()
                break
    return version


if __name__ == "__main__":
    print(list_tags("alpine"))
