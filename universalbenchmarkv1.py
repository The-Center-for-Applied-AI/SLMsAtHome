import ollama
import pandas as pd
import shutil
import string
import subprocess
import sys

base_model = "qwen2.5:0.5b"

if shutil.which("ollama") is None:
    print(f'Ollama is not installed or not in PATH. Aborting.')
    sys.exit(0)

user_warning = input(f'WARNING: Running this benchmark will close all Ollama models to free up memory for the benchmark. Continue? (Y/N): ')
print()
if user_warning.lower() != "y":
    print("Aborting.")
    sys.exit(0)

user_input = input(f'Type your Ollama models and separate them with a space: ')
user_input = user_input.split()
if len(user_input) > 0:
    user_input = list(set(user_input))
else:
    print(f'No models were specified. Aborting.')
    sys.exit(0)

try:
    ollama_list_full = ollama.list()
except Exception:
    print(f'Ollama may not be running. Aborting.')
    sys.exit(0)
ollama_list = []
for model_atr in ollama_list_full["models"]:
    ollama_list.append(model_atr["model"])

originally_had = False
if base_model.lower() not in ollama_list:
    print(f'Base model not found ({base_model}). Installing now.')
    try:
        ollama.pull(base_model)
    except Exception:
        print(f'Something went wrong and the base model could not be installed. Aborting.')
        sys.exit(0)
    user_answer = input(f'Do you want to keep the base model? (Y/N): ')
    if user_answer.lower() == "y":
        originally_had = True
else:
    print(f'Base model found ({base_model})')
    originally_had = True
print()

model_list = []
for model_name in user_input:
    user_answer = ""
    if model_name not in ollama_list:
        if f'{model_name}:latest' in ollama_list:
            model_list.append(f'{model_name}:latest')
            continue
        user_answer = input(f'Model \"{model_name}\" not in your Ollama list of models. Would you like to install it? (Y/N): ')
        if user_answer.lower() == "y":
            print(f'Installing model \"{model_name}\"')
            try:
                ollama.pull(model_name)
                if len(model_name.split(":")) == 1:
                    model_list.append(f'{model_name}:latest')
                else:
                    model_list.append(model_name)
            except Exception:
                print(f'Could not install model \"{model_name}\". Did you spell the model name correctly? (Ollama model names are case-sensitive)')
                print()
        else:
            print(f'Not installing model \"{model_name}\"')
            print()
    else:
        model_list.append(model_name)

ollama_dict = {}
ollama_list_full = ollama.list()
for ollama_model in ollama_list_full["models"]:
    if ollama_model["model"] in model_list:
        try:
            ollama_dict[ollama_model["model"]] = {"name": ollama_model["model"],
                                                 "disk_size": ollama_model["size"],
                                                 "param_size": ollama_model["details"]["parameter_size"],
                                                 "quant": ollama_model["details"]["quantization_level"],
                                                 "hash": ollama_model["digest"]}
        except Exception:
            print(f'Something went wrong with {ollama_model["model"]}. Excluding model and moving on.')
            print()
            continue

