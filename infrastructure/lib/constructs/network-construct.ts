import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';

export class NetworkConstruct extends Construct {
  public readonly vpc: ec2.Vpc;
  public readonly lambdaSecurityGroup: ec2.SecurityGroup;
  public readonly openSearchSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.vpc = this.createVpc();
    this.setupFlowLogs();
    this.lambdaSecurityGroup = this.createLambdaSecurityGroup();
    this.openSearchSecurityGroup = this.createOpenSearchSecurityGroup();
  }

  

  private createVpc(): ec2.Vpc {
    return new ec2.Vpc(this, 'MyVPC', {
      maxAzs: 1,
      natGateways: 1,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          cidrMask: 24,
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          mapPublicIpOnLaunch: false
        }
      ],
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
      flowLogs: {},
    });
  }

  private setupFlowLogs() {
    const account = cdk.Stack.of(this).account;
    
    const flowLogRole = new iam.Role(this, 'FlowLogRole', {
      assumedBy: new iam.ServicePrincipal('vpc-flow-logs.amazonaws.com')
        .withConditions({
          'StringEquals': {
            'aws:SourceAccount': account
          }
        })
    });

    const flowLogGroup = new logs.LogGroup(this, 'FlowLogGroup', {
      retention: logs.RetentionDays.THREE_DAYS,
    });

    new ec2.FlowLog(this, 'FlowLog', {
      resourceType: ec2.FlowLogResourceType.fromVpc(this.vpc),
      destination: ec2.FlowLogDestination.toCloudWatchLogs(flowLogGroup, flowLogRole),
    });
  }

  private createLambdaSecurityGroup(): ec2.SecurityGroup {
    const sg = new ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
      vpc: this.vpc,
      allowAllOutbound: false,
      description: 'Security group for Lambda functions',
    });

    sg.addEgressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      'Allow HTTPS outbound traffic'
    );

    

    return sg;
  }

  private createOpenSearchSecurityGroup(): ec2.SecurityGroup {
    const sg =new ec2.SecurityGroup(this, 'OpenSearchSecurityGroup', {
      vpc: this.vpc,
      description: 'Security group for OpenSearch',
      allowAllOutbound: false
    });
    sg.addIngressRule(
      ec2.Peer.securityGroupId(this.lambdaSecurityGroup.securityGroupId),
      ec2.Port.tcp(443),
      'Allow HTTPS inbound traffic from Lambda'
    );

    return sg;

  }
}