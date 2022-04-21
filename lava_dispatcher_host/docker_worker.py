# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-present Linaro Limited
#
# Author: Antonio Terceiro <antonio.terceiro@linaro.org>
#
# This file is part of LAVA.
#
# LAVA is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# LAVA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses>.

import logging
import logging.handlers
import os
import pathlib
import platform
import random
import re
import signal
import socket
import string
import subprocess
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from lava_common.constants import DISPATCHER_DOWNLOAD_DIR
from lava_common.worker import get_parser


#########
# Globals
#########
# Create the logger that will be configured later
logging.Formatter.convert = time.gmtime
LOG = logging.getLogger("lava-worker")
FORMAT = "%(asctime)-15s %(levelname)7s %(message)s"

PAT = re.compile(r"\d+\.\d+\.(\d+\.){0,1}\d{4}\.g[\d\w]+")


###########
# Helpers #
###########
def log_output(line):
    line = line.decode("utf-8").strip()
    if line[24:31] in ["  DEBUG", "   INFO", "WARNING", "  ERROR"]:
        LOG.info("> " + line[24:])
    else:
        LOG.info("> " + line)


def filter_options(options):
    ret = ["--worker-dir", options.worker_dir, "--url", options.url]
    if options.ws_url:
        ret.extend(["--ws-url", options.ws_url])

    ret.extend(["--http-timeout", str(options.http_timeout)])
    ret.extend(["--ping-interval", str(options.ping_interval)])
    ret.extend(["--job-log-interval", str(options.job_log_interval)])

    if options.username:
        ret.extend(["--username", options.username])
    if options.token:
        ret.extend(["--token", options.token])
    if options.token_file:
        ret.extend(["--token-file", options.token_file])
    return ret


