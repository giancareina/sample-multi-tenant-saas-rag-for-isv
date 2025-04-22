import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as path from 'path';
import * as s3notifications from 'aws-cdk-lib/aws-s3-notifications';

interface ComputeConstructProps {
  vpc: ec2.Vpc;
  vpcSubnets?: ec2.SubnetSelection;
  securityGroup: ec2.SecurityGroup;
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  mainTable: dynamodb.Table;
  fileBucket: s3.Bucket;
  openSearchSecurityGroup: ec2.SecurityGroup;
  lambdaSecurityGroup: ec2.SecurityGroup;
}

export class ComputeConstruct extends Construct {
  public readonly chatCompletionHandler: lambda_python.PythonFunction;
  public readonly documentManagerHandler: lambda_python.PythonFunction;
  public readonly presignedUrlGenerator: lambda_python.PythonFunction;
  public readonly documentSyncHandler: lambda_python.PythonFunction;
  lambdaRole: iam.Role;

  constructor(scope: Construct, id: string, props: ComputeConstructProps) {
    super(scope, id);

    const region = cdk.Stack.of(this).region;
    const account = cdk.Stack.of(this).account;

    props.lambdaSecurityGroup.addEgressRule(
      props.openSearchSecurityGroup,
      ec2.Port.tcp(443),
      'Allow access to OpenSearch'
    );

    const lambdaRole = this.createLambdaRole(props.mainTable.tableArn, region, account);

    // VPC subnet for Lambda
    const defaultVpcSubnets = props.vpcSubnets ?? {
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS
    };

    // Data Functions
    this.chatCompletionHandler = new lambda_python.PythonFunction(this, 'ChatCompletionHandler', {
      entry: path.join(__dirname, '../../lambda/chat'),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: 'chat_completion.py',
      handler: 'handler',
      vpc: props.vpc,
      vpcSubnets: defaultVpcSubnets,
      securityGroups: [props.lambdaSecurityGroup],
      role: lambdaRole,
      environment: {
        'TABLE_NAME': props.mainTable.tableName,
        'USER_POOL_ID': props.userPool.userPoolId,
        'USER_POOL_CLIENT_ID': props.userPoolClient.userPoolClientId,
        ALLOWED_ORIGINS: process.env.CORS_ALLOWED_ORIGIN ?? '*'
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
    });

    // Document Functions
    this.documentManagerHandler = new lambda_python.PythonFunction(this, 'DocumentManagerHandler', {
      entry: path.join(__dirname, '../../lambda/documents'),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: 'document_manager.py',
      handler: 'handler',
      vpc: props.vpc,
      vpcSubnets: defaultVpcSubnets,
      securityGroups: [props.lambdaSecurityGroup],
      role: lambdaRole,
      environment: {
        'TABLE_NAME': props.mainTable.tableName,
        'USER_POOL_ID': props.userPool.userPoolId,
        'USER_POOL_CLIENT_ID': props.userPoolClient.userPoolClientId,
        ALLOWED_ORIGINS: process.env.CORS_ALLOWED_ORIGIN ?? '*'
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
    });

    const documentTrackingHandler = new lambda_python.PythonFunction(this, 'DocumentTrackingHandler', {
      entry: path.join(__dirname, '../../lambda/documents'),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: 'document_tracker.py',
      handler: 'handler',
      role: lambdaRole,
      environment: {
        TABLE_NAME: props.mainTable.tableName,
        ALLOWED_ORIGINS: process.env.CORS_ALLOWED_ORIGIN ?? '*'
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
    });

    // Utils Functions
    this.presignedUrlGenerator = new lambda_python.PythonFunction(this, 'PresignedUrlGenerator', {
      entry: path.join(__dirname, '../../lambda/upload'),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: 'presigned_url.py',
      handler: 'handler',
      role: lambdaRole,
      environment: {
        FILE_BUCKET: props.fileBucket.bucketName,
        'USER_POOL_ID': props.userPool.userPoolId,
        'USER_POOL_CLIENT_ID': props.userPoolClient.userPoolClientId,
        ALLOWED_ORIGINS: process.env.CORS_ALLOWED_ORIGIN ?? '*'
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
    });

    // Setup S3 notifications
    props.fileBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED_PUT,
      new s3notifications.LambdaDestination(documentTrackingHandler)
    );
    
    props.fileBucket.grantReadWrite(this.presignedUrlGenerator);

    // Document Syncer Function
    this.documentSyncHandler = new lambda_python.PythonFunction(this, 'DocumentSyncHandler', {
      entry: path.join(__dirname, '../../lambda/documents'),
      runtime: lambda.Runtime.PYTHON_3_13,
      index: 'document_syncer.py',
      handler: 'handler',
      vpc: props.vpc,
      vpcSubnets: defaultVpcSubnets,
      securityGroups: [props.lambdaSecurityGroup],
      role: lambdaRole,
      environment: {
        'TABLE_NAME': props.mainTable.tableName,
        'USER_POOL_ID': props.userPool.userPoolId,
        'USER_POOL_CLIENT_ID': props.userPoolClient.userPoolClientId,
        ALLOWED_ORIGINS: process.env.CORS_ALLOWED_ORIGIN ?? '*'
      },
      timeout: cdk.Duration.minutes(5),  // Configure for long-running execution
      memorySize: 1024,
    });

  }

  private createLambdaRole(tableArn: string, region: string, account: string): iam.Role {
    const role = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'cognito-idp:AdminInitiateAuth',
        'cognito-idp:DescribeUserPool',
        'cognito-idp:DescribeUserPoolClient'
      ],
      resources: ['*']
    }));

    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents'
      ],
      resources: [`arn:aws:logs:${region}:${account}:log-group:/aws/lambda/*`]
    }));

    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:PutItem',
        'dynamodb:GetItem',
        'dynamodb:UpdateItem',
        'dynamodb:DeleteItem',
        'dynamodb:Query',
        'dynamodb:Scan'
      ],
      resources: [tableArn]
    }));

    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream'
      ],
      resources: ['arn:aws:bedrock:*::foundation-model/*']
    }));

    

    return role;
  }
}