# Set up list of query questions
queries = [
    "Pick the healthiest food from one of the following choices as just saying a single word: ice-cream, broccoli, donuts, ramen-noodles. Do not add anything else to your response besides your single word answer.",
    "Who was the first president of the United States? Answer with just the name.",
    "Explain in exactly three sentences who died and why it sparked world war 1.",
    "What is 2+2? Answer with just a single number.",
    "Write Python code that prints \"hello world\" and do not add anything else to your response including any additional words, phrases, sentences, or paragraphs or any special formatting including codeblocks or markdown. I only want raw text as your code output and nothing else.",
    "What is the square root of 16? Answer with just a single number.",
    "What is the capital city of France? Answer with just the city's name.",
    "If a is greater than b, and b is greater than c, which one is the smallest? Answer with just a single letter (a, b, or c).",
    "How many Rs are in the word \"strawberry\"? Answer with the numerical version of the number (1) not the spelling (one).",
    "Spell the word \"accommodate\". Do not add anything else to your response including any additional words or phrases.",
    "Earth is the third planet from the sun: true or false? Answer with just \"true\" or \"false\".",
    "Complete the following sentence with just your response. Do not put your response in a sentence, and do not repeat the prompt in your answer: The capital of the United States is...",
    "If I was born on Oct 1, 2000, what is my age as of August 27, 2024? Answer with just \"NUMERICAL_AGE years old\".",
    "Recite pi up to 10 decimal points. Do not add anything else to your response including any additional words or phrases.",
    "Who painted the Mona Lisa? Answer with just the name of the painter and nothing else.",
    "Identify the verb in the following sentence: \"she runs fast.\" Answer with just the verb.",
    "What comes next in the series: a, b, c, d? Answer with just a single letter.",
    "What is the atomic number of hydrogen? Answer with just a single number.",
    "Complete the following analogy: Dog is to Bark as Cat is to... Answer with just a single word.",
    "If a triangle has sides of 3, 4, and 5, what is the area of the triangle? Answer with just a single number.",
    "Translate 'hello' into Spanish. Answer with just a single word.",
    "What is the boiling point of water in degrees Celsius? Answer with just a single number.",
    "Who wrote the play 'Romeo and Juliet'? Answer with just the name of the author and nothing else.",
    "How many continents are there on Earth? Answer with just a single number.",
    "What is the derivative of x^2 with respect to x? Answer with just a mathematical expression and nothing else.",
    "Which planet is known as the 'Red Planet'? Answer with just the planet's name.",
    "What is the 5th Fibonacci number if the sequence starts with 0 and 1? Answer with just a single number.",
    "Convert 100 degrees Fahrenheit to Celsius. Answer with just a single number rounded to the nearest whole number.",
    "If you have 5 apples and eat 2, how many do you have left? Answer with just a single number.",
    "Who is the author of the 'Harry Potter' series? Answer with just the author's name.",
    "Spell the word 'pharaoh'. Do not add anything else to your response.",
    "What is the currency used in Japan? Answer with just the name of the currency.",
    "What is the chemical symbol for gold? Answer with just the symbol.",
    "Who discovered penicillin? Answer with just the scientist's name.",
    "What is the capital city of Canada? Answer with just the city's name.",
    "How many vowels are in the word \"education\"? Answer with just a single number.",
    "What is the largest planet in the solar system? Answer with just the planet's name.",
    "What is 7 multiplied by 8? Answer with just a single number.",
    "What is the smallest prime number? Answer with just a single number.",
    "What is the official language of Brazil? Answer with just a single word.",
    "Which element has the chemical symbol 'O'? Answer with just the element's name.",
    "If today is Monday, what day will it be in 5 days? Answer with just the day's name.",
    "Who wrote 'The Theory of Relativity'? Answer with just the scientist's name.",
    "What is the capital of Italy? Answer with just the city's name.",
    "How many legs does a spider have? Answer with just a single number.",
    "What is the currency of the United Kingdom? Answer with just the name of the currency.",
    "Which ocean is the largest by surface area? Answer with just the ocean's name.",
    "How many sides does a hexagon have? Answer with just a single number.",
    "What is the speed of light in a vacuum in meters per second (rounded to the nearest whole number)? Answer with just a single number.",
    "Who is known as the 'Father of Computers'? Answer with just the name."
]

