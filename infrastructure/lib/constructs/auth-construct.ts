import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as path from 'path';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

interface AuthConstructProps {
  openSearchDomainA: string;
  openSearchDomainB: string;
}

export class AuthConstruct extends Construct {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;
  private preTokenGenerationHandler: lambda_python.PythonFunction;

  constructor(scope: Construct, id: string, props: AuthConstructProps) {
    super(scope, id);

    // Pre Token Generation Lambda Function
    this.preTokenGenerationHandler = new lambda_python.PythonFunction(this, 'PreTokenGenerationHandler', {
      entry: path.join(__dirname, '../../lambda/auth'),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: 'cognito-pre-token-generation.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        OPENSEARCH_DOMAIN_A: props.openSearchDomainA,
        OPENSEARCH_DOMAIN_B: props.openSearchDomainB
      }
    });

    this.userPool = this.createUserPool(this.preTokenGenerationHandler);
    this.userPoolClient = this.createUserPoolClient();
  }

  public configureTable(table: dynamodb.Table) {
    // env
    this.preTokenGenerationHandler.addEnvironment('TABLE_NAME', table.tableName);
    
    // Grant access permissions to DynamoDB
    table.grantReadData(this.preTokenGenerationHandler);
  }

  public configureOpenSearchDomains(domainA: string, domainB: string) {
    this.preTokenGenerationHandler.addEnvironment('OPENSEARCH_DOMAIN_A', domainA);
    this.preTokenGenerationHandler.addEnvironment('OPENSEARCH_DOMAIN_B', domainB);
  }

  private createUserPool(preTokenFunction: lambda.Function): cognito.UserPool {
    const userPool = new cognito.UserPool(this, 'UserPool', {
      selfSignUpEnabled: true,
      signInAliases: { email: true, username: true },
      autoVerify: { email: true },
      passwordPolicy: {
        minLength: 12,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      mfa: cognito.Mfa.OPTIONAL,
      mfaSecondFactor: {
        sms: false,
        otp: true,
      },
      advancedSecurityMode: cognito.AdvancedSecurityMode.OFF,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      lambdaTriggers: {
        preTokenGeneration: preTokenFunction
      }
    });

    // Grant permissions for Cognito to invoke triggers
    preTokenFunction.addPermission('CognitoPermission', {
      principal: new iam.ServicePrincipal('cognito-idp.amazonaws.com'),
      sourceArn: userPool.userPoolArn
    });

    return userPool;
  }

  private createUserPoolClient(): cognito.UserPoolClient {
    return this.userPool.addClient('UserPoolClient', {
      generateSecret: false,
      preventUserExistenceErrors: true,
      authFlows: {
        adminUserPassword: true,
        userPassword: true,
        userSrp: true
      }
    });
  }
}