def has_image(image):
    try:
        subprocess.check_output(
            ["docker", "image", "inspect", image],
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_image(image):
    if has_image(image):
        return True

    try:
        subprocess.check_output(["docker", "pull", image], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as exc:
        LOG.warning(exc.output.decode("utf-8", errors="replace").strip())
    return False


def build_customized_image(image, build_dir):
    dockerfile = build_dir / "Dockerfile"
    if not dockerfile.exists():
        LOG.warning("Dockerfile (%s) not found", dockerfile)
        return image

    # To make sure lava-dispatcher image version matches lava-server version,
    # all the FROM commands defined in the original Dockerfile will be ignored
    # and Dockerfile.lava using the image passed to the function as base image
    # will be generated for building.
    with open(dockerfile, "r") as f:
        instructions = f.readlines()
    lava_dockerfile = build_dir / "Dockerfile.lava"
    with open(lava_dockerfile, "w") as f:
        f.write("# Generated by /usr/bin/lava-docker-worker\n")
        f.write(f"FROM {image}\n")
        for instruction in instructions:
            if not re.match(r" *FROM.*", instruction):
                f.write(instruction)

    tag = f"{image}.customized"
    try:
        p = subprocess.Popen(
            ["docker", "build", "--force-rm", "-f", "Dockerfile.lava", "-t", tag, "."],
            cwd=build_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        for line in p.stdout:
            log_output(line)
        return tag
    except subprocess.CalledProcessError:
        sys.exit(1)


class Terminate(RuntimeError):
    @classmethod
    def trigger(cls, *args):
        raise cls()


def run(version, options):
    if PAT.match(version):
        # development
        if platform.machine() == "x86_64":
            image = f"hub.lavasoftware.org/lava/lava/amd64/lava-dispatcher:{version}"
        elif platform.machine() == "aarch64":
            image = f"hub.lavasoftware.org/lava/lava/aarch64/lava-dispatcher:{version}"
        else:
            print("ERROR: unsupported architecture '{platform.machine()}'")
            sys.exit(1)
    else:
        # released version
        image = f"lavasoftware/lava-dispatcher:{version}"

    LOG.info("Using image %s", image)
    rand = "".join((random.choice(string.hexdigits) for c in range(5)))
    docker_name = f"lava-worker-{version}-{rand}"
    LOG.info("Docker name %s", docker_name)
    service = [
        "docker",
        "run",
        "--rm",
        "--init",
        "--privileged",
        "--net=host",
        "--name",
        docker_name,
    ]

    mounts = []
    mounts.append((DISPATCHER_DOWNLOAD_DIR, None))

    tftp_dir = pathlib.Path("/srv/tftp")
    if tftp_dir.exists():
        mounts.append((str(tftp_dir), None))

    worker_dir = options.worker_dir.absolute()
    worker_dir.mkdir(parents=True, exist_ok=True)
    mounts.append((worker_dir, None))
    mounts.append(("/run/udev", None))
    mounts.append(("/dev", None))
    mounts.append(("/var/run/docker.sock", None))
    mounts.append(("/boot", "readonly=true"))
    mounts.append(("/lib/modules", "readonly=true"))
    for path, opts in mounts:
        m = f"--mount=type=bind,source={path},destination={path}"
        if opts:
            m += "," + opts
        service.append(m)

    # TODO handle ctrl-c/SIGINT
    # TODO dev move: provide default values for all options, including
    # TODO           translate localhost -> 172.17.0.1
    # TODO dev move: build and use docker image from local tree

    # set hostname to have a fixed default worker name
    service.append("--hostname=docker-" + socket.getfqdn())

    if not get_image(image):
        LOG.warning("=> Image not available")
        time.sleep(5)
        return

    if options.build_dir.exists():
        LOG.info("Building custom image in %s", options.build_dir)
        image = build_customized_image(image, options.build_dir)
    service.append(image)

    try:
        signal.signal(signal.SIGTERM, Terminate.trigger)
        container = subprocess.Popen(
            service
            + ["lava-worker", "--exit-on-version-mismatch", "--wait-jobs"]
            + ["--log-file", "-", "--name", options.name]
            + filter_options(options),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,
        )
        for line in container.stdout:
            log_output(line)
        if container.poll():
            LOG.error("Returned %d", container.poll())
            time.sleep(5)
    except FileNotFoundError as exc:
        LOG.error("'%s' not found", exc.filename)
        time.sleep(5)
    except subprocess.CalledProcessError as failure:
        LOG.info("Failed to start the worker")
        time.sleep(5)
    except (KeyboardInterrupt, Terminate):
        LOG.info("[EXIT] Received Ctrl+C")
        subprocess.check_output(
            ["docker", "kill", "--signal", "TERM", docker_name],
            stderr=subprocess.STDOUT,
        )
        for line in container.stdout:
            log_output(line)
        LOG.error("Returned %d", container.wait())
        sys.exit(0)


def get_server_version(options):
    server_version_url = re.sub(r"/$", "", options.url) + "/api/v0.2/system/version/"
    retries = Retry(total=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retries)
    http = requests.Session()
    http.mount("http://", adapter)
    http.mount("https://", adapter)
    server_version = http.get(server_version_url, timeout=10).json()
    return server_version["version"]


##########
# Setups #
##########
def setup_logger(log_file: str, level: str) -> None:
    """
    Configure the logger

    :param log_file: the log_file or "-" for sys.stdout
    :param level: the log level
    """
    # Configure the log handler
    if log_file == "-":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.handlers.WatchedFileHandler(log_file)
    handler.setFormatter(logging.Formatter(FORMAT))
    LOG.addHandler(handler)

    # Set-up the LOG level
    if level == "ERROR":
        LOG.setLevel(logging.ERROR)
    elif level == "WARN":
        LOG.setLevel(logging.WARN)
    elif level == "INFO":
        LOG.setLevel(logging.INFO)
    else:
        LOG.setLevel(logging.DEBUG)


def main():
    # Parse command line
    options = get_parser(docker_worker=True).parse_args()
    options.build_dir = options.build_dir.resolve()

    if options.devel:
        options.url = "http://localhost:8000/"
        options.ws_url = "http://localhost:8001/"
        options.worker_dir = pathlib.Path.cwd() / "tmp" / "worker-docker"
        options.level = "DEBUG"
        options.log_file = "-"
    elif not options.url:
        print("ERROR: --url option not provided", file=sys.stderr)
        sys.exit(1)

    # Setup logger
    setup_logger(options.log_file, options.level)
    LOG.info("[INIT] LAVA docker worker has started.")
    LOG.info("[INIT] Name   : %r", options.name)
    LOG.info("[INIT] Server : %r", options.url)

    LOG.info("[INIT] Starting main loop")
    while True:
        LOG.info("Get server version")
        try:
            server_version = get_server_version(options)
        except requests.RequestException:
            LOG.warning("-> Unable to get server version")
            continue
        LOG.info("=> %s", server_version)
        try:
            run(server_version, options)
        except Exception as exc:
            LOG.exception(exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
