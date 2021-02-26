#!/usr/bin/env python3

import io
import shlex
import subprocess
import sys
from urllib.request import urlopen


def latest_alpine_version():
    version = ""
    with urlopen(
        "https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86_64/latest-releases.yaml"
    ) as response:
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
        print(shlex.join(proc.args))
        output = io.StringIO()
        for line in proc.stdout:
            output.write(line)
            sys.stdout.write(line)
    return output.getvalue().strip()


def buildah_run(container, cmd):
    return buildah("run {container} -- {cmd}")


def build():
    tag = latest_alpine_version()
    ctr = buildah(f"from docker.io/alpine:{tag}")
    buildah_run(
        ctr, "apk --no-cache add autoconf automake gcc make musl-dev openssl-dev git"
    )
    buildah("config", "--workingdir", "/work", ctr)
    buildah("commit", "--squash", "--rm", ctr, f"alpine-compiler:{tag}")


if __name__ == "__main__":
    build()
