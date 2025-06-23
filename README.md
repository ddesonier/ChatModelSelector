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
   ```
   docker build --no-cache -t modelSelectionChat:latest . 
   ```
2. **Push to ACR**
   - Log in to Azure
     ```
     az login
     ```
   - Set the subscription (if needed)
     ```
     az account set --subscription "<your-subscription-name-or-id>"
     ```
   - Log in to your ACR
     ```
     az acr login --name <your-acr-name>
     ```
   - Tag your local image for ACR
     ```
     docker tag code-assistant:latest <your-acr-name>.azurecr.io/code-assistant:latest
     ```
   - Push the image to ACR
     ```
     docker push <your-acr-name>.azurecr.io/code-assistant:latest
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

### General Tips
- Ensure all environment variables are set correctly
- Check that your Azure credentials have proper permissions
- Verify that your Azure OpenAI resource has deployments configured
- Use the discovery script to automatically find your resource details
