# JWT OpenSearch RAG Solution - Infrastructure

This project implements the infrastructure for a Retrieval-Augmented Generation (RAG) application using Amazon OpenSearch and AWS services. The infrastructure is defined using AWS CDK and deploys all necessary backend components.

## Architecture

The application is built using AWS CDK and consists of several layers:

- **Network Layer**: VPC, subnets, and security groups
- **Auth Layer**: Cognito user pool for authentication
- **Storage Layer**: OpenSearch domains, DynamoDB table, and S3 bucket
- **Compute Layer**: Lambda functions for processing requests
- **API Layer**: API Gateway for exposing endpoints
- **Setup Layer**: Resources for initial setup and configuration

## Features

- Document upload and management
- Document indexing in OpenSearch
- Chat interface with RAG capabilities
- Multi-tenant support
- JWT-based authentication

## Getting Started

### Prerequisites

- Node.js 18.x or later
- AWS CLI configured with appropriate credentials
- AWS CDK installed (v2.170.0 or later)
- Docker installed and running (latest version, required for Python Lambda function deployment)

### Installation

1. Install dependencies:

```bash
npm install
```

Note: We recommend using `npm install` instead of `npm ci` due to dependency issues with the `@aws/pdk` package. The `@aws/pdk` package is required for security checks but causes compatibility issues with `npm ci`. This is related to [aws/aws-pdk#902](https://github.com/aws/aws-pdk/issues/902) issue.

2. Deploy the application:

```bash
npm run cdk deploy
```

3. After deployment, note the output values that will be needed for the frontend configuration:
   - API Gateway endpoint
   - Cognito User Pool ID
   - Cognito User Pool Client ID
   - AWS Region

## Project Structure

```
infrastructure/
├── bin/                # CDK application entry point
├── lib/                # CDK constructs and stack definitions
│   ├── constructs/     # Reusable infrastructure components
│   └── opensearch-rag-app-stack.ts  # Main stack definition
├── lambda/             # Lambda function code
│   ├── auth/           # Authentication handlers
│   ├── chat/           # Chat completion handlers
│   ├── documents/      # Document management
│   ├── setup/          # Setup and initialization
│   └── upload/         # File upload handlers
├── test/               # Unit tests
├── cdk.json            # CDK configuration
└── package.json        # Project dependencies
```


## Security Considerations

This infrastructure implements several security best practices:

- OpenSearch domains deployed within a VPC
- Least privilege IAM policies
- JWT-based authentication with Cognito
- Network isolation using security groups
- HTTPS enforcement for all API endpoints
- Security checks using AWS PDK (Prototyping Development Kit)

## Dependency Notes

The project uses `@aws/pdk` for security checks and best practices validation. This package has some dependency conflicts that can cause issues with `npm ci`. If you encounter problems:

1. Use `npm install` instead of `npm ci`
2. If you need to use `npm ci` for CI/CD pipelines, you may need to temporarily remove `@aws/pdk` from dependencies and modify the CDK application initialization code.

## Customization

You can customize the deployment by modifying the CDK stack and constructs. Common customizations include:

- Changing the OpenSearch instance types
- Modifying the VPC configuration
- Adjusting the Lambda function configurations
- Adding additional API endpoints

## Troubleshooting

### Deployment Issues

- Ensure you have sufficient permissions in your AWS account
- Check CloudFormation console for detailed error messages
- Verify that service quotas are not being exceeded

### Runtime Issues

- Check CloudWatch Logs for Lambda function errors
- Verify network connectivity between components
- Ensure OpenSearch domains are in an active state

## License

This project is licensed under the [MIT License](../LICENSE)