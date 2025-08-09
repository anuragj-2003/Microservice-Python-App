import boto3

def get_subnet_ids():
    print("Fetching subnet IDs from the VPC...")
    vpc_id = 'vpc-007a076bcdb557cb9'  # Your VPC ID
    REGION = "ap-south-1"
    ec2 = boto3.client("ec2", region_name=REGION)
    
    # Fetch subnets in multiple AZs
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

    # Debug: print raw response
    print("Raw Subnet Response:", subnets)
    
    if 'Subnets' not in subnets or not subnets['Subnets']:
        print("No subnets found in the VPC.")
        return []

    print("Available subnets and their AZs:")
    for subnet in subnets['Subnets']:
        print(f"Subnet ID: {subnet['SubnetId']}, AZ: {subnet['AvailabilityZone']}")

    # Get subnets from different AZs
    subnet_ids = []
    azs = set()  # To ensure we're getting subnets from different AZs
    
    for subnet in subnets['Subnets']:
        if subnet['AvailabilityZone'] not in azs:
            subnet_ids.append(subnet['SubnetId'])
            azs.add(subnet['AvailabilityZone'])
        if len(azs) == 2:  # We only need two subnets from different AZs
            break
    
    if len(azs) < 2:
        raise Exception("Not enough subnets in different AZs found.")
    
    print(f"Using subnets: {subnet_ids}")
    return subnet_ids

# Run the function
get_subnet_ids()
