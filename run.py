import openai
import os
import subprocess
import time
import json
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()
openai.api_key = os.getenv("OPEN_AI_KEY")
def get_code_from_gpt(prompt):
    # Define the system message and the user prompt
    messages = [
        {"role": "system", "content": '''
        You are an assistant that builds vanilla JavaScript projects.
        You build javascript projects with clean code, beautiful styling, and responsive design.
        The projects must be professional and ready to be deployed.
        The projects are on the level of a senior developer with 20 years of experience.
        '''
         },
        {"role": "user", "content": prompt}
    ]

    # Get the code from the GPT-4 model
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )

    return response['choices'][0]['message']['content']


def create_file(file_type, project_num, user_prompt):
    # Define the prompt for the AI to generate code
    code_prompt = f'''
    I want you to build me the following website: {user_prompt}.
    It must be a vanilla JavaScript project. 
    Before you start, make sure you have an idea of what the whole project should look like.
    The project must have a working javascript file, a working html file, and a working css file.
    The file names are index.html, index.js, and index.css.
    The project must be beautifully styled and responsive.
    In the next message give me only the code for the {file_type} file.
    Don't say anything else beside the code, because i will put your whole response in the index.{file_type} file.
    '''

    # Get the generated code
    code = get_code_from_gpt(code_prompt)

    # Define the file path and make sure the directory exists
    file_path = f"Versions/V{project_num}/index.{file_type}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write the generated code to the file
    with open(file_path, "w") as f:
        f.write(code)


def run_lighthouse(project_folder):
    # Define the path to the batch file and the output path for the report
    batch_file_path = "run_lighthouse.bat"
    output_path = os.path.join(project_folder, "report.json")
    lighthouse_command = [batch_file_path, output_path]

    # Run the Lighthouse analysis
    try:
        result = subprocess.run(lighthouse_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Error running Lighthouse:", result.stderr.decode("utf-8"))
    except Exception as e:
        print("Error:", e)


def get_lighthouse_report(project_folder):
    # Define the path to the Lighthouse report
    report_path = os.path.join(project_folder, "report.json")

    # Load and return the report
    with open(report_path, "r", encoding="utf-8") as file:
        report = json.load(file)
    return report


def calculate_total_score(report):
    # Get the scores from the Lighthouse report
    performance_score = report['categories']['performance']['score']
    best_practices_score = report['categories']['best-practices']['score']
    accessibility_score = report['categories']['accessibility']['score']
    seo_score = report['categories']['seo']['score']

    # Calculate and return the total score
    total_score = (
        performance_score * 0.3 +
        best_practices_score * 0.4 +
        accessibility_score * 0.15 +
        seo_score * 0.15
   
    )
    return total_score

def create_and_test_project(project_num, user_prompt):
    # For each file type, generate and save the code
    for file_type in ["html", "css", "js"]:
        create_file(file_type, project_num, user_prompt)

    # Define the project folder
    project_folder = os.path.abspath(f'Versions/V{project_num}')

    # Start the server
    server = subprocess.Popen(['python', '-m', 'http.server', '--bind', '127.0.0.1', '8080'], cwd=project_folder)
    time.sleep(2)

    # Run Lighthouse on the project
    run_lighthouse(project_folder)

    # Stop the server
    server.terminate()
    server.wait()

    # Get the Lighthouse report and calculate the total score
    report = get_lighthouse_report(project_folder)
    total_score = calculate_total_score(report)
    return total_score, project_num
if __name__ == "__main__":
    # Set the OpenAI API key and prompt the user for the project details
    user_prompt = input("Enter your prompt: ")
    num_projects = 4

    scores = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # For each project, create, test, and score it
        futures = [executor.submit(create_and_test_project, i, user_prompt) for i in range(1, num_projects + 1)]

        for future in concurrent.futures.as_completed(futures):
            score, project_num = future.result()
            scores.append((score, project_num))

    # Determine and print the best version
    best_version_score, best_version_index = max(scores, key=lambda x: x[0])
    print(f"The best version is: todo{best_version_index} with a total score of {best_version_score}")