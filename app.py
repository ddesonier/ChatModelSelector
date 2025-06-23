import streamlit as st
from streamlit_chat import message
import os
from openai import AzureOpenAI
import json
from azure.core.credentials import AzureKeyCredential
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
    
    # Entra ID authentication options
    st.write("**Entra ID Authentication Options:**")
    
    use_managed_identity = os.getenv('USE_MANAGED_IDENTITY', 'false').lower() == 'true'
    sp_client_id = os.getenv('AZURE_CLIENT_ID')
    sp_client_secret = os.getenv('AZURE_CLIENT_SECRET')
    sp_tenant_id = os.getenv('AZURE_TENANT_ID')
    certificate_path = os.getenv('AZURE_CLIENT_CERTIFICATE_PATH')
    use_interactive = os.getenv('USE_INTERACTIVE_AUTH', 'false').lower() == 'true'
    use_device_code = os.getenv('USE_DEVICE_CODE', 'false').lower() == 'true'
    
    st.write(f"- 🎯 Managed Identity: `{'ENABLED' if use_managed_identity else 'DISABLED'}`")
    st.write(f"- 🔑 Service Principal (Secret): `{'CONFIGURED' if (sp_client_id and sp_client_secret and sp_tenant_id) else 'NOT CONFIGURED'}`")
    st.write(f"- 📜 Service Principal (Certificate): `{'CONFIGURED' if (sp_client_id and sp_tenant_id and certificate_path) else 'NOT CONFIGURED'}`")
    st.write(f"- 🌐 Interactive Browser: `{'ENABLED' if use_interactive else 'DISABLED'}`")
    st.write(f"- 📱 Device Code: `{'ENABLED' if use_device_code else 'DISABLED'}`")
    st.write("- 🖥️ Azure CLI: Available for fallback")
    st.write("- 💻 VS Code: Available for fallback")
    
    # Show authentication status
    auth_methods_available = 0
    auth_methods_configured = []
    
    if use_managed_identity:
        auth_methods_available += 1
        auth_methods_configured.append("🎯 Managed Identity")
    if sp_client_id and sp_client_secret and sp_tenant_id:
        auth_methods_available += 1
        auth_methods_configured.append("🔑 Service Principal (Secret)")
    if sp_client_id and sp_tenant_id and certificate_path:
        auth_methods_available += 1
        auth_methods_configured.append("📜 Service Principal (Certificate)")
    if use_interactive:
        auth_methods_available += 1
        auth_methods_configured.append("🌐 Interactive Browser")
    if use_device_code:
        auth_methods_available += 1
        auth_methods_configured.append("📱 Device Code")
        
    # Always available fallback methods
    fallback_methods = ["🖥️ Azure CLI", "💻 VS Code", "🔄 DefaultAzureCredential"]
        
    if auth_methods_available > 0:
        st.success(f"✅ {auth_methods_available} Entra ID authentication method(s) configured")
        for method in auth_methods_configured:
            st.write(f"  • {method}")
        
        st.info("**Fallback methods available:**")
        for method in fallback_methods:
            st.write(f"  • {method}")
    else:
        st.warning("⚠️ No explicit Entra ID authentication methods configured")
        st.info("**Using fallback methods:**")
        for method in fallback_methods:
            st.write(f"  • {method}")
        st.info("💡 Configure at least one explicit method for better security and reliability")
        
        # Show helpful setup links
        with st.expander("🛠️ Quick Setup Options"):
            st.write("**For Azure-hosted applications:**")
            st.code("USE_MANAGED_IDENTITY=true")
            
            st.write("**For development:**")
            st.code("""USE_INTERACTIVE_AUTH=true
AZURE_CLIENT_ID=your-app-registration-id
AZURE_TENANT_ID=your-tenant-id""")
            
            st.write("**For CI/CD and containers:**")
            st.code("""AZURE_CLIENT_ID=your-service-principal-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_TENANT_ID=your-tenant-id""")
            
            st.write("**Quick setup scripts:**")
            st.code("""# Create Service Principal
.\\create-service-principal.ps1 -ServicePrincipalName 'ModelSelectorApp'

# Validate setup
.\\validate-entra-auth.ps1""")

    if all([endpoint, apikey, subscription_id, resource_group_name, aoai_account_name]):
        st.success("✅ All basic required environment variables are set")
    else:
        st.error("❌ Some basic required environment variables are missing")
        missing = []
        if not endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not apikey:
            missing.append("AZURE_OPENAI_KEY")
        if not subscription_id:
            missing.append("SUBSCRIPTION_ID")
        if not resource_group_name:
            missing.append("RESOURCE_GROUP_NAME")
        if not aoai_account_name:
            missing.append("AOAI_ACCOUNT_NAME")
        
        st.error(f"Missing: {', '.join(missing)}")
        st.info("💡 Run `.\discover-azure-resources.ps1` to find the correct values")
    
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

