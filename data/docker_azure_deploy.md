# Containerising and deploying to Azure

A Dockerfile describes how to build an image: a base image, installed dependencies, copied code, and a start command. Copy requirements.txt and install dependencies before copying the source code so Docker can cache the slow install layer.

Push the image to Azure Container Registry (ACR), then run it on Azure Container Apps, which scales containers automatically including down to zero replicas. Azure App Service is a simpler option for a single web app, and Azure Functions suits event-driven or scheduled work.

Never bake secrets into an image. Pass configuration as environment variables or secrets, and prefer managed identity so the container authenticates to Azure OpenAI and Azure AI Search without any key.

# Monitoring and cost

Use Azure Monitor and Application Insights for logs and traces. Track token usage per request because Azure OpenAI is billed per token. Set budget alerts in Cost Management, and delete the resource group when a demo is finished.
