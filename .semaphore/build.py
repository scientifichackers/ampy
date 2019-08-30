import io
import os
import tempfile
from pathlib import Path

import yaml

from ampy.settings import DOCKER_IMAGE
from ampy.util import call, shell

MPY_REPO = "https://github.com/micropython/micropython.git"
# PORT_NAME = os.environ["MPY_PORT"]
PORT_NAME = "esp32"
DOCKER_HOME = "/root"
MPY_DIR = Path.cwd() / "micropython"


def main():
    print("Cloing git repo...")
    version = clone_mpy_repo()

    print("Generating Dockerfile...")
    build_job = extract_build_job()
    dockerfile = gen_dockerfile(build_job)
    print("\n", "-" * 10, dockerfile.read_text(), "-" * 10, "\n")

    print("Building docker image...")
    image = build_docker_image(dockerfile, version)

    print("Running tests...")
    test_docker_image(image, build_job)

    print("Pusing docker image...")
    docker_login()
    docker_push(image)


def clone_mpy_repo() -> str:
    if not MPY_DIR.exists():
        call("git", "clone", MPY_REPO, MPY_DIR)
    os.chdir(MPY_DIR)

    call("git", "fetch")
    # version = call("git", "describe", "--abbrev=0", read_stdout=True).strip()
    version = "master"
    call("git", "checkout", version)

    return version


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


def test_docker_image(image: str, build_job: dict):
    try:
        for line in build_job["script"]:
            shell_in_docker(image, line)
    finally:
        for line in build_job.get("after_failure", []):
            shell_in_docker(image, line)


def shell_in_docker(image: str, cmd: str):
    shell(f"docker run -v {MPY_DIR}:{DOCKER_HOME} -w {DOCKER_HOME} {image} {cmd}")


def build_docker_image(dockerfile: Path, release: str) -> str:
    image = f"{DOCKER_IMAGE}:{PORT_NAME}-{release}"
    call("docker", "build", f"-t={image}", f"-f={dockerfile}", MPY_DIR)
    return image


def gen_dockerfile(build_job: dict) -> Path:
    dockerfile = Path(tempfile.gettempdir()) / (PORT_NAME + ".Dockerfile")

    with io.StringIO() as f:
        f.write("FROM ubuntu:xenial\n")
        f.write(f"ENV HOME {DOCKER_HOME}\n")
        f.write(f"ENV DEBIAN_FRONTEND noninteractive\n")
        f.write("WORKDIR $HOME\n")
        f.write("RUN apt-get update\n")

        f.write("RUN apt-get install -y wget git\n")

        if PORT_NAME == "esp32":
            f.write("COPY ports/esp32/Makefile ports/esp32/Makefile\n")

        for line in build_job["install"]:
            line = line.replace("sudo", "")
            line = line.replace("apt-get", "apt-get -y")
            f.write("RUN " + line + "\n")

        dockerfile.write_text(f.getvalue())

    return dockerfile


def extract_build_job():
    with open(MPY_DIR / ".travis.yml") as f:
        config = yaml.safe_load(f)

    for job in config["jobs"]["include"]:
        if not PORT_NAME in job["env"]:
            continue
        return job

    raise ValueError(f"Port {PORT_NAME!r} not found in .travis.yml")


if __name__ == "__main__":
    main()