# Create Cognitive Services client with comprehensive Entra ID authentication
def create_azure_credential():
    """
    Create Azure credential using multiple Entra ID authentication methods.
    Prioritizes security best practices and supports various deployment scenarios.
    """
    print("🔐 Initializing Entra ID authentication...")
    
    # Method 1: Managed Identity (preferred for Azure-hosted resources)
    use_managed_identity = os.getenv('USE_MANAGED_IDENTITY', 'false').lower() == 'true'
    if use_managed_identity:
        print("🎯 Attempting Managed Identity authentication...")
        try:
            from azure.identity import ManagedIdentityCredential
            # Support both system-assigned and user-assigned managed identities
            client_id = os.getenv('AZURE_CLIENT_ID')  # For user-assigned MI
            if client_id:
                credential = ManagedIdentityCredential(client_id=client_id)
                print(f"✅ Using User-Assigned Managed Identity: {client_id}")
            else:
                credential = ManagedIdentityCredential()
                print("✅ Using System-Assigned Managed Identity")
            return credential
        except Exception as e:
            print(f"❌ Managed Identity failed: {e}")
    
    # Method 2: Service Principal (for CI/CD and container scenarios)
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    print("🔍 Service Principal credentials check:")
    print(f"  AZURE_CLIENT_ID: {'SET' if client_id else 'NOT SET'}")
    print(f"  AZURE_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'}")
    print(f"  AZURE_TENANT_ID: {'SET' if tenant_id else 'NOT SET'}")
    
    if client_id and client_secret and tenant_id:
        print("🔑 Using Service Principal (Client Secret) authentication...")
        try:
            from azure.identity import ClientSecretCredential
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            print("✅ Service Principal credential created successfully")
            return credential
        except Exception as e:
            print(f"❌ Service Principal authentication failed: {e}")
    
    # Method 3: Certificate-based Service Principal (more secure)
    certificate_path = os.getenv('AZURE_CLIENT_CERTIFICATE_PATH')
    if client_id and tenant_id and certificate_path:
        print("📜 Using Certificate-based Service Principal authentication...")
        try:
            from azure.identity import CertificateCredential
            credential = CertificateCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                certificate_path=certificate_path
            )
            print("✅ Certificate-based authentication configured")
            return credential
        except Exception as e:
            print(f"❌ Certificate authentication failed: {e}")
    
    # Method 4: Interactive Browser (for development/testing)
    use_interactive = os.getenv('USE_INTERACTIVE_AUTH', 'false').lower() == 'true'
    if use_interactive and client_id and tenant_id:
        print("🌐 Using Interactive Browser authentication...")
        try:
            from azure.identity import InteractiveBrowserCredential
            credential = InteractiveBrowserCredential(
                tenant_id=tenant_id,
                client_id=client_id
            )
            print("✅ Interactive browser authentication configured")
            return credential
        except Exception as e:
            print(f"❌ Interactive authentication failed: {e}")
    
    # Method 5: Device Code Flow (for headless environments)
    use_device_code = os.getenv('USE_DEVICE_CODE', 'false').lower() == 'true'
    if use_device_code and client_id and tenant_id:
        print("📱 Using Device Code authentication...")
        try:
            from azure.identity import DeviceCodeCredential
            credential = DeviceCodeCredential(
                tenant_id=tenant_id,
                client_id=client_id
            )
            print("✅ Device code authentication configured")
            return credential
        except Exception as e:
            print(f"❌ Device code authentication failed: {e}")
    
    # Method 6: Azure CLI (for local development) - Skip in Docker as it's not available
    try:
        # Check if we're in a container environment
        in_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'
        if not in_docker:
            print("🖥️ Attempting Azure CLI authentication...")
            from azure.identity import AzureCliCredential
            credential = AzureCliCredential()
            # Test the credential
            test_token = credential.get_token("https://management.azure.com/.default")
            if test_token:
                print("✅ Azure CLI authentication successful")
                return credential
        else:
            print("🐳 Skipping Azure CLI authentication (Docker environment)")
    except Exception as e:
        print(f"❌ Azure CLI authentication failed: {e}")
    
    # Fallback: DefaultAzureCredential (tries multiple methods automatically)
    print("🔄 Falling back to DefaultAzureCredential...")
    try:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        print("✅ DefaultAzureCredential configured")
        return credential
    except Exception as e:
        print(f"❌ DefaultAzureCredential failed: {e}")
        raise Exception("All authentication methods failed. Please check your Entra ID configuration.")

