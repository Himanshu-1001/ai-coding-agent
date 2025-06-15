from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
import os

load_dotenv()

client = OpenAI()

def get_weather(city: str):
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."
    
    return "Something went wrong"


def create_directories(dir_path):
    os.makedirs(dir_path, exist_ok=True)
    return f"Directory created at {dir_path}"


def file_write(filePath, fileContent):
    if not os.path.exists(os.path.dirname(filePath)):
        return "Error: Directory does not exist"
    if os.path.exists(filePath):
        return "Error: File already exist"
    
    with open(filePath, "w") as file:
        file.write(fileContent)

    return f"Content is written to {filePath}"


def run_cmd(cmd):
    # BLOCKED_CMDS = ["rm", 'shutdown', 'reboot']
    # if any(block_cmd in cmd for block_cmd in BLOCKED_CMDS):
    #     return "Command can't be executed as it is dangerous for the system"
    return os.system(cmd)


    

available_tool = {
    "get_weather": get_weather,
    "file_write": file_write,
    "run_cmd": run_cmd,
}


SYSTEM_PROMPT = """
    You are an helpful AI Assistant who is responsible for solving user query.
    For a user query, you perform these steps start, suggestion, plan, action and observe.

    Rules:
    1. Follow the output in the json format.
    2. Always perform one step at a time and wait for the next input.
    3. Carefully analyse the user query.

    Safety Rules:
    1. Never execute the dangerous commands(rm, del, format, etc).
    2. Confirm file paths before overwriting.
    3. Reject commands that could harm the computer.
    4. When using echo with special characters, always use quotes and proper escaping

    Output format:
    {{
        "step": "string",
        "content": "string",
        "function": "The name of the funtion when step is action.
        "input": The input parameter for the function.
        "safety_check": bool
    }}

    Available Tools:
    1. get_weather: This tools takes location as an input and returns the weather of that location.
    2. file_write: This tool is used to perform the  write operation on the file and takes two parameters file path and file content.
    2. run_cmd: This tool is used to execute linux commands in the terminal and accepts a parameter command and executes on linux machine.

    Examples:
    User: What is the weather of Delhi
    Output: {{"step": "start", "content": "The user is asking for the weather of Delhi"}}
    Output: {{"step": "plan", "content": "To get the weather of Delhi, need to call the get_weather tool"}}
    Output: {{"step": "action",  "function": "get_weather", input: "Delhi"}}
    Output: {{"step": "observe", "content": "12 Degree Celcius"}}
    Output: {{ "step": "output", "content": "The weather for Delhi is 12 degrees." }}
    
    
    Examples:
    User: Create a simple text file inside project folder with Hello World written inside the file.
    Output: {{"step": "start", "content": "The user is asking to create a simple text file inside project folder with Hello World written inside the file"}}
    Output: {{"step": "plan", "content": "To solve user query, 1. Need to create a folder project, 2. Naviagte to the project folder and create a file hello_world.txt with Hello World wriiten inside it.     "}}
    Output: {{"step": "action", "function": "run_cmd", "input": "mkdir project", "safety_check": True}}
    Output: {{"step": "observe", "content": "project folder created successfully"}}
    Output: {{"step": "plan", "content": "Now, navigate to the project directory and create a file"}}
    Output: {{"step": "action", "function": "run_cmd", "input": "cd project && echo "Hello World" > hello_world.txt", "safety_check": True}}
    Output: {{"step": "observe", "content": "project created successfully"}}
    Output: {{ "step": "output", "content": "The file is created inside the project with Hello world wriiten inside it." }}
    
    Examples:
    User: Create a simple todo react app using vite with react.
    Output: {{"step": "start", "content": "The user is asking to create a simple todo react app using vite with react"}}
    Output: {{"step": "suggestion", "content": "Some suggestions to enhance your todo app, 1. Want to Add Dark Mode, 2. Want to Add subtasks, 3. Want to add date and time also "}}
    Output: {{"step": "plan", "content": "To create a todo app using vite with react, first need to inititalize the project, install dependicies, create files and write the code. and then run the application"}}
    Output: {{"step": "action", "function": "run_cmd", "input": "npx create vite@latest todo-app -- --template react", "safety_check": True}}
    Output: {{"step": "observe", "content": "project inititalized successfully"}}
    Output: {{"step": "plan", "content": "Now, navigate to the project directory and install the dependencies"}}
    Output: {{"step": "action", "function": "run_cmd", "input": "cd todo-app && npm install", "safety_check": True}}
    Output: {{"step": "observe", "content": ""All dependencies have been installed successfully in the 'todo-app' folder. The next step is to implement the frontend CRUD functionality for the todo app."}}
    ...so on
    Output: {{ "step": "output", "content": "Project created successfully and the application is also running." }}
    
"""


messages = [{"role": "system", "content": SYSTEM_PROMPT}]


while True:
    query = input(">")
    if(query == "exit"):
        break
    
    messages.append({"role": "user", "content": query})
    
    while True:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=messages
        )

        messages.append({"role": "assistant", "content": json.dumps(response.choices[0].message.content)})
        parsed_response = json.loads(response.choices[0].message.content)

        print('🤖', parsed_response)
        
        if(parsed_response.get("step") == "suggestion"):
            break
        
        if(parsed_response.get("step") == "action"):
            if not parsed_response.get("safety_check"):
                messages.append({"role": "user", "content": json.dumps({"step": "observe", "output": "Command is harmful and cannot be execute."})})
                continue
            
            func = parsed_response.get("function")
            arg = parsed_response.get("input")
            
            fun_to_call = available_tool[func]
            print(f"Tool called {func} with {arg}")
            ans = fun_to_call(arg)
            print("🔎", ans)
            messages.append({"role": "user", "content": json.dumps({"step": "observe", "output": ans})})
            continue
        
        if(parsed_response.get("step") == "output"):
            break