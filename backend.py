import os
from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

load_dotenv()

# Document Intelligence: Extract text from uploaded file
def extract_text_from_file(file):
    endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")

    document_client = DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    poller = document_client.begin_analyze_document("prebuilt-read", document=file)
    result = poller.result()

    extracted_text = "\n".join([line.content for page in result.pages for line in page.lines])
    return extracted_text


# Foundry Agent: Analyze resume + JD via Azure Agent
def analyze_resume_with_agent(resume_text, jd_text):
    project_endpoint = os.getenv("AZURE_FOUNDRY_AGENT_ENDPOINT")

    # 1. Create Foundry client
    project = AIProjectClient(
        credential=DefaultAzureCredential(),
        endpoint=project_endpoint
    )

    # 2. Load Agent
    agent = project.agents.get_agent("asst_f4fDXIXxFb18zbknINB4PDJN")

    # 3. Create a new thread (each session should have one)
    thread = project.agents.threads.create()

    # 4. Create message (send both Resume + JD as input)
    user_message = f"""Analyze the resume and job description below:

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {jd_text}

    Provide a match summary, skill comparison, and suitability score out of 100."""

    project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # 5. Trigger the run
    run = project.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id
    )

    # 6. Handle errors or collect output
    if run.status == "failed":
        return {"error": f"Agent run failed: {run.last_error}"}
    
    # 7. Get response messages
    messages = project.agents.messages.list(
        thread_id=thread.id,
        order=ListSortOrder.ASCENDING
    )

    responses = []
    for message in messages:
        if message.text_messages:
            responses.append({
                "role": message.role,
                "text": message.text_messages[-1].text.value
            })

    return responses
