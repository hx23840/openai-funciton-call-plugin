import requests
import openai
import json


def send_request(method, url, data=None, params=None):
    response = requests.request(method, url, json=data, params=params)
    response.raise_for_status()
    return response.json()


# Base URL
BASE_URL = "https://plugin.askyourpdf.com"  # 请将这个URL替换为实际的API URL


def download_pdf(url):
    path = "/api/download_pdf"
    full_url = BASE_URL + path
    params = {"url": url}
    response = send_request("POST", full_url, params=params)
    return response


def perform_query(doc_id, query):
    path = "/query"
    full_url = BASE_URL + path
    data = {"doc_id": doc_id, "query": query}
    response = send_request("POST", full_url, data=data)
    return response


openai.api_key = "YOUR_API_KEY"


# Step 1, send model the user query and what functions it has access to
def run_conversation():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "user", "content": "I want to upload pdf use this url:https://arxiv.org/pdf/1706.03762.pdf"}],
        functions=[
            {
                "name": "download_pdf",
                "description": "upload a pdf",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The pdf url"},
                    },
                    "required": ["url"],
                },
            }
        ],
        function_call="auto",
    )

    message = response["choices"][0]["message"]

    # Step 2, check if the model wants to call a function
    if message.get("function_call"):
        # Step 3, call the function
        function_call = message.get('function_call')
        arguments = json.loads(function_call.get('arguments'))
        function_response = download_pdf(url=arguments.get("url"))

        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": "I want to search content with pdf, The query content is What is the "
                                            "Self-attention?,The doc id is " + function_response["docId"]}
            ],
            functions=[
                {
                    "name": "perform_query",
                    "description": "search content with a pdf",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_id": {"type": "string", "description": "The doc id"},
                            "query": {"type": "string", "description": "The query content"},
                        },
                        "required": ["doc_id", "query"],
                    },
                }
            ],
            function_call="auto",
        )

        message = second_response["choices"][0]["message"]
        if message.get("function_call"):
            # Step 3, call the function
            function_call = message.get('function_call')
            arguments = json.loads(function_call.get('arguments'))
            function_response = perform_query(doc_id=arguments.get("doc_id"), query=arguments.get("query"))

            return function_response


print(run_conversation())