# Set up list of answers
# Answer: the answer to the query.
# Length: How long the response should be.
# Sentences: States whether the response should be sentence(s) or word(s)
# Partial: States whether a model should get partial credit if their part of the answer is somewhere in the response
# Normalize: Remove all punctuation for normalization. Would be false if looking for specific decimal numbers
answers = [
    {"answer": "broccoli", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "george washington", "length": 2, "sentences": False, "partial": True, "normalize": True},
    {"answer": "franz ferdinand", "length": 3, "sentences": True, "partial": True, "normalize": False},
    {"answer": "4", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "print(\"hello world\")", "length": 2, "sentences": False, "partial": True, "normalize": False},
    {"answer": "4", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "paris", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "c", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "3", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "accommodate", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "true", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "washington dc", "length": 2, "sentences": False, "partial": True, "normalize": True},
    {"answer": "23 years old", "length": 3, "sentences": False, "partial": True, "normalize": True},
    {"answer": "3.1415926535", "length": 1, "sentences": False, "partial": False, "normalize": False},
    {"answer": "leonardo da vinci", "length": 3, "sentences": False, "partial": True, "normalize": True},
    {"answer": "runs", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "e", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "1", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "meow", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "6", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "hola", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "100", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "william shakespeare", "length": 2, "sentences": False, "partial": True, "normalize": True},
    {"answer": "7", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "2x", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "mars", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "3", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "38", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "3", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "jk rowling", "length": 2, "sentences": False, "partial": True, "normalize": True},
    {"answer": "pharaoh", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "yen", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "au", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "alexander fleming", "length": 2, "sentences": False, "partial": True, "normalize": True},
    {"answer": "ottawa", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "5", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "jupiter", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "56", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "2", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "portuguese", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "oxygen", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "saturday", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "albert einstein", "length": 2, "sentences": False, "partial": True, "normalize": True},
    {"answer": "rome", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "8", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "pound", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "pacific", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "6", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "299792458", "length": 1, "sentences": False, "partial": False, "normalize": True},
    {"answer": "charles babbage", "length": 2, "sentences": False, "partial": True, "normalize": True}
]

