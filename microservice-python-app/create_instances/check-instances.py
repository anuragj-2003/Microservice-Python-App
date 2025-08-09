import boto3

def list_running_ec2_instances(region='ap-south-1'):
    ec2 = boto3.client('ec2', region_name=region)
    print("\n🔍 Checking EC2 Instances...")
    instances = ec2.describe_instances(Filters=[
        {'Name': 'instance-state-name', 'Values': ['running']}
    ])
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            print(f"➡️ EC2 Instance ID: {instance['InstanceId']} | Type: {instance['InstanceType']}")

def list_eks_clusters(region='ap-south-1'):
    eks = boto3.client('eks', region_name=region)
    print("\n🔍 Checking EKS Clusters...")
    clusters = eks.list_clusters()['clusters']
    for cluster in clusters:
        desc = eks.describe_cluster(name=cluster)['cluster']
        print(f"➡️ EKS Cluster Name: {cluster} | Status: {desc['status']}")

def list_running_rds_instances(region='ap-south-1'):
    rds = boto3.client('rds', region_name=region)
    print("\n🔍 Checking RDS Instances...")
    instances = rds.describe_db_instances()['DBInstances']
    for db in instances:
        if db['DBInstanceStatus'] == 'available':
            print(f"➡️ RDS DB Instance Identifier: {db['DBInstanceIdentifier']} | Engine: {db['Engine']}")

if __name__ == "__main__":
    region = 'ap-south-1'  # Asia Pacific (Mumbai)
    list_running_ec2_instances(region)
    list_eks_clusters(region)
    list_running_rds_instances(region)

