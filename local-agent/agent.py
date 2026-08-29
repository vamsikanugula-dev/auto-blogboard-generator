import os
import subprocess
from pathlib import Path
from ollama import chat

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def read_file(path):
    file_path = (PROJECT_ROOT / path).resolve()

    if not str(file_path).startswith(str(PROJECT_ROOT)):
        return "Error: access outside project directory is not allowed."

    if not file_path.exists():
        return f"Error: {path} does not exist."

    return file_path.read_text(encoding="utf-8")

def write_file(path, content):
    file_path = (PROJECT_ROOT / path).resolve()

    if not str(file_path).startswith(str(PROJECT_ROOT)):
        return "Error: access outside project directory is not allowed."

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    return f"Successfully wrote {path}"

def run_command(command):
    result = subprocess.run(
        command,
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180
    )

    return (
        f"Exit code: {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the current project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or replace the contents of a project file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file."
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete new file contents."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a command in the project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    }
]

messages = [
    {
        "role": "system",
        "content": f"""
You are a local coding agent.

You are working inside this project:

{PROJECT_ROOT}

You can inspect and modify the project using tools.

When the user asks you to inspect files, use read_file.
When the user asks you to modify files, use write_file.
When testing or inspecting the project, use run_command.

Do not merely explain what you would do.
Actually use the tools when necessary.

Never access files outside the project directory.
"""
    }
]

print("Local Qwen Coding Agent")
print(f"Project: {PROJECT_ROOT}")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You > ")

    if user_input.lower() in {"exit", "quit"}:
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    for _ in range(20):
        response = chat(
            model="qwen3.5:9b",
            messages=messages,
            tools=tools
        )

        message = response["message"]
        messages.append(message)

        if not message.get("tool_calls"):
            print("\nQwen >", message.get("content", ""))
            break

        for call in message["tool_calls"]:
            name = call["function"]["name"]
            args = call["function"]["arguments"]

            print(f"\n[Tool] {name}")

            if name == "read_file":
                result = read_file(args["path"])

            elif name == "write_file":
                result = write_file(
                    args["path"],
                    args["content"]
                )

            elif name == "run_command":
                result = run_command(args["command"])

            else:
                result = f"Unknown tool: {name}"

            messages.append({
                "role": "tool",
                "content": result
            })

            print(result[:1000])

    else:
        print("Agent reached the maximum tool iterations.")