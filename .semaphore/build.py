import io
import os
import tempfile
import zipfile
from pathlib import Path
from typing import NamedTuple

import requests
import yaml

from ampy.settings import DOCKER_IMAGE
from ampy.util import call

GITHUB_API = "https://api.github.com"
MPY_RELEASES_URL = f"{GITHUB_API}/repos/micropython/micropython/releases"
PORT_NAME = os.environ["MPY_PORT"]
# PORT_NAME = "esp32"
DOCKER_HOME = "/root"


class MpyRelease(NamedTuple):
    zip_url: str
    version: str


def main():
    print("Getting latest micropython release...")
    release = get_latest_release()

    print(f"Downloading micropython {release.version!r}...")
    mpy_dir = download_latest_release(release, Path.cwd())
    print(f"Downloaded @ {mpy_dir!r}")

    print("Generating Dockerfile...")
    build_job = extract_build_job(mpy_dir)
    dockerfile = gen_dockerfile(build_job)
    print("\n", "-" * 10, dockerfile.read_text(), "-" * 10, "\n")

    print("Building docker image...")
    image = build_docker_image(dockerfile, mpy_dir, release)

    print("Running tests...")
    test_docker_image(image, mpy_dir, build_job)

    print("Pusing docker image...")
    docker_login()
    docker_push(image)


def docker_login():
    call(
        "docker",
        "login",
        f"-u={os.environ['DOCKER_USER']}",
        f"-p={os.environ['DOCKER_PASS']}",
        silent=True,
    )


def docker_push(image: str):
    call("docker", "push", image)


def test_docker_image(image: str, mpy_dir: Path, build_job: dict):
    try:
        for line in build_job["script"]:
            shell_in_docker(image, mpy_dir, line)
    finally:
        for line in build_job.get("after_failure", []):
            shell_in_docker(image, mpy_dir, line)


def shell_in_docker(image: str, mpy_dir: Path, cmd: str):
    call(
        "docker", "run", f"-v={mpy_dir}:{DOCKER_HOME}", f"-w={DOCKER_HOME}", image, cmd
    )


def build_docker_image(dockerfile: Path, mpy_dir: Path, release: MpyRelease) -> str:
    image = f"{DOCKER_IMAGE}:{PORT_NAME}-{release.version}"
    call("docker", "build", f"-t={image}", f"-f={dockerfile}", mpy_dir)
    return image


def gen_dockerfile(build_job: dict) -> Path:
    dockerfile = Path(tempfile.gettempdir()) / (PORT_NAME + ".Dockerfile")

    with io.StringIO() as f:
        f.write("FROM ubuntu:xenial\n")
        f.write(f"ENV HOME {DOCKER_HOME}\n")
        f.write(f"ENV DEBIAN_FRONTEND noninteractive\n")
        f.write("WORKDIR $HOME\n")
        f.write("RUN apt-get update\n")

        if PORT_NAME == "esp32":
            f.write("RUN apt-get install -y wget git\n")
            f.write("COPY ports/esp32/Makefile ports/esp32/Makefile\n")
        elif PORT_NAME == "esp8266":
            f.write("RUN apt-get install -y wget zcat git\n")

        for line in build_job["install"]:
            line = line.replace("sudo", "")
            line = line.replace("apt-get", "apt-get -y")
            f.write("RUN " + line + "\n")

        dockerfile.write_text(f.getvalue())

    return dockerfile


def extract_build_job(mpy_dir: Path):
    with open(mpy_dir / ".travis.yml") as f:
        config = yaml.safe_load(f)

    for job in config["jobs"]["include"]:
        if not PORT_NAME in job["env"]:
            continue
        return job

    raise ValueError(f"Port {PORT_NAME!r} not found in .travis.yml")


def download_latest_release(release: MpyRelease, dest_dir: Path) -> Path:
    mpy_dir = dest_dir / f"micropython-{release.version}"
    if not mpy_dir.exists():
        download_release(release)
    return mpy_dir


def download_release(release: MpyRelease):
    data = requests.get(release.zip_url).content
    with io.BytesIO(data) as b:
        with zipfile.ZipFile(b) as f:
            f.extractall()


def get_latest_release() -> MpyRelease:
    return MpyRelease(
        "https://github.com/micropython/micropython/archive/master.zip", "master"
    )
    # release = requests.get(MPY_RELEASES_URL).json()[0]
    # return MpyRelease(release["zipball_url"], release["tag_name"].replace("v", ""))


if __name__ == "__main__":
    main()
