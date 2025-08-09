import boto3
import time

# AWS region
REGION = 'ap-south-1'

# Initialize boto3 clients
ec2 = boto3.client('ec2', region_name=REGION)

def create_default_vpc():
    print("Creating a default VPC in the Mumbai region...")

    # Create VPC
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = vpc['Vpc']['VpcId']
    print(f"Created VPC with ID: {vpc_id}")
    
    # Enable DNS support and DNS hostnames
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    
    # Create Internet Gateway and attach it to the VPC
    igw = ec2.create_internet_gateway()
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Internet Gateway {igw_id} attached to VPC {vpc_id}")
    
    # Fetch valid Availability Zones for the Mumbai region
    azs = ec2.describe_availability_zones()
    valid_azs = [az['ZoneId'] for az in azs['AvailabilityZones'] if az['State'] == 'Available']
    
    # Ensure there are at least two valid AZs
    if len(valid_azs) < 2:
        print("Not enough available Availability Zones in the Mumbai region. Retrying...")
        time.sleep(5)  # Wait for 5 seconds before retrying
        azs = ec2.describe_availability_zones()  # Try fetching AZs again
        valid_azs = [az['ZoneId'] for az in azs['AvailabilityZones'] if az['State'] == 'Available']
        if len(valid_azs) < 2:
            raise Exception("Still not enough available Availability Zones in the Mumbai region.")

    # Create subnets in different Availability Zones
    subnets = []
    for i, az in enumerate(valid_azs[:2]):  # Select only the first two AZs
        subnet = ec2.create_subnet(
            CidrBlock=f'10.0.{i}.0/24',
            VpcId=vpc_id,
            AvailabilityZone=az
        )
        subnets.append(subnet['Subnet']['SubnetId'])
        print(f"Created subnet {subnet['Subnet']['SubnetId']} in AZ {az}")

    # Create a route table
    route_table = ec2.create_route_table(VpcId=vpc_id)
    route_table_id = route_table['RouteTable']['RouteTableId']
    print(f"Created Route Table with ID: {route_table_id}")

    # Create a route to the Internet Gateway
    ec2.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=igw_id
    )
    print(f"Created route for internet access in Route Table {route_table_id}")
    
    # Associate route table with subnets
    for subnet_id in subnets:
        ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=route_table_id)
        print(f"Associated route table with subnet {subnet_id}")

    # Create a default security group
    security_group = ec2.create_security_group(
        GroupName='default-sg',
        Description='Default security group for the VPC',
        VpcId=vpc_id
    )
    sg_id = security_group['GroupId']
    print(f"Created Security Group {sg_id}")

    # Allow inbound HTTP and HTTPS traffic
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpProtocol='tcp',
        FromPort=80,
        ToPort=80,
        CidrIp='0.0.0.0/0'
    )
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpProtocol='tcp',
        FromPort=443,
        ToPort=443,
        CidrIp='0.0.0.0/0'
    )
    print(f"Security Group {sg_id} allows inbound HTTP/HTTPS traffic")

    return vpc_id, subnets, sg_id, igw_id, route_table_id


if __name__ == '__main__':
    try:
        vpc_id, subnets, sg_id, igw_id, route_table_id = create_default_vpc()
        print("\nDefault VPC and all associated resources have been successfully created!")
        print(f"VPC ID: {vpc_id}")
        print(f"Subnets: {subnets}")
        print(f"Security Group ID: {sg_id}")
        print(f"Internet Gateway ID: {igw_id}")
        print(f"Route Table ID: {route_table_id}")
    except Exception as e:
        print(f"An error occurred: {e}")
