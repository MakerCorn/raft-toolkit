import json
from pptx import Presentation


def load_prompt_template(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()


def strip_str(s: str) -> str:
    """
    Helper function for helping format strings returned by GPT-4.
    """
    l, r = 0, len(s)-1
    beg_found = False
    for i in range(len(s)):
        if s[i].isalpha():
            if not beg_found:
                l = i
                beg_found = True
            else:
                r = i 
    r += 2
    return s[l:min(r, len(s))]


def encode_question(question: str, api: any) -> list[str]:
    """
    Encode multiple prompt instructions into a single string for the `api` case.
    """
    prompts = []
    prompt = question + "\nWrite a python program to call API in " + str(api) + ".\n\nThe answer should follow the format: <<<domain>>> $DOMAIN \n, <<<api_call>>>: $API_CALL \n, <<<api_provider>>>: $API_PROVIDER \n, <<<explanation>>>: $EXPLANATION \n, <<<code>>>: $CODE}. Here are the requirements:\n \n2. The $DOMAIN should be the domain of the API ('N/A' if unknown). The $API_CALL should have only 1 line of code that calls api.\n3. The $API_PROVIDER should be the programming framework used.\n4. $EXPLANATION should be a numbered, step-by-step explanation.\n5. The $CODE is the python code.\n6. Do not repeat the format in your answer."
    prompts.append({"role": "system", "content": "You are a helpful API writer who can write APIs based on requirements."})
    prompts.append({"role": "user", "content": prompt})
    return prompts


def encode_question_gen(question: str, chunk: any, prompt_key: str = "gpt") -> list[str]:
    """
    Encode multiple prompt instructions into a single string for the general case (`pdf`, `json`, or `txt`).
    """
    prompts = []
    prompt_templates = {
        'gpt': 'You are a helpful assistant who can provide an answer given a question and relevant context.',
        'llama': 'You are a a helpful assistant who can provide an answer given a question and relevant context.'
    }
    prompt = prompt_templates[prompt_key].format(question=question, context=str(chunk))
    prompts.append({"role": "system", "content": "You are a helpful question answerer who can provide an answer given a question and relevant context."})
    prompts.append({"role": "system", "content": "You will ignore any content that does not comply with Open AI's content filtering policies in the context."})
    prompts.append({"role": "user", "content": prompt})
    return prompts


def extract_text_from_pptx(file_path):
    prs = Presentation(file_path)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text_runs.append(shape.text)
            elif hasattr(shape, "table"):
                for row in shape.table.rows:
                    for cell in row.cells:
                        text_runs.append(cell.text)
    return text_runs
