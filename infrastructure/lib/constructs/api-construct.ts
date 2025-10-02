import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';

interface ApiConstructProps {
  userPool: cognito.UserPool;
  chatCompletionHandler: lambda.Function;
  documentManagerHandler: lambda.Function;
  presignedUrlGenerator: lambda.Function;
  documentSyncHandler: lambda.Function;
  consumptionMeteringHandler: lambda.Function;
}

export class ApiConstruct extends Construct {
  public readonly restApi: apigw.RestApi;

  constructor(scope: Construct, id: string, props: ApiConstructProps) {
    super(scope, id);

    // access log
    const accessLogGroup = new logs.LogGroup(this, 'ApiGatewayAccessLogs', {
      retention: logs.RetentionDays.THREE_DAYS,
    });

    this.restApi = this.createRestApi();
    const cognitoAuthorizer = this.createAuthorizer(props.userPool);
    this.setupRoutes(props, cognitoAuthorizer);
  }

  private createRestApi(): apigw.RestApi {
    // Check if cors origin is set
    if (!process.env.CORS_ALLOWED_ORIGIN) {
      throw new Error('CORS_ALLOWED_ORIGIN environment variable must be set');
  }
    const api = new apigw.RestApi(this, 'RestApi', {
      defaultCorsPreflightOptions: {
        allowOrigins: [process.env.CORS_ALLOWED_ORIGIN ?? 'http://localhost:5173'],
        allowMethods: ['OPTIONS', 'POST', 'GET', 'DELETE'],
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
          'X-Amz-Invocation-Type'
        ],
        allowCredentials: true
      }
    });

    // Add CORS headers to error response
    api.addGatewayResponse('DEFAULT_4XX', {
      type: apigw.ResponseType.DEFAULT_4XX,
      responseHeaders: {
       'Access-Control-Allow-Origin': `'${process.env.CORS_ALLOWED_ORIGIN || 'http://localhost:5173'}'`,
        'Access-Control-Allow-Credentials': "'true'"
      }
    });
    
    api.addGatewayResponse('DEFAULT_5XX', {
      type: apigw.ResponseType.DEFAULT_5XX,
      responseHeaders: {
        'Access-Control-Allow-Origin': `'${process.env.CORS_ALLOWED_ORIGIN || 'http://localhost:5173'}'`,
        'Access-Control-Allow-Credentials': "'true'"
      }
    });
    
    return api;
  }

  private createAuthorizer(userPool: cognito.UserPool): apigw.CognitoUserPoolsAuthorizer {
    return new apigw.CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [userPool],
    });
  }

  private setupRoutes(props: ApiConstructProps, authorizer: apigw.CognitoUserPoolsAuthorizer) {
    // Chat message endpoint
    const chatResource = this.restApi.root.addResource('chat');
    const messagesResource = chatResource.addResource('messages');
    messagesResource.addMethod('POST',
      new apigw.LambdaIntegration(props.chatCompletionHandler, {
        proxy: true,
      }), {
      authorizer: authorizer,
      authorizationType: apigw.AuthorizationType.COGNITO,
    });

    // Document management endpoint
    const documentsResource = this.restApi.root.addResource('documents');
    documentsResource.addMethod('GET',
      new apigw.LambdaIntegration(props.documentManagerHandler, {
        proxy: true,
      }), {
      authorizer: authorizer,
      authorizationType: apigw.AuthorizationType.COGNITO,
    });

    documentsResource.addMethod('DELETE',
      new apigw.LambdaIntegration(props.documentManagerHandler, {
        proxy: true,
      }), {
      authorizer: authorizer,
      authorizationType: apigw.AuthorizationType.COGNITO,
    });

    // Upload URL retrieval endpoint
    const uploadUrlResource = documentsResource.addResource('upload-url');
    uploadUrlResource.addMethod('GET',
      new apigw.LambdaIntegration(props.presignedUrlGenerator, {
        proxy: true,
      }), {
      authorizer: authorizer,
      authorizationType: apigw.AuthorizationType.COGNITO,
    });

    // Document synchronization endpoint
    const syncResource = documentsResource.addResource('sync');
    syncResource.addMethod('POST',
      new apigw.LambdaIntegration(props.documentSyncHandler, {
        proxy: false,
        integrationResponses: [{
          statusCode: '202',
            responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': `'${process.env.CORS_ALLOWED_ORIGIN || '*'}'`,
            'method.response.header.Access-Control-Allow-Credentials': "'true'",
            'method.response.header.Content-Type': "'application/json'"
          },
          responseTemplates: {
            'application/json': JSON.stringify({
              message: 'Processing started',
              status: 'accepted'
            })
          }
        }],
        requestTemplates: {
          'application/json': `
          #set($context.requestOverride.header.X-Amz-Invocation-Type = 'Event')
          {
            "body": $input.json('$'),
            "headers": {
              #foreach($header in $input.params().header.keySet())
              "$header": "$util.escapeJavaScript($input.params().header.get($header))"
              #if($foreach.hasNext),#end
              #end
            },
            "requestContext": {
              "authorizer": {
                "claims": {
                  #foreach($key in $context.authorizer.claims.keySet())
                  "$key": "$util.escapeJavaScript($context.authorizer.claims.get($key))"
                  #if($foreach.hasNext),#end
                  #end
                }
              }
            }
          }`
        }
      }), {
      methodResponses: [{
        statusCode: '202',
            responseParameters: {
              'method.response.header.Access-Control-Allow-Origin': true,
              'method.response.header.Access-Control-Allow-Credentials': true,
          'method.response.header.Content-Type': true
      }
      }],
      authorizer: authorizer,
      authorizationType: apigw.AuthorizationType.COGNITO,
    });

    // Consumption metering endpoints
    const consumptionResource = this.restApi.root.addResource('consumption');
    
    // Dashboard endpoint - GET /consumption/dashboard
    const dashboardResource = consumptionResource.addResource('dashboard');
    dashboardResource.addMethod('GET',
      new apigw.LambdaIntegration(props.consumptionMeteringHandler, {
        proxy: true,
      }), {
      authorizer: authorizer,
      authorizationType: apigw.AuthorizationType.COGNITO,
    });
  }
}