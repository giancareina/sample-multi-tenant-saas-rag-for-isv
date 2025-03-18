// lib/constructs/setup-construct.ts
import { Stack } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import path = require('path');
import * as lambda_python from '@aws-cdk/aws-lambda-python-alpha';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';

interface SetupConstructProps {
  userPool: cognito.UserPool;
  userPoolClient: cognito.UserPoolClient;
  mainTable: dynamodb.Table;
  vpc: ec2.Vpc;
  lambdaSecurityGroup: ec2.SecurityGroup;
  openSearchDomainA: opensearch.Domain;
  openSearchDomainB: opensearch.Domain;
  setupLambdaRole: iam.Role;
}

export class SetupConstruct extends Construct {
  constructor(scope: Construct, id: string, props: SetupConstructProps) {
    super(scope, id);

        const region = Stack.of(this).region;
        const account = Stack.of(this).account;

        // Create IAM Role for Bedrock
        const bedrockRole = new iam.Role(this, 'BedrockFullAccessRole', {
            assumedBy: new iam.CompositePrincipal(
                new iam.ServicePrincipal('opensearchservice.amazonaws.com'),
                new iam.ServicePrincipal('lambda.amazonaws.com')
            ),
            description: 'Role with full access to Bedrock API',
        });

        // Grant full access permissions to Bedrock
        bedrockRole.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            actions: ['bedrock:*'],
            resources: [`*`]
        }));

        // Check if demo user password is set
        if (!process.env.DEMO_USER_PASSWORD) {
            throw new Error('DEMO_USER_PASSWORD environment variable must be set');
        }

        // Lambda function for tenant setup
        const tenantSetupFunction = new lambda_python.PythonFunction(this, 'TenantSetupFunction', {
            runtime: lambda.Runtime.PYTHON_3_11,
            index: 'tenant_setup.py',
            handler: 'handler',
            vpc: props.vpc,
            vpcSubnets: {
                subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS
            },
            securityGroups: [props.lambdaSecurityGroup],
            role: props.setupLambdaRole,
            entry: path.join(__dirname, '../../lambda/setup'),
            timeout: cdk.Duration.minutes(5),
            environment: {
                COGNITO_USER_POOL_ID: props.userPool.userPoolId,
                TABLE_NAME: props.mainTable.tableName,
                COGNITO_APP_CLIENT_ID: props.userPoolClient.userPoolClientId,
                OPENSEARCH_DOMAIN_A: props.openSearchDomainA.domainEndpoint,
                OPENSEARCH_DOMAIN_B: props.openSearchDomainB.domainEndpoint,
                BEDROCK_ACCESS_ROLE: bedrockRole.roleArn,
                DEMO_USER_PASSWORD: process.env.DEMO_USER_PASSWORD
            }
        });

        // add IAM permission
        tenantSetupFunction.addToRolePolicy(new iam.PolicyStatement({
            actions: [
                'cognito-idp:CreateUserPoolClient',
                'cognito-idp:DeleteUserPoolClient',
                'cognito-idp:ListUserPoolClients',
                'cognito-idp:AdminCreateUser',
                'cognito-idp:AdminDeleteUser',
                'cognito-idp:AdminSetUserPassword',
                'cognito-idp:Get*',
                'cognito-idp:AdminInitiateAuth'
            ],
            resources: [`arn:aws:cognito-idp:${region}:${account}:userpool/*`]
        }));

        tenantSetupFunction.addToRolePolicy(new iam.PolicyStatement({
            actions: [
                'dynamodb:PutItem',
                'dynamodb:DeleteItem',
                'dynamodb:GetItem',
                'dynamodb:UpdateItem'
            ],
            resources: [props.mainTable.tableArn]
        }));

        tenantSetupFunction.addToRolePolicy(new iam.PolicyStatement({
            actions: [
                'es:*'
            ],
            resources: [
                `${props.openSearchDomainA.domainArn}/*`,
                `${props.openSearchDomainB.domainArn}/*`,
                `${props.openSearchDomainA.domainArn}`,
                `${props.openSearchDomainB.domainArn}`
            ]
        }));

        tenantSetupFunction.addToRolePolicy(new iam.PolicyStatement({
            actions: ['iam:PassRole'],
            resources: [bedrockRole.roleArn]
        }));

        

        // Create custom resource provider
        const provider = new cr.Provider(this, 'TenantSetupProvider', {
            onEventHandler: tenantSetupFunction,
        });

        // Create custom resource
        new cdk.CustomResource(this, 'TenantSetupResource', {
            serviceToken: provider.serviceToken,
            properties: {
                BEDROCK_ACCESS_ROLE: bedrockRole.roleArn
            }
        });
  }
}
