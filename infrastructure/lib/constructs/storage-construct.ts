import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as opensearch from 'aws-cdk-lib/aws-opensearchservice';
import { AuthConstruct } from './auth-construct';
import { Stack } from 'aws-cdk-lib';
import { NagSuppressions } from 'cdk-nag';

interface StorageConstructProps {
  vpc: ec2.IVpc;
  authConstruct: AuthConstruct;
  openSearchSecurityGroup: ec2.SecurityGroup;
}

export class StorageConstruct extends Construct {
  public readonly mainTable: dynamodb.Table;
  public readonly fileBucket: s3.Bucket;
  public readonly openSearchDomainA: opensearch.Domain;
  public readonly openSearchDomainB: opensearch.Domain;
  public readonly setupLambdaRole: iam.Role;

  constructor(scope: Construct, id: string, props: StorageConstructProps) {
    super(scope, id);

    this.setupLambdaRole = new iam.Role(this, 'SetupLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for setup Lambda and OpenSearch master user'
    });

    this.setupLambdaRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole')
    );

    this.mainTable = this.createDynamoDBTable();
    this.fileBucket = this.createS3Bucket();
    this.openSearchDomainA = this.createOpenSearchDomain(props, 'A');
    this.openSearchDomainB = this.createOpenSearchDomain(props, 'B');

    
  }

  private createDynamoDBTable(): dynamodb.Table {
    return new dynamodb.Table(this, 'MainTable', {
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
  }

  private createS3Bucket(): s3.Bucket {
    return new s3.Bucket(this, 'FileBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      cors: [
        {
          allowedHeaders: ['*'],
          allowedMethods: [
            s3.HttpMethods.GET,
            s3.HttpMethods.PUT,
            s3.HttpMethods.POST,
            s3.HttpMethods.DELETE,
            s3.HttpMethods.HEAD,
          ],
          allowedOrigins: [process.env.CORS_ALLOWED_ORIGIN || '*'],
          exposedHeaders: [],
          maxAge: 60
        }
      ]
    });
  }


  private createOpenSearchDomain(props: StorageConstructProps, suffix: string): opensearch.Domain {
    const domain = new opensearch.Domain(this, `OpenSearchDomain${suffix}`, {
      version: opensearch.EngineVersion.OPENSEARCH_2_17,
      vpc: props.vpc,
      vpcSubnets: [
        {
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS
        }
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      securityGroups: [props.openSearchSecurityGroup],
      capacity: {
        dataNodes: 1,
        dataNodeInstanceType: 'm5.large.search',
        multiAzWithStandbyEnabled: false
      },
      ebs: {
        volumeSize: 10,
        volumeType: ec2.EbsDeviceVolumeType.GP3,
      },
      nodeToNodeEncryption: true,
      encryptionAtRest: {
        enabled: true,
      },
      enforceHttps: true,
      fineGrainedAccessControl: {
        masterUserArn: this.setupLambdaRole.roleArn
      },
      accessPolicies: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          principals: [new iam.AnyPrincipal()],
          actions: ['es:ESHttp*'],
          resources: ['*']
        })
      ],
    });
  
    domain.applyRemovalPolicy(cdk.RemovalPolicy.DESTROY);

    NagSuppressions.addResourceSuppressions(domain, [
      {
        id: 'AwsPrototyping-OpenSearchNoUnsignedOrAnonymousAccess',
        reason: 'JWT authentication will be configured later'
      }
    ]);
  
    return domain;
  }  
}