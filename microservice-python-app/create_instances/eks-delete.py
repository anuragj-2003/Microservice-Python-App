import boto3
import time
import botocore

CLUSTER_NAME = "microservices"
REGION = "ap-south-1"
ROLE_NAMES = ["eksClusterRole1", "eksNodeRole1"]

eks = boto3.client("eks", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
ec2 = boto3.client("ec2", region_name=REGION)

def delete_eks_cluster():
    try:
        print(f"Deleting EKS cluster: {CLUSTER_NAME}")
        eks.delete_cluster(name=CLUSTER_NAME)
        print("Waiting for cluster deletion to complete...")
        waiter = eks.get_waiter("cluster_deleted")
        waiter.wait(name=CLUSTER_NAME)
        print("✅ EKS cluster deleted.")
    except botocore.exceptions.ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print("Cluster not found. Skipping deletion.")
        else:
            raise

def detach_and_delete_role(role_name):
    try:
        print(f"\nDetaching policies and deleting IAM role: {role_name}")
        # List attached policies
        policies = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
        for policy in policies:
            print(f"Detaching policy: {policy['PolicyArn']}")
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])

        # Delete the role
        iam.delete_role(RoleName=role_name)
        print(f"✅ IAM role {role_name} deleted.")
    except iam.exceptions.NoSuchEntityException:
        print(f"IAM role {role_name} does not exist. Skipping.")

def delete_nodegroups():
    try:
        response = eks.list_nodegroups(clusterName=CLUSTER_NAME)
        nodegroups = response.get("nodegroups", [])
        for ng in nodegroups:
            print(f"Deleting node group: {ng}")
            eks.delete_nodegroup(clusterName=CLUSTER_NAME, nodegroupName=ng)
            print("Waiting for node group to delete...")
            waiter = eks.get_waiter("nodegroup_deleted")
            waiter.wait(clusterName=CLUSTER_NAME, nodegroupName=ng)
            print(f"✅ Node group {ng} deleted.")
    except Exception as e:
        print(f"⚠️ Node group deletion skipped or failed: {e}")

if __name__ == "__main__":
    print("🚨 WARNING: This script will delete the EKS cluster, node groups, and IAM roles.")
    confirm = input("Type 'DELETE' to continue: ")
    if confirm != "DELETE":
        print("Aborted.")
        exit(0)

    delete_nodegroups()
    delete_eks_cluster()
    for role in ROLE_NAMES:
        detach_and_delete_role(role)

    print("\n🧹 Cleanup complete.")
