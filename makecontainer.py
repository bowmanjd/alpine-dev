#!/usr/bin/env python3

import io
import json
import logging
import os
import re
import shlex
import subprocess
import time

logging.basicConfig(format="%(message)s", level=logging.INFO)


def get_latest(image_name, repo="library", pattern=r"(\d\.?)+", registry="docker.io"):
    version_re = re.compile(pattern)
    clean_re = re.compile("[^0-9.]")
    try:
        info = subprocess.check_output(
            ["skopeo", "list-tags", f"docker://{registry}/{repo}/{image_name}"]
        )
    except subprocess.CalledProcessError:
        version = ""
    else:
        try:
            tags = json.loads(info)["Tags"]
            version_lookup = {
                tuple(map(int, clean_re.sub("", t).split("."))): t
                for t in tags
                if version_re.match(t)
            }
            version = version_lookup[max(version_lookup)]
        except (IndexError, ValueError):
            version = ""
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
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, proc.args)
    return output.getvalue().strip()


def buildah_run(container, cmd):
    return buildah(f"run {container} -- {cmd}")


def build_recent(image_name):
    source_latest = get_latest("alpine")
    target_latest = get_latest(image_name, "bowmanjd")
    if source_latest != target_latest:
        build(image_name, source_latest)


def build(version):
    ctr = buildah(f"from docker.io/alpine:{version}")
    tags = [
        f"{image_name}:{tag}",
        f"{image_name}:latest",
        f"{image_name}:{time.strftime('%Y.%m.%d')}",
    ]
    buildah_run(
        ctr, "apk --no-cache add autoconf automake gcc make musl-dev openssl-dev git"
    )
    buildah(f"config --workingdir /work {ctr}")
    buildah(f"config --label version='{tag}' {ctr}")
    try:
        image_id = buildah(f"images -q {tags[0]}")
    except subprocess.CalledProcessError:
        pass
    else:
        buildah(f"rmi -f {image_id}")
    buildah(f"commit --squash --rm {ctr} {image_name}:{tag}")
    buildah("tag " + " ".join(tags))
    return tags


def push(registry, repo, image_name, tag):
    pass


if __name__ == "__main__":
    # image_name = "alpine-dev"
    # build_recent(image_name)
    print(get_latest("ubuntu", pattern="focal-(\d\.?)+"))
