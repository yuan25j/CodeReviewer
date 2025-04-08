import os, re, shutil
import subprocess, tempfile, time
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Set your OpenAI API key. Ensure you have it set in your environment.
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

CODE_GEN_SYS_PROMPT = """\
You are a coding assistant that generates clean concise python code. You also practice good software engineering practices. If the users's request is too complex to meaningfully fulfill using a single python file, seperate the functionality into multiple individual python files, each addressing a different aspect of the codebsae. Each python file should be represented by a seperate code block; where each code block is wrapped by '```python <main text>```' Your code output precisely follows the following formatting instructions:\n\nFor each pyton file you decide to generate, you are to generate one code snippet with two sections, the first section addresses the user's desired functionality, the second section provides some test cases that the code should pass. The entry point for the second section should always be 'check()'. Follwing these sections, include a 'if __name__  == \"__main__\"' which calls the check() function. If the code you are given include interactive code that cannot be checked using test cases, organize the testable functions into a merged check(), call the check() after the if name == main shield, then comment out the interactive code (such as a Flask server setup). Finally, also generate an appropriate filename for the file. Below is an example of the correct formatting:

Prompt: Generate a function that reverse an input string.
Response: 
```python
def reverse(input_str): 
    return input_str[::-1]

def check():
    assert reverse("abcd") == "dcba"
    assert reverse("aaa") == "aaa"
    assert reverse("a black cat") == "tac kcalb a")

if __name__ == "__main__":
    check()
```
Filename: fibonacci.py

Prompt:
"""

def clear_directory(path: str, create_if_missing: bool = True):
    if os.path.exists(path):
        if os.path.isdir(path):
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Remove file or symbolic link
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove subdirectory
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            raise NotADirectoryError(f"{path} exists but is not a directory.")
    elif create_if_missing:
        os.makedirs(path)


def prompt_llm(prompt, system_prompt=None, model_name="gpt-4o"):
    """Prompts a LLM with an optional system prompt and return the generated text."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.2,
    )
    text = response.choices[0].message.content.strip()
    print(f"Original response ######\n{text}")
    return text


def extract_code_blocks(text: str) -> list:
    """Extracts Python code blocks enclosed by ```python ... ``` from a string.
    
    Returns a list of code block strings.
    """
    pattern = r"```python\s+(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def extract_python_filenames(text: str):
    matches = re.findall(r"Filename:\s*[\w\-\.]+\.py", text)
    filenames = [match.split()[-1] for match in matches]
    return filenames


# Ensures python code as string runs without error
def check_script_string(code, timeout=2):
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        subprocess.run(
            ["python", tmp_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout
        )
        return True
    except subprocess.TimeoutExpired:
        return True  # Assume success after timeout
    except Exception as e:
        print(e)
        return False
    finally:
        if 'tmp_path' in locals():
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def generate_code_files(instruction):
    """Simulate a developer generating an independent Python file with test cases. Parses output to return code snippet and test snippet."""
    module_code = prompt_llm(instruction, system_prompt=CODE_GEN_SYS_PROMPT)
    code_snippets = extract_code_blocks(module_code)
    filenames = extract_python_filenames(module_code)
    print(len(code_snippets))
    print(len(filenames))
    for snip in code_snippets:
        print(snip)
        print("#######")
    print(filenames)
    assert len(code_snippets) == len(filenames)
    return code_snippets, filenames


def save_snippets_to_file(save_dir, code_snippet, filename):
    fp = save_dir + "/" + filename
    print(f"About to save snippet to file: {fp}")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(code_snippet)
    return 


def generate_project(starting_prompt, target_dir):
    clear_directory(target_dir)
    code_snippets, filenames = generate_code_files(starting_prompt)
    counter = 0
    for code_snippet, filename in zip(code_snippets, filenames):
        print(f"###### Snippet {counter} ######")
        counter += 1
        print(code_snippet)
        print(filename)

        # if not check_script_string(code_snippet):
        #     raise ValueError("Error with snippet")
        
        save_snippets_to_file(target_dir, code_snippet, filename)
    return


if __name__ == "__main__":
    save_dir = "/Users/tianyiniu/Code/hack3datafiles/Sample_files"
    # clear_directory(save_dir)
    
    # Generate fibonacci snippet
    # instruction1 = "what's a simple python function that gets the nth fibonacci number?"
    instruction1 = "what's a simple python function that finds the maximum prime factor for a integer < 100?"
    code_snippets, filenames = generate_code_files(instruction1)
    counter = 0
    for snippet, filename in zip(code_snippets, filenames):
        print(f"###### Snippet {counter} ######")
        counter += 1
        print(snippet)
        print(filename)
        save_snippets_to_file(save_dir, snippet, filename)

    # Generate a project that involves an interactive environment
    # generate_project("I a simple project that involves multiple files. I want to program an interactive game where the user enters a password and the program returns an encrypted key. The encryption should happen in a seperate file than the user input! The password should just be the input reversed for now")
