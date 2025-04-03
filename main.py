import os
import openai

# Set your OpenAI API key. Ensure you have it set in your environment.
openai.api_key = '' 

def call_chatgpt(prompt, system_prompt=None):
    """
    Call ChatGPT (gpt-3.5-turbo) with an optional system prompt and return the generated text.
    """
    messages = []
    if system_prompt:
        messages.append({"srole": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.2,  # Lower temperature for more deterministic output
    )
    return response.choices[0].message.content.strip()

def generate_module(developer_id, instruction):
    """
    Simulate a developer generating an independent Python module with test cases.
    """
    prompt = (
        f"You are Developer {developer_id}. Your task is to create a complete, independent Python module for a project. "
        f"{instruction}\n"
        "Output the full module code including necessary imports, functions, classes, and a set of test cases that verify your module's functionality. "
        "Make sure the tests are executable (e.g., using unittest or simple assert statements) so that the final merged project can run all tests successfully."
    )
    module_code = call_chatgpt(prompt)
    return module_code

def merge_modules(modules):
    """
    Use ChatGPT as a head LLM to merge multiple code modules into one final, conflict-free project.
    """
    prompt = (
        "You are a code reviewer. Three developers have submitted separate, independent Python modules for a project. "
        "Each module includes test cases to verify its functionality. Your task is to merge these modules into one final, cohesive Python project that passes all test cases. "
        "Integrate all functionalities seamlessly, resolve any merge conflicts, and include a main block that runs all tests. "
        "Ensure the final code is runnable and well-organized.\n\n"
    )
    for i, module in enumerate(modules, start=1):
        prompt += f"Module {i}:\n{module}\n\n"
    prompt += "Please provide the final merged Python project code."
    
    final_code = call_chatgpt(prompt)
    return final_code

def main():
    # Instructions for each developer's module, now including test cases.
    instruction1 = (
        "Create a module that handles data input. "
        "This module should read user input from the command line and parse it into a structured format (e.g., a dictionary). "
        "Include error handling for invalid input. "
        "Also, write test cases to verify that the parsing works correctly and errors are handled as expected."
    )
    instruction2 = (
        "Create a module that implements the core business logic. "
        "This module should perform computations or data transformations based on input from the data module. "
        "Define functions that process the data and return the results. "
        "Also, include test cases to ensure the business logic functions correctly for various inputs."
    )
    instruction3 = (
        "Create a module that handles output formatting. "
        "This module should take the processed data and results, format them nicely, and print them to the console. "
        "Include functions for generating a user-friendly report and test cases to verify that the output is formatted as expected."
    )

    # Generate code modules (including tests) from the three simulated developers.
    module1 = generate_module("1", instruction1)
    module2 = generate_module("2", instruction2)
    module3 = generate_module("3", instruction3)

    print("Module from Developer 1 (Data Input):\n")
    print(module1)
    print("\n" + "="*60 + "\n")
    print("Module from Developer 2 (Business Logic):\n")
    print(module2)
    print("\n" + "="*60 + "\n")
    print("Module from Developer 3 (Output Formatting):\n")
    print(module3)
    print("\n" + "="*60 + "\n")

    # Merge all modules using the head LLM.
    final_project_code = merge_modules([module1, module2, module3])
    print("Final Merged Project Code:\n")
    print(final_project_code)

if __name__ == "__main__":
    main()