try:
    print("Attempting to create Cognitive Services client...")
    azure_credential = create_azure_credential()
    
    # Add timeout and retry configuration for better reliability
    from azure.core.pipeline.policies import RetryPolicy
    
    client2 = CognitiveServicesManagementClient(
        credential=azure_credential,
        subscription_id=subscription_id,
        # Add retry policy for better reliability
        per_retry_policies=[RetryPolicy(retry_total=3, retry_backoff_factor=0.8)]
    )
    print("✅ Cognitive Services client created successfully")
    
    print(f"Attempting to list deployments for resource: {aoai_account_name} in RG: {resource_group_name}")
    
    # Add performance monitoring
    import time
    start_time = time.time()
    
    results = client2.deployments.list(
        resource_group_name=resource_group_name,
        account_name=aoai_account_name,
    )
    
    end_time = time.time()
    print(f"✅ Deployment list call successful (took {end_time - start_time:.2f} seconds)")
    
    # List deployments with better error handling
    deployments = []
    deployment_count = 0
    
    try:
        for item in results:
            deployments.append(item.name)
            deployment_count += 1
            print(f"Found deployment: {item.name} (Model: {getattr(item.properties, 'model', {}).get('name', 'Unknown')})")
    except Exception as iteration_error:
        print(f"❌ Error iterating through deployments: {iteration_error}")
        deployments = []
    
    print(f"Total deployments found: {deployment_count}")
    
    # Display success message in Streamlit
    if deployment_count > 0:
        st.success(f"✅ Successfully connected to Azure OpenAI! Found {deployment_count} deployment(s).")
        with st.expander("🔍 Authentication Details", expanded=False):
            st.write("**Successfully authenticated using:**")
            # You could enhance this to show which method was actually used
            st.write("- Entra ID credential chain")
            st.write(f"- Retrieved {deployment_count} model deployments")
            st.write(f"- Response time: {end_time - start_time:.2f} seconds")
    else:
        st.warning("⚠️ Connected to Azure but no deployments found.")
        
except Exception as e:
    print(f"Exception occurred: {type(e).__name__}: {str(e)}")
    
    # Enhanced error categorization and user guidance
    error_str = str(e)
    error_type = type(e).__name__
    
    st.error(f"❌ Failed to retrieve deployments: {error_type}")
    
    # More specific error handling with actionable guidance
    if "ResourceNotFound" in error_str or "NotFound" in error_str:
        st.error("🔍 **Resource Not Found**")
        st.error(f"Azure OpenAI resource '{aoai_account_name}' not found in resource group '{resource_group_name}'.")
        
        with st.expander("🛠️ Quick Fix Options"):
            st.write("**Option 1: Use Discovery Script (Recommended)**")
            st.code(".\\discover-azure-resources.ps1")
            
            st.write("**Option 2: Manual Verification**")
            st.code("""# List all Azure OpenAI resources
az cognitiveservices account list --query "[?kind=='OpenAI'].{name:name, resourceGroup:resourceGroup, location:location}" -o table""")
            
            st.write("**Option 3: Check Current Subscription**")
            st.code("az account show --query '{name:name, id:id}' -o table")
        
    elif "AuthenticationFailed" in error_str or "Unauthorized" in error_str:
        st.error("🔐 **Authentication Failed**")
        st.error("Your Azure credentials are not valid or have expired.")
        
        with st.expander("🛠️ Authentication Solutions"):
            st.write("**For Local Development:**")
            st.code("az login")
            
            st.write("**For Service Principal:**")
            st.write("- Check AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID")
            st.write("- Verify the Service Principal has not expired")
            
            st.write("**For Managed Identity:**")
            st.write("- Ensure your resource has a Managed Identity assigned")
            st.write("- Check that the identity has proper permissions")
        
    elif "Forbidden" in error_str or "InsufficientPermissions" in error_str:
        st.error("🚫 **Access Denied**")
        st.error("You don't have sufficient permissions to access this resource.")
        
        with st.expander("🛠️ Permission Solutions"):
            st.write("**Required Permissions:**")
            st.write("- `Cognitive Services User` role on the Azure OpenAI resource")
            st.write("- `Reader` role on the resource group (minimum)")
            
            st.write("**Check Current Permissions:**")
            st.code(f"""az role assignment list --assignee $(az account show --query user.name -o tsv) --scope /subscriptions/{subscription_id}/resourceGroups/{resource_group_name}""")
            
            st.write("**Contact your Azure administrator to grant proper permissions**")
    
    elif "SubscriptionNotFound" in error_str:
        st.error("📋 **Subscription Issue**")
        st.error(f"Subscription '{subscription_id}' not found or not accessible.")
        
        with st.expander("🛠️ Subscription Solutions"):
            st.code("az account list --query '[].{name:name, id:id}' -o table")
            st.write("Verify you're using the correct subscription ID and have access to it.")
    
    else:
        st.error("❓ **Unexpected Error**")
        st.error(f"Error details: {error_str}")
        
        with st.expander("🛠️ General Troubleshooting"):
            st.write("**Check Authentication:**")
            st.code(".\\test-entra-auth.ps1")
            
            st.write("**Verify Environment Variables:**")
            st.code(".\\check-env.ps1")
            
            st.write("**Common Solutions:**")
            st.write("- Run `az login` to re-authenticate")
            st.write("- Check your internet connection")
            st.write("- Verify all environment variables are correctly set")
            st.write("- Ensure your Azure subscription is active")
    
    # Provide debug information
    st.info("💡 **Debug Information:**")
    st.info("Check the console/terminal output for detailed authentication attempts and error messages.")
    
    deployments = []  # Fallback to empty list when exception occurs

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
