# JWT OpenSearch RAG Solution

This repository contains a sample implementation of a Retrieval Augmented Generation (RAG) application using Amazon OpenSearch Service and Amazon Cognito. It combines JWT-based authentication with efficient search capabilities provided by OpenSearch.

## Architecture Overview

This solution consists of the following components:

- **Frontend**: Single Page Application built with React + TypeScript
- **Backend**: Serverless architecture defined with AWS CDK
  - Amazon Cognito: User authentication
  - Amazon API Gateway: RESTful API
  - AWS Lambda: Business logic
  - Amazon OpenSearch Service: Document search
  - Amazon DynamoDB: Metadata management
  - Amazon S3: Document storage

## Key Features

- User authentication and JWT-based access control
- Document upload and management
- Natural language document search
- Chat interface for interactive search

## Directory Structure

```
/
├── frontend/           # Frontend application (React + TypeScript)
├── infrastructure/     # Infrastructure code (AWS CDK)
└── sample-docs/        # Sample documents
```

## Prerequisites

- [Node.js](https://nodejs.org/) (v18 or later)
- [AWS CLI](https://aws.amazon.com/cli/) (latest version)
- [AWS CDK](https://aws.amazon.com/cdk/) (v2.170.0 or later)
- AWS account with appropriate IAM permissions

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/jwt-opensearch.git
cd jwt-opensearch
```

### 2. Deploy the Backend

```bash
cd infrastructure
touch .env
```

Make and edit the `.env` file with the values based on your environment:

```
CORS_ALLOWED_ORIGIN=http://localhost:5173
DEMO_USER_PASSWORD=Password1234!
```

```bash
npm install
npm run cdk deploy
```

Note: We recommend using `npm install` instead of `npm ci` due to dependency issues with the `@aws/pdk` package.

After deployment completes, note the output values (API endpoint, Cognito User Pool ID, etc.).

### 3. Configure and Start the Frontend

```bash
cd ../frontend
touch .env
```

Make and edit the `.env` file with the values obtained from the CDK deployment:

```
VITE_API_ENDPOINT=https://your-api-id.execute-api.region.amazonaws.com/prod
VITE_APP_USER_POOL_ID=region_userpoolid
VITE_APP_USER_CLIENT_ID=your-app-client-id
```

```bash
npm install
npm run dev
```

The frontend application will be available at http://localhost:5173.

## Detailed Documentation

- [Frontend Setup](./frontend/README.md)
- [Infrastructure Deployment](./infrastructure/README.md)

## Security

This sample application implements the following security best practices:

- JWT-based authentication
- Enforced HTTPS communication
- IAM policies based on the principle of least privilege
- OpenSearch deployment within a VPC

## Disclaimer

This code is provided as a sample and should undergo appropriate security review before use in production environments.

## License

This project is licensed under the [MIT License](LICENSE).