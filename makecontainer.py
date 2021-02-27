#!/usr/bin/env python3

import io
import json
import logging
import shlex
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import urlopen

logging.basicConfig(format="%(message)s", level=logging.INFO)


def get_latest(repo, image_name):
    try:
        info = subprocess.check_output(
            ["skopeo", "inspect", f"docker://docker.io/{repo}/{image_name}"]
        )
    except subprocess.CalledProcessError:
        version = ""
    else:
        try:
            tags = json.loads(info)["RepoTags"]
            latest = sorted(tuple(map(int, t.split("."))) for t in tags if "." in t)[-1]
            version = ".".join(str(i) for i in latest)
        except (IndexError, ValueError):
            version = ""
    return version


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


def buildah(cmd):
    with subprocess.Popen(
        ["buildah", *shlex.split(cmd)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as proc:
        logging.info(shlex.join(proc.args))
        output = io.StringIO()
        for line in proc.stdout:
            output.write(line)
            logging.info(line.strip())
    return output.getvalue().strip()


def buildah_run(container, cmd):
    return buildah(f"run {container} -- {cmd}")


def build_recent(image_name):
    source_latest = get_latest("library", "alpine")
    target_latest = get_latest("bowmanjd", image_name)
    if source_latest != target_latest:
        build(image_name, source_latest)


def build(image_name, tag):
    ctr = buildah(f"from docker.io/alpine:{tag}")
    buildah_run(
        ctr, "apk --no-cache add autoconf automake gcc make musl-dev openssl-dev git"
    )
    buildah(f"config --workingdir /work {ctr}")
    buildah(f"config --label version='{tag}' {ctr}")
    try:
        image_id = buildah(f"images -q {image_name}:{tag}")
    except subprocess.CalledProcessError:
        pass
    else:
        buildah(f"rmi -f {image_id}")
    buildah(f"commit --squash --rm {ctr} {image_name}:{tag}")
    buildah(
        f"tag {image_name}:{tag} {image_name}:latest"
        f" {image_name}:{time.strftime('%Y.%m.%d')}"
    )


if __name__ == "__main__":
    # image_name = "alpine-dev"
    # build_recent(image_name)
    print(get_latest("library", "alpine"))
