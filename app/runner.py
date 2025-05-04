import os
import tempfile

import docker


def run_code(code: str, test_input: str, language: str):
    client = docker.from_env()
    with tempfile.TemporaryDirectory() as tmpdir:
        ext = ".py" if language == "python" else ".go"
        code_file = os.path.join(tmpdir, f"main{ext}")
        with open(code_file, "w") as f:
            f.write(code)

        input_file = os.path.join(tmpdir, "input.txt")
        with open(input_file, "w") as f:
            f.write(test_input)

        image = "python:3.11-slim" if language == "python" else "golang:1.22"
        cmd = {
            "python": "python main.py < input.txt",
            "golang": "go run main.go < input.txt"
        }[language]

        # Run a docker container for executing the code
        result = client.containers.run(
            image=image,
            command=cmd,
            volumes={tmpdir: {'bind': '/code', 'mode': 'ro'}},
            working_dir="/code",
            network_disabled=True,
            mem_limit="256m",
            cpu_period=100000,
            cpu_quota=50000,
            stderr=True,
            stdout=True,
            remove=True,
            timeout=10
        )
        return result.decode()
