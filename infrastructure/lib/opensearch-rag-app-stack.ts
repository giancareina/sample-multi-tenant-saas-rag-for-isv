import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { NetworkConstruct } from './constructs/network-construct';
import { AuthConstruct } from './constructs/auth-construct';
import { StorageConstruct } from './constructs/storage-construct';
import { ComputeConstruct } from './constructs/compute-construct';
import { ApiConstruct } from './constructs/api-construct';
import { SetupConstruct } from './constructs/setup-construct';

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

    // Outputs
    this.outputValues(auth, api);
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