# Kill all models to avoid interference and to speed up memory
def kill_models():
    try:
        for model in ollama.ps()['models']:
            # Kill model for RAM
            subprocess.run(['ollama', 'stop', model['model']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print(f'Could not close models to free memory. Aborting.')
        sys.exit(0)

# Get the memory usage of the language model
def get_memory_usage(model_identity):
    try:
        model_ps_list = ollama.ps()
        for model in model_ps_list['models']:
            if model['name'].lower() == model_identity.lower() and model['size']:
                return model['size'] / (1024 ** 2)
        print(f'Could not get memory usage of Ollama model. Aborting.')
        sys.exit(0)
    except Exception:
        print(f'Could not get memory usage of Ollama model. Aborting.')
        sys.exit(0)

# Get the percent difference between two numbers to normalize TPS
def get_percent_diff(num1, num2):
    return ((num1 - num2) / ((num1 + num2) / 2)) * 100

# Benchmark the listed model
def benchmark_model(model, is_base):
    return_dict = {}
    outputs = []
    prompt_tps = 0
    eval_tps = 0
    mem_usage = 0

    kill_models()

    # Loop each query to ask the model
    for query in range(len(queries)):
        try:
            model_response = ollama.generate(model=model, prompt=queries[query])
        except Exception:
            print(f'Could not prompt model {model}. Aborting.')
            sys.exit(0)

        # Get model memory
        try:
            mem_usage += get_memory_usage(model)
        except Exception:
            print(f'Could not get memory usage of Ollama model. Aborting.')
            sys.exit(0)

        # Get model output
        try:
            outputs.append(model_response['response'])
        except Exception:
            outputs.append("")

        # Get prompt eval rate of the model
        try:
            prompt_tps += (model_response["prompt_eval_count"] / (model_response["prompt_eval_duration"] / 1e9))
        except Exception:
            prompt_tps += -1

        # Get eval rate of the model
        try:
            eval_tps += (model_response["eval_count"] / (model_response["eval_duration"] / 1e9))
        except Exception:
            eval_tps += -1

        if is_base:
            print(f'Base Model calibration: {query+1}/{len(queries)}')
        else:
            print(f'{model} benchmark: {query+1}/{len(queries)}')
    print()

    # Kill models for RAM
    kill_models()

    correctness_list = []
    obedience_list = []
    for pointer in range(len(outputs)):
        correctness = 0

        length = answers[pointer]["length"]
        sentences = answers[pointer]["sentences"]
        partial = answers[pointer]["partial"]
        normalize = answers[pointer]["normalize"]

        answer = answers[pointer]["answer"].strip().lower()

        output = outputs[pointer].strip().lower().replace("\n", " ").replace("'", "\"").replace(",", "")

        # Remove Punctuation
        if normalize:
            output = output.translate(str.maketrans('', '', string.punctuation))

        # Obedience
        if sentences:
            marks = [".", "!", "?"]
            mark_count = 0
            for mark in marks:
                mark_count += output.count(mark)
            obedience = (output != "" and mark_count == length)
        else:
            obedience = (output != "" and len(output.split()) == length)

        # Correctness
        if (" " + answer + " ") in (" " + output + " "):
            correctness = 1
        if partial and correctness != 1:
            total_points = 0
            partial_point = 1 / len(answer.split())
            for word in answer.split():
                split_output = output.split()
                if word in split_output:
                    total_points += partial_point
            correctness = total_points

        correctness_list.append(correctness)
        obedience_list.append(obedience)

    return_dict["model"] = model
    if not is_base:
        return_dict["quant"] = ollama_dict[model]["quant"]
        if ollama_dict[model]["param_size"][-1] == "M":
            return_dict["param_size"] = float(ollama_dict[model]["param_size"][:-1]) / 1000
        elif ollama_dict[model]["param_size"][-1] == "B":
            return_dict["param_size"] = float(ollama_dict[model]["param_size"][:-1])
        return_dict["disk_size"] = ollama_dict[model]["disk_size"] / 1000000
        return_dict["mem_use"] = (mem_usage / len(outputs))
    return_dict["prompt_tps"] = (prompt_tps / len(outputs))
    return_dict["eval_tps"] = (eval_tps / len(outputs))
    return_dict["obedience"] = (sum(obedience_list) / len(obedience_list))
    return_dict["correctness"] = (sum(correctness_list) / len(correctness_list))
    if not is_base:
        return_dict["hash"] = ollama_dict[model]["hash"]
    return return_dict

if len(ollama_dict) == 0:
    print(f'No models to benchmark. Aborting.')
    sys.exit(0)
else:
    print(f'Benchmarking the following models:')
    for model_listed in ollama_dict:
        print(model_listed)
    print()

# Benchmark the base model
base_model_dict = benchmark_model(base_model, 1)

# Delete the base model if the user does not want to keep it
if not originally_had:
    ollama.delete(base_model)

# Benchmark each listed model
model_dict = {}
for model_listed in ollama_dict:
    model_dict[model_listed] = benchmark_model(model_listed, 0)

# Analyze each result
for i in model_dict:
    # If what the user benchmarked is the same as the base model, zero-out the prompt and eval TPS
    if i == base_model:
        model_dict[i]["prompt_tps"] = 0
        model_dict[i]["eval_tps"] = 0
    # Get the percent difference between other model and base model in terms of TPS
    else:
        if model_dict[i]["prompt_tps"] == -1:
            model_dict[i]["prompt_tps"] = -200
        else:
            model_dict[i]["prompt_tps"] = get_percent_diff(model_dict[i]["prompt_tps"], base_model_dict["prompt_tps"])
        if model_dict[i]["eval_tps"] == -1:
            model_dict[i]["eval_tps"] = -200
        else:
            model_dict[i]["eval_tps"] = get_percent_diff(model_dict[i]["eval_tps"], base_model_dict["eval_tps"])
    # Don't make obedience and correctness decimals
    model_dict[i]["obedience"] = model_dict[i]["obedience"] * 100
    model_dict[i]["correctness"] = model_dict[i]["correctness"] * 100

# Prepare for output in Pandas DataFrame
data = []
for i in model_dict:
    data.append(model_dict[i])

# Set Pandas display options
pd.set_option('display.max_rows', None)  # Show all rows
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_colwidth', None)  # Don't truncate column content
pd.set_option('display.width', None)  # Auto-adjust display width

# Make a Pandas DataFrame with the data
df = pd.DataFrame(data)
df.columns = ["Model", "Quantization", "Param Size (B)", "Disk Size (MB)", "Mem Usage (MB)", "Prompt TPS (% Diff from base)", "Eval TPS (% Diff from base)", "Obedience %", "Correctness %", "Hash"]
df.drop(columns=["Hash"], inplace=True)
print(df)
print()

# Catch-all exit
sys.exit(0)