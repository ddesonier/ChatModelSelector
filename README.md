# ChatModelSelector
AI Foundry Python AI Model Selector

## Setup Instructions

1. Update the `.env` file with your Azure credentials:
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI resource endpoint
   - `AZURE_OPENAI_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_API_VERSION`: API version 
   - `SUBSCRIPTION_ID`: Your Azure subscription ID
   - `RESOURCE_GROUP_NAME`: Resource group containing your AOAI resource
   - `AOAI_ACCOUNT_NAME`: Name of your Azure OpenAI account

### Common Setup Steps
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## 🐳 Build Docker Container and Push to ACR

1. **Build Docker Container**
   ```bash
   docker build --no-cache -t modelselectionchat:latest . 
   ```

2. **Test Docker Container Locally (Optional)**
   ```bash
   # Create .env file first with your Azure credentials
   docker run -p 8501:8501 --env-file .env modelselectionchat:latest
   ```

3. **Push to ACR**
   - Log in to Azure
     ```bash
     az login
     ```
   - Set the subscription (if needed)
     ```bash
     az account set --subscription "<your-subscription-name-or-id>"
     ```
   - Log in to your ACR
     ```bash
     az acr login --name <your-acr-name>
     ```
   - Tag your local image for ACR
     ```bash
     docker tag modelselectionchat:latest <your-acr-name>.azurecr.io/modelselectionchat:latest
     ```
   - Push the image to ACR
     ```bash
     docker push <your-acr-name>.azurecr.io/modelselectionchat:latest
     ```

**Note:** The Dockerfile has been fixed to:
- ✅ Remove `--no-index` flag that was preventing package downloads
- ✅ Use local files instead of cloning from GitHub
- ✅ Correct the app entry point path
- ✅ Optimize Docker layer caching

### 🔐 Docker Authentication Setup

For Docker containers, you need Azure AD authentication (Service Principal):

1. **Create a Service Principal:**
   ```bash
   .\create-service-principal.ps1 -ServicePrincipalName "ModelSelectorApp"
   ```

2. **Add the output to your .env file:**
   ```bash
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   AZURE_TENANT_ID=your-tenant-id
   ```

3. **Rebuild and run the container:**
   ```bash
   docker build -t modelselectionchat:latest .
   docker run -p 8501:8501 --env-file .env modelselectionchat:latest
   ```

**Alternative:** You can create a Service Principal manually:
```bash
az ad sp create-for-rbac --name "ModelSelectorApp" --role contributor
```
   - Verify the image is in ACR
     ```
     az acr repository list --name <your-acr-name> --output table
     ```

---





## Features

- Select from available Azure OpenAI deployments
- Interactive chat interface
- Download conversation history
- Error handling and validation

## Troubleshooting

### Quick Diagnostic Tools

**🔧 Test your configuration:**
```powershell
.\test-connection.ps1
```
This script will check all your environment variables and test the Azure connection.

### Common Issues

**"Must provide either the api_version argument or the OPENAI_API_VERSION environment variable"**
- Solution: Ensure `AZURE_OPENAI_API_VERSION` is set in your `.env` file

**"ResourceNotFound: The Resource 'your-resource' was not found"**
- Solution: Run `.\discover-azure-resources.ps1` to find your correct resource names
- Verify `RESOURCE_GROUP_NAME` and `AOAI_ACCOUNT_NAME` in your `.env` file
- Check that you're logged into the correct Azure subscription

**"No deployments found"**
- Ensure your Azure OpenAI resource has model deployments created
- Check permissions: you need at least "Cognitive Services User" role
- Verify your subscription ID is correct

**"DefaultAzureCredential failed to retrieve a token" (Docker)**
- This happens when running in Docker containers
- Solution: Create a Service Principal and add credentials to .env:
  ```bash
  .\create-service-principal.ps1 -ServicePrincipalName "ModelSelectorApp"
  ```
- Add the output variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID) to your .env file
- Rebuild the Docker image after adding the credentials

**Docker container authentication issues:**
- Ensure your .env file includes Service Principal credentials
- The Service Principal needs "Contributor" role on your subscription
- Check that all Azure environment variables are properly set in the container

### General Tips
- Ensure all environment variables are set correctly
- Check that your Azure credentials have proper permissions
- Verify that your Azure OpenAI resource has deployments configured
- Use the discovery script to automatically find your resource details
