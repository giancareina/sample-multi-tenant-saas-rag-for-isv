import * as cdk from 'aws-cdk-lib';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { NetworkConstruct } from './constructs/network-construct';
import { AuthConstruct } from './constructs/auth-construct';
import { StorageConstruct } from './constructs/storage-construct';
import { ComputeConstruct } from './constructs/compute-construct';
import { ApiConstruct } from './constructs/api-construct';
import { SetupConstruct } from './constructs/setup-construct';
import { NagSuppressions } from 'cdk-nag';

export class OpenSearchRagAppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Network Layer
    const network = new NetworkConstruct(this, 'Network');

    // Auth Layer
    const auth = new AuthConstruct(this, 'Auth', {
      openSearchDomainA: '',  // later
      openSearchDomainB: ''
    });

    // Storage Layer
    const storage = new StorageConstruct(this, 'StorageConstruct', {
      vpc: network.vpc,
      authConstruct: auth,
      openSearchSecurityGroup: network.openSearchSecurityGroup
    });

    // Configure DynamoDB table to Auth Layer after creation
    auth.configureTable(storage.mainTable);
    auth.configureOpenSearchDomains(
      storage.openSearchDomainA.domainEndpoint,
      storage.openSearchDomainB.domainEndpoint
    );


    // Compute Layer
    const compute = new ComputeConstruct(this, 'Compute', {
      vpc: network.vpc,
      lambdaSecurityGroup: network.lambdaSecurityGroup,
      openSearchSecurityGroup: network.openSearchSecurityGroup,
      securityGroup: network.lambdaSecurityGroup,
      userPool: auth.userPool,
      userPoolClient: auth.userPoolClient,
      mainTable: storage.mainTable,
      fileBucket: storage.fileBucket,
    });

    // API Layer
    const api = new ApiConstruct(this, 'Api', {
      userPool: auth.userPool,
      chatCompletionHandler: compute.chatCompletionHandler,
      documentManagerHandler: compute.documentManagerHandler,
      presignedUrlGenerator: compute.presignedUrlGenerator,
      documentSyncHandler: compute.documentSyncHandler,
      consumptionMeteringHandler: compute.consumptionMeteringHandler
    });
    

    new SetupConstruct(this, 'Setup', {
      userPool: auth.userPool,
      userPoolClient: auth.userPoolClient,
      mainTable: storage.mainTable,
      vpc: network.vpc,
      lambdaSecurityGroup: network.lambdaSecurityGroup,
      openSearchDomainA: storage.openSearchDomainA,
      openSearchDomainB: storage.openSearchDomainB,
      setupLambdaRole: storage.setupLambdaRole,
    });

    const region = cdk.Stack.of(this).region;
    const account = cdk.Stack.of(this).account;
    
    const bedrockConsumptionLogRole = new iam.Role(this, 'BedrockConsumptionLogRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com')
        .withConditions({
          'StringEquals': {
            'aws:SourceAccount': account
          },
          'ArnLike': {
            'aws:SourceArn': `arn:aws:bedrock:${region}:${account}:*`
          }
        })
    });

    const bedrockConsumptionLogGroup = new logs.LogGroup(this, 'BedrockConsumptionLogGroup', {
      retention: logs.RetentionDays.THREE_DAYS,
    });

    bedrockConsumptionLogRole.addToPolicy(new iam.PolicyStatement({
                effect: iam.Effect.ALLOW,
                actions: ['logs:CreateLogStream', 'logs:PutLogEvents'],
                resources: [`arn:aws:logs:${region}:${account}:log-group:${bedrockConsumptionLogGroup.logGroupName}:log-stream:aws/bedrock/modelinvocations`]
            }));

    // Outputs
    this.outputValues(auth, api);

    // CDK Nag suppressions
    this.addNagSuppressions();
  }

  private addNagSuppressions(): void {
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/Auth/PreTokenGenerationHandler/ServiceRole/Resource',
        '/OpenSearchRagAppStack/StorageConstruct/SetupLambdaRole/Resource',
        '/OpenSearchRagAppStack/AWS679f53fac002430cb0da5b7982bd2287/ServiceRole/Resource',
        '/OpenSearchRagAppStack/Compute/LambdaExecutionRole/Resource',
        '/OpenSearchRagAppStack/BucketNotificationsHandler050a0587b7544547bf325f094a3db834/Role/Resource',
        '/OpenSearchRagAppStack/Setup/TenantSetupProvider/framework-onEvent/ServiceRole/Resource'
      ],
      [
        { id: 'AwsPrototyping-IAMNoManagedPolicies', reason: 'Lambda functions use AWSLambdaBasicExecutionRole which only provides minimal CloudWatch Logs permissions' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      ['/OpenSearchRagAppStack/Auth/UserPool/Resource'],
      [
        { id: 'AwsPrototyping-CognitoUserPoolAdvancedSecurityModeEnforced', reason: 'Advanced Security Mode is optional for a demo application' },
        { id: 'AwsPrototyping-CognitoUserPoolMFA', reason: 'MFA is optional for this demo application' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/StorageConstruct/SetupLambdaRole/DefaultPolicy/Resource',
        '/OpenSearchRagAppStack/Compute/LambdaExecutionRole/DefaultPolicy/Resource',
        '/OpenSearchRagAppStack/BucketNotificationsHandler050a0587b7544547bf325f094a3db834/Role/DefaultPolicy/Resource',
        '/OpenSearchRagAppStack/Setup/TenantSetupProvider/framework-onEvent/ServiceRole/DefaultPolicy/Resource'
      ],
      [
        { id: 'AwsPrototyping-IAMNoWildcardPermissions', reason: 'Required for Lambda functions to access various resources especially VPC' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/Setup/BedrockModelAccessRole/DefaultPolicy/Resource'
      ],
      [
        { id: 'AwsPrototyping-IAMNoWildcardPermissions', reason: 'We are using wildcards for the model invocation to maintain flexibility in changing the models. Access is restricted to foundation models only.' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/StorageConstruct/SetupLambdaRole/DefaultPolicy/Resource'
      ],
      [
        { id: 'AwsPrototyping-IAMPolicyNoStatementsWithFullAccess', reason: 'Granting es:* is necessary for setup operations on OpenSearch, but the resource is limited to specific domains' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/StorageConstruct/FileBucket/Resource',
        '/OpenSearchRagAppStack/StorageConstruct/FileBucket/Policy/Resource'
      ],
      [
        { id: 'AwsPrototyping-S3BucketLoggingEnabled', reason: 'Server access logging not required for this demo' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/StorageConstruct/OpenSearchDomainA/Resource',
        '/OpenSearchRagAppStack/StorageConstruct/OpenSearchDomainB/Resource'
      ],
      [
        { id: 'AwsPrototyping-OpenSearchAllowlistedIPs', reason: 'Access control handled through VPC and security groups' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      ['/OpenSearchRagAppStack/Api/RestApi/Resource'],
      [
        { id: 'AwsPrototyping-APIGWRequestValidation', reason: 'Request validation is optional for demo application' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      ['/OpenSearchRagAppStack/Api/RestApi/DeploymentStage.prod/Resource'],
      [
        { id: 'AwsPrototyping-APIGWAssociatedWithWAF', reason: 'WAF not required for this demo application' }
      ]
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/OpenSearchRagAppStack/Api/RestApi/Default/OPTIONS/Resource',
        '/OpenSearchRagAppStack/Api/RestApi/Default/chat/OPTIONS/Resource',
        '/OpenSearchRagAppStack/Api/RestApi/Default/chat/messages/OPTIONS/Resource',
        '/OpenSearchRagAppStack/Api/RestApi/Default/documents/OPTIONS/Resource',
        '/OpenSearchRagAppStack/Api/RestApi/Default/documents/upload-url/OPTIONS/Resource',
        '/OpenSearchRagAppStack/Api/RestApi/Default/documents/sync/OPTIONS/Resource'
      ],
      [
        { id: 'AwsPrototyping-CognitoUserPoolAPIGWAuthorizer', reason: 'The request finally reaches OpenSearch, and JWT verification is performed on OpenSearch.' }
      ]
    );
    
  }

  private outputValues(
    auth: AuthConstruct,
    api: ApiConstruct,
  ): void {
    // Frontend environment variables
    new cdk.CfnOutput(this, 'VITE_APP_REGION', {
      value: this.region,
      description: 'AWS Region for frontend environment'
    });

    new cdk.CfnOutput(this, 'VITE_APP_USER_POOL_ID', {
      value: auth.userPool.userPoolId,
      description: 'Cognito User Pool ID for frontend environment'
    });

    new cdk.CfnOutput(this, 'VITE_APP_USER_CLIENT_ID', {
      value: auth.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID for frontend environment'
    });

    new cdk.CfnOutput(this, 'VITE_API_ENDPOINT', {
      value: api.restApi.url,
      description: 'API Gateway endpoint for frontend environment'
    });
  }
}
