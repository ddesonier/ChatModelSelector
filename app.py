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

# Try multiple environment variable names for API version and provide fallback
apiversion = os.getenv('AZURE_OPENAI_API_VERSION') or os.getenv('OPENAI_API_VERSION') or '2024-06-01'

# Get Azure resource details
subscription_id = os.getenv('SUBSCRIPTION_ID')

resource_group_name = os.getenv('RESOURCE_GROUP_NAME')

aoai_account_name = os.getenv('AOAI_ACCOUNT_NAME')


print(f"Endpoint: {endpoint}")
print(f"APIKey: {apikey}")
print(f"API Version: {apiversion}")
print(f"Subscription ID: {subscription_id}")
print(f"Resource Group Name: {resource_group_name}")
print(f"AOAI Account Name: {aoai_account_name}")

# Display configuration in Streamlit for debugging
with st.expander("🔧 Current Configuration (for debugging)", expanded=False):
    st.write("**Environment Variables Loaded:**")
    st.write(f"- AZURE_OPENAI_ENDPOINT: `{endpoint or 'NOT SET'}`")
    st.write(f"- AZURE_OPENAI_KEY: `{'***' + (apikey[-4:] if apikey else 'NOT SET')}`")
    st.write(f"- AZURE_OPENAI_API_VERSION: `{apiversion}`")
    st.write(f"- SUBSCRIPTION_ID: `{subscription_id or 'NOT SET'}`")
    st.write(f"- RESOURCE_GROUP_NAME: `{resource_group_name or 'NOT SET'}`")
    st.write(f"- AOAI_ACCOUNT_NAME: `{aoai_account_name or 'NOT SET'}`")
    
    if all([endpoint, apikey, subscription_id, resource_group_name, aoai_account_name]):
        st.success("✅ All required environment variables are set")
    else:
        st.error("❌ Some required environment variables are missing")

# Validate required parameters
required_vars = {
    'AZURE_OPENAI_ENDPOINT': endpoint,
    'AZURE_OPENAI_KEY': apikey,
    'SUBSCRIPTION_ID': subscription_id,
    'RESOURCE_GROUP_NAME': resource_group_name,
    'AOAI_ACCOUNT_NAME': aoai_account_name
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    st.error("Please check your .env file and ensure all required variables are set.")
    st.stop()

# Authenticate using AzureKeyCredential
credential = AzureKeyCredential(apikey)

# Create OpenAI client with error handling
try:
    client = AzureOpenAI(
        azure_endpoint=endpoint, 
        api_key=apikey,  
        api_version=apiversion
    )
except Exception as e:
    st.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
    st.error("Please verify your Azure OpenAI endpoint and API key.")
    st.stop()

# Create Cognitive Services client and list deployments with error handling
try:
    print("Attempting to create Cognitive Services client...")
    client2 = CognitiveServicesManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=subscription_id,
    )
    print("Cognitive Services client created successfully")
    
    print(f"Attempting to list deployments for resource: {aoai_account_name} in RG: {resource_group_name}")
    results = client2.deployments.list(
        resource_group_name=resource_group_name,
        account_name=aoai_account_name,
    )
    print("Deployment list call successful")
    
    # List deployments
    deployments = []
    deployment_count = 0
    for item in results:
        deployments.append(item.name)
        deployment_count += 1
        print(f"Found deployment: {item.name}")
    
    print(f"Total deployments found: {deployment_count}")
        
except Exception as e:
    print(f"Exception occurred: {type(e).__name__}: {str(e)}")
    st.error(f"Failed to retrieve deployments: {str(e)}")
    
    if "ResourceNotFound" in str(e):
        st.error(f"❌ Azure OpenAI resource '{aoai_account_name}' not found in resource group '{resource_group_name}'.")
        st.error("Please verify the following in your .env file:")
        st.error("- RESOURCE_GROUP_NAME: The correct resource group name")
        st.error("- AOAI_ACCOUNT_NAME: The correct Azure OpenAI account name")
        st.error("- SUBSCRIPTION_ID: The correct subscription ID")
        
        # Provide helpful commands
        st.info("💡 Try these Azure CLI commands to find your resources:")
        st.code("""# List all Azure OpenAI resources in your subscription
az cognitiveservices account list --query "[?kind=='OpenAI'].{name:name, resourceGroup:resourceGroup, location:location}" -o table

# List resource groups
az group list --query "[].name" -o table

# Check current subscription
az account show --query "{name:name, id:id}" -o table""")
        
    elif "AuthenticationFailed" in str(e) or "Unauthorized" in str(e):
        st.error("❌ Authentication failed. Please check your Azure credentials.")
        st.info("💡 Try running: `az login` to authenticate with Azure")
        
    elif "Forbidden" in str(e):
        st.error("❌ Access denied. You don't have permission to access this resource.")
        st.info("💡 You need at least 'Cognitive Services User' role on the Azure OpenAI resource")
        st.info("Contact your Azure administrator to grant proper permissions")
        
    else:
        st.error("❌ Please check your Azure credentials and permissions.")
        st.info("💡 Common solutions:")
        st.info("- Run `az login` to authenticate")
        st.info("- Verify you're in the correct subscription: `az account show`")
        st.info("- Check if the resource exists: `az cognitiveservices account show --name [resource-name] --resource-group [rg-name]`")
    
    deployments = []  # Fallback to empty list

# Check if deployments are available
if not deployments:
    st.warning("⚠️ No deployments found or unable to retrieve deployments.")
    
    st.info("🔍 **Quick Diagnostic Steps:**")
    st.info("1. **Check Console Output**: Look at the terminal/console where you ran `streamlit run app.py` for detailed error messages")
    st.info("2. **Verify Resource Exists**: Check if your Azure OpenAI resource actually exists in the Azure portal")
    st.info("3. **Check Deployments**: Ensure your Azure OpenAI resource has model deployments created")
    
    st.info("🛠️ **How to Fix:**")
    
    with st.expander("📋 Option 1: Use the Discovery Script (Recommended)"):
        st.code("""# Run this in PowerShell
.\\discover-azure-resources.ps1""")
        st.write("This will automatically find your Azure OpenAI resources and show the correct values to use.")
    
    with st.expander("🔧 Option 2: Manual Verification"):
        st.code("""# Check if you're logged in to Azure
az account show

# Find your Azure OpenAI resources
az cognitiveservices account list --query "[?kind=='OpenAI']" -o table

# Check deployments for a specific resource
az cognitiveservices account deployment list --name YOUR_RESOURCE_NAME --resource-group YOUR_RG_NAME""")
    
    with st.expander("➕ Option 3: Create New Deployment"):
        st.write("If your resource exists but has no deployments:")
        st.write("1. Go to Azure Portal → Your OpenAI Resource → Model deployments")
        st.write("2. Click 'Create new deployment'")
        st.write("3. Select a model (e.g., gpt-35-turbo, gpt-4) and give it a name")
        st.write("4. Deploy the model")
    
    st.error("🛑 **App stopped** - Please resolve the deployment issue above and refresh the page.")
    st.stop()

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
    file_name="conversation.json",
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
