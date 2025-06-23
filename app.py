import streamlit as st
from streamlit_chat import message
import os
from openai import AzureOpenAI
import json
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from dotenv import load_dotenv

load_dotenv()
# Get user input for AOAI endpoint, API key, API version, and deployment name
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
apikey = os.getenv('AZURE_OPENAI_KEY')
apiversion = os.getenv('AZ_OPENAI_API_VERSION')

# Authenticate using AzureKeyCredential
credential = AzureKeyCredential(apikey)

# Create OpenAI client
client = AzureOpenAI(
  azure_endpoint = endpoint, 
  api_key=apikey,  
  api_version=apiversion
)

client2 = CognitiveServicesManagementClient(
    credential=DefaultAzureCredential(),
    subscription_id=os.getenv('SUBSCRIPTION_ID'),
)

results = client2.deployments.list(
    resource_group_name=os.getenv('RESOURCE_GROUP_NAME'),
    account_name=os.getenv('AOAI_ACCOUNT_NAME'),
)

# List deployments
#deployments = client2.list_deployments()
deployments = []
for item in results:
    deployments.append(item.name)
    #print(item.name)

model = st.selectbox(
    'Select Model Deployment:',
    deployments
) 


# Set up the default prompt for the AI assistant
default_prompt = """
You are an AI assistant  that helps users write concise\
 reports on sources provided according to a user query.\
 You will provide reasoning for your summaries and deductions by\
 describing your thought process. You will highlight any conflicting\
 information between or within sources. Greet the user by asking\
 what they'd like to investigate.
"""

# Get the system prompt from the sidebar
system_prompt = st.sidebar.text_area("System Prompt", default_prompt, height=200)

# Define the seed message for the conversation
seed_message = {"role": "system", "content": system_prompt}

# Session management
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "messages" not in st.session_state:
    st.session_state["messages"] = [seed_message]
if "model_name" not in st.session_state:
    st.session_state["model_name"] = []
if "cost" not in st.session_state:
    st.session_state["cost"] = []
if "total_tokens" not in st.session_state:
    st.session_state["total_tokens"] = []
if "total_cost" not in st.session_state:
    st.session_state["total_cost"] = 0.0

# Display total cost of conversation in sidebar
counter_placeholder = st.sidebar.empty()
counter_placeholder.write(
    f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}"
)


# Clear conversation button
clear_button = st.sidebar.button("Clear Conversation", key="clear")
if clear_button:
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["messages"] = [seed_message]
    st.session_state["number_tokens"] = []
    st.session_state["model_name"] = []
    st.session_state["cost"] = []
    st.session_state["total_cost"] = 0.0
    st.session_state["total_tokens"] = []
    counter_placeholder.write(
        f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}"
    )

# Download conversation button
download_conversation_button = st.sidebar.download_button(
    "Download Conversation",
    data=json.dumps(st.session_state["messages"]),
    file_name=f"conversation.json",
    mime="text/json",
)

# Generate response based on user input
def generate_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    completion = client.chat.completions.create(
        model = model,
        messages=st.session_state["messages"],
    )
    response = completion.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": response})
    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

# Main app title
st.title("ChatGPT Demo")

# Container for chat history
response_container = st.container()

# Container for text box
container = st.container()

# User input form
with container:
    with st.form(key="my_form", clear_on_submit=True):
        user_input = st.text_area("You:", key="input", height=100)
        submit_button = st.form_submit_button(label="Send")
    if submit_button and user_input:
        output, total_tokens, prompt_tokens, completion_tokens = generate_response(
            user_input
        )
        st.session_state["past"].append(user_input)
        st.session_state["generated"].append(output)
        st.session_state["model_name"].append(model)
        st.session_state["total_tokens"].append(total_tokens)
        cost = total_tokens * 0.001625 / 1000
        st.session_state["cost"].append(cost)
        st.session_state["total_cost"] += cost

# Display conversation history
if st.session_state["generated"]:
    with response_container:
        for i in range(len(st.session_state["generated"])):
            message(
                st.session_state["past"][i],
                is_user=True,
                key=str(i) + "_user",
                avatar_style="shapes",
            )
            message(
                st.session_state["generated"][i], key=str(i), avatar_style="identicon"
            )
        counter_placeholder.write(
            f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}"
        )
