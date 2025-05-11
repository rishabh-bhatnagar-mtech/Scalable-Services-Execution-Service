import os
import pathlib
import subprocess
import tempfile

import docker


def run_code(code: str, test_input: str, language: str):
    client = docker.from_env()
    with tempfile.TemporaryDirectory() as tmpdir:
        pathlib.Path(tmpdir).mkdir(parents=True, exist_ok=True)
        ext = ".py" if language == "python" else ".go"
        code_file = os.path.join(tmpdir, f"main{ext}")
        with open(code_file, "w") as f:
            f.write(code)
        input_file = os.path.join(tmpdir, "input.txt")
        with open(input_file, "w") as f:
            f.write(test_input)
        image = "python:3.11-slim" if language == "python" else "golang:1.22"
        container = client.containers.run(
            image=image,
            command="sleep 600",
            working_dir="/code",
            detach=True,
            tty=True
        )
        try:
            subprocess.run([
                "docker", "cp", code_file, f"{container.id}:/code/main{ext}"
            ], check=True)
            subprocess.run([
                "docker", "cp", input_file, f"{container.id}:/code/input.txt"
            ], check=True)
            run_cmd = {
                "python": "python main.py < /code/input.txt",
                "golang": "go run main.go < /code/input.txt"
            }[language]
            exec_result = container.exec_run(
                cmd=["/bin/sh", "-c", run_cmd],
                stdout=True,
                stderr=True
            )
            output = exec_result.output.decode()
            print("Output of the docker container:", output, flush=True)
            return output
        finally:
            container.remove(force=True)


if __name__ == "__main__":
    code = '''package main

import "fmt"

func main() {
    var s string
    fmt.Scan(&s)
    fmt.Println("Input: ", s)
}'''
    test_input = "Hello, Docker!"
    language = "golang"
    print(run_code(code, test_input, language))
