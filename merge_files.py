"""
Merges all code files in a directory using a designated LLM. Also runs assertion test to check if merge is successful. 
"""

import os, re, shutil, subprocess, tempfile, time
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


MERGE_SYS_PROMPT = """\
You are an expert coding assistant that specializes in merging code to prevent conflicts, as well as ensuring good software engineering practices by refactoring different functionalities into different code files. You are to generate one or more merged code snippet from multiple smaller code snippets. Whem merging the snippets, you should account for potential merge conflicts. Conflicts could arise in namespace conflicts, functionality conflicts, race conditions, etc. You must solve these issues by renaming relevant functions, or rewriting them to work with each other. However, you should minimize overall changes. Each code snippet you are given to merge comes with a set of test cases. You must also incorporate all test cases into the merged code (they should all pass). If the code you are given include interactive code that cannot be checked using test cases, organize the testable functions into a merged check(), call the check() after the if name == main shield, then comment out the interactive code (such as a Flask server setup). Note that if you rename a function, it's corresponding test cases must also be renamed. Lastly, your code must follow the following formatting instructions precisely:

For each code file you decide to generate, create two sections: the first section merges the code functionality, the second section merges the test cases. The entry point for the second section should always be 'check()'. Follwing these sections, include a 'if __name__  == \"__main__\"' which calls the check() function. Next, generate a proper filename for the python file. Below is an example of the correct formatting:

Prompt: 
```python

# code snippet 1
def function1(input):
    return output

def check():
    **test cases**

if __name__ == "__main__":
    check()
    
```
```python

# code snippet 2
def function2(input):
    return output

def check():
    **test cases**

if __name__ == "__main__":
    check()
```

Response: 
```python
def function1_refactored(input): 
    # one specific organized functionality from all input files
    return output

def check():
    assert function1(input) == expected_output
    etc.
```
Filename: refactored_func1.py

```python
def function2(input): 
    # another specific organized functionality from all input files
    return output

def check():
    assert function2(input) == expected_output
    etc.

if __name__ == "__main__":
    check()
```
Filename: refactored_func2.py

Prompt:
"""

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


def prompt_llm(prompt, system_prompt=None, model_name="gpt-4o-mini"):
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
    return text

# Set your OpenAI API key. Ensure you have it set in your environment.
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Ensures python file at filepath runs without error
def check_script_filepath(filepath, timeout=2):
    if not os.path.isfile(filepath):
        return False
    with open(filepath, "r") as f: 
        text = f.read()
        if not "check()" in text: 
            return True
    try:
        subprocess.run(
            ["python", filepath],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            env={**os.environ, "PYTHONPATH": os.path.dirname(filepath)}  # Ensure imports work
        )
        return True
    except subprocess.TimeoutExpired:
        return True  # Assume success after timeout
    except Exception:
        return False
    
# Ensures python code as string runs without error
def check_script_string(code, timeout=2):
    if not "check()" in code: 
        return True
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


def check_isolated_files(directory):
    for filename in os.listdir(directory):
        if not filename.endswith(".py"):
            continue
        filepath = os.path.join(directory, filename)
        result = check_script_filepath(filepath, timeout=2)
        if not result:
            raise ValueError(f"ERROR: Halting merge process. File {filename} does not run successfully.")


# Merges all .py files in a directory
def execute_merge(code_dir, add_modifying_prompt=None):
    code_string = ""
    for filename in os.listdir(code_dir):
        if not filename.endswith(".py"):
            continue
        filepath = code_dir + "/" + filename
        with open(filepath, "r", encoding="utf-8") as f: 
            code_string += f"```python\n{f.read()}\n```\n"

    code_string += "\nPlease provide the final merged Python project code." 
    if add_modifying_prompt:
        code_string += f"\nAdditionally, {add_modifying_prompt}"   
    merged_code = prompt_llm(code_string, system_prompt=MERGE_SYS_PROMPT, model_name="gpt-4o")
    code_snippets = extract_code_blocks(merged_code)
    filenames = extract_python_filenames(merged_code)
    assert len(code_snippets) == len(filenames)
    return code_snippets, filenames


def merge_modules(code_dir):
    try:
        # Check if all files in code_dir runs in isolation
        check_isolated_files(code_dir)
    except ValueError as e: 
        print(e)
        return

    # Gets merged code
    merged_code_snippets, filenames = execute_merge(code_dir)

    merge_finalized = False
    while not merge_finalized:
        # Check if merged code runs without error: 
        for snippet in merged_code_snippets:
            merge_success = check_script_string(snippet)
            if not merge_success:
                break
        else: 
            merge_finalized = True
            continue

        print("Merge unsuccessful. Re-executing merge")
        previous_merged_code = "\n".join(["```python\n" + snip + "\n```" for snip in merged_code_snippets])

        additional_instruction = f"You previously generated the following code:\n{previous_merged_code}\nIt did not run. Merge the files again but differently."
        merged_code_snippets, filenames = execute_merge(code_dir, add_modifying_prompt=additional_instruction)
        
    print("Merge successful!")

    # Format output 
    output = ""
    for snip, filename in zip(merged_code_snippets, filenames):
        output += f"##### {filename} #####\n{snip}\n"
    return output


if __name__ == "__main__":
    merged_code = merge_modules("/Users/tianyiniu/Code/hack3datafiles/Sample_files")
    print(merged_code)