# JWT OpenSearch RAG Solution - Frontend

This is the frontend application for the JWT OpenSearch RAG Solution. It's built with React, TypeScript, and Tailwind CSS, providing a user-friendly interface for document management and search capabilities.

## Features

- User authentication with Amazon Cognito
- Document upload and management
- Chat interface for natural language queries
- Document search and retrieval
- Responsive design

## Prerequisites

- [Node.js](https://nodejs.org/) (v18 or later)
- npm or yarn
- Backend services deployed via the infrastructure CDK project

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in the root of the frontend directory:

```bash
touch .env
```

Edit the `.env` file with the following values from your CDK deployment:

```
VITE_API_ENDPOINT=https://your-api-id.execute-api.region.amazonaws.com/prod
VITE_APP_USER_POOL_ID=region_userpoolid
VITE_APP_USER_CLIENT_ID=your-app-client-id
```

### 3. Start the Development Server

```bash
npm run dev
```

The application will be available at http://localhost:5173.

### 4. Build for Production

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/             # API client configuration
│   ├── assets/          # Images and other assets
│   ├── components/      # Reusable UI components
│   ├── config/          # Configuration files
│   ├── features/        # Feature-specific components
│   │   ├── chat/        # Chat interface
│   │   ├── documents/   # Document management
│   │   └── upload/      # File upload
│   ├── types/           # TypeScript type definitions
│   ├── App.tsx          # Main application component
│   └── main.tsx         # Application entry point
├── .env                 # Environment variables
├── index.html           # HTML template
├── package.json         # Project dependencies
├── tailwind.config.js   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── vite.config.ts       # Vite configuration
```

## Authentication Flow

The application uses Amazon Cognito for authentication. The authentication flow is as follows:

1. User signs in through the Cognito UI
2. Upon successful authentication, Cognito returns JWT tokens
3. The application stores the tokens and includes them in API requests
4. The backend validates the tokens and processes the requests

## API Integration

The application communicates with the backend API using Axios. The API client is configured to include the JWT token in the Authorization header for all requests.

## Customization

### Styling

The application uses Tailwind CSS for styling. You can customize the appearance by modifying the `tailwind.config.js` file.

### Adding New Features

To add new features:

1. Create a new directory under `src/features/`
2. Implement the feature components
3. Add the feature to the main application in `App.tsx`

## Troubleshooting

### Authentication Issues

- Ensure the Cognito User Pool ID and Client ID are correct in the `.env` file
- Check that the user has been confirmed in the Cognito User Pool

### API Connection Issues

- Verify that the API endpoint is correct in the `.env` file
- Ensure that CORS is properly configured on the API Gateway
- Check the browser console for error messages

### Apple Silicon (M1/M2/M3) Mac Issues

If you encounter the following error when running `npm run dev` on an Apple Silicon Mac:

```
Error: Cannot find module @rollup/rollup-darwin-arm64. npm has a bug related to optional dependencies...
```

Try installing the missing module directly:

```bash
npm install @rollup/rollup-darwin-arm64 --no-save
```

Then run `npm run dev` again. This issue is specific to Apple Silicon Macs due to architecture-specific native dependencies.

## License

This project is licensed under the [MIT License](../LICENSE)