# JWT OpenSearch RAG Solution with metering

This repository is a fork of https://github.com/aws-samples/sample-multi-tenant-saas-rag-using-bedrock-and-amazon-opensearch-service-with-jwt, and it extends it by adding metering functionality for SaaS model-based companies. Please refer to the source repository Readme file. 

This repository adds the following feature:

1. Usage dashboard in the frontend where users can see the total cost and consumption of bedrock models.
2. Functionality in the backend (Lambda, API Gateway) to keep track of the usage metrics per tenant. 