import boto3
import json

# Constants
CLUSTER_NAME = "microservices"
REGION = "ap-south-1"
ROLE_NAME = "eksClusterRole1"
NODE_ROLE_NAME = "eksNodeRole1"

# Clients
eks = boto3.client("eks", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
ec2 = boto3.client("ec2", region_name=REGION)

def get_subnet_ids():
    print("Fetching subnet IDs from the default VPC...")
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    if not vpcs['Vpcs']:
        raise Exception("No default VPC found in the Mumbai region.")
    vpc_id = vpcs['Vpcs'][0]['VpcId']

    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets'][:2]]  # Pick 2
    print(f"Using subnets: {subnet_ids}")
    return subnet_ids

def create_iam_role(role_name, assume_policy, policy_arns):
    try:
        print(f"Creating IAM role: {role_name}")
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_policy)
        )
        role_arn = response['Role']['Arn']
        for policy_arn in policy_arns:
            iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        print(f"IAM role {role_name} created with ARN: {role_arn}")
        return role_arn
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"IAM role {role_name} already exists. Fetching ARN...")
        return iam.get_role(RoleName=role_name)['Role']['Arn']

def create_eks_cluster(cluster_name, role_arn, subnet_ids):
    print(f"Creating EKS Cluster: {cluster_name}")
    eks.create_cluster(
        name=cluster_name,
        version="1.29",
        roleArn=role_arn,
        resourcesVpcConfig={
            'subnetIds': subnet_ids,
            'endpointPublicAccess': True,
            'endpointPrivateAccess': False
        }
    )
    print("Waiting for EKS cluster to become ACTIVE...")
    waiter = eks.get_waiter('cluster_active')
    waiter.wait(name=cluster_name)
    print("✅ EKS Cluster is now ACTIVE.")

if __name__ == "__main__":
    cluster_assume_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "eks.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    cluster_policy_arns = [
        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
    ]

    node_assume_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    node_policy_arns = [
        "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
        "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    ]

    # Create IAM roles
    cluster_role_arn = create_iam_role(ROLE_NAME, cluster_assume_policy, cluster_policy_arns)
    node_role_arn = create_iam_role(NODE_ROLE_NAME, node_assume_policy, node_policy_arns)

    # Get Subnet IDs from Mumbai region
    subnet_ids = get_subnet_ids()

    # Create the EKS cluster
    create_eks_cluster(CLUSTER_NAME, cluster_role_arn, subnet_ids)

    # Instructions
    print("\n🎯 Next Steps:")
    print(f"1. Create a managed node group:")
    print(f"   eksctl create nodegroup --cluster {CLUSTER_NAME} --region {REGION} --name ng-1 \\")
    print(f"     --node-type t3.medium --nodes 2 --nodes-min 1 --nodes-max 3 \\")
    print(f"     --node-role {node_role_arn}")
    print("\n2. Configure kubectl:")
    print(f"   aws eks --region {REGION} update-kubeconfig --name {CLUSTER_NAME}")
    print("\n3. Deploy your app:")
    print(f"   kubectl apply -f k8s/")
