import boto3


def discover_ec2_instances(region: str | None = None) -> list[dict]:
    """
    Discover EC2 instances in the configured AWS region.

    Returns an empty list if no EC2 instances are found.
    """

    ec2 = boto3.client("ec2", region_name=region)

    paginator = ec2.get_paginator("describe_instances")

    discovered_instances = []

    for page in paginator.paginate():
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):

                tags = {
                    tag["Key"]: tag["Value"]
                    for tag in instance.get("Tags", [])
                }

                instance_id = instance["InstanceId"]

                discovered_instances.append({
                    "name": tags.get("Name", instance_id),
                    "provider": "AWS",
                    "instance_id": instance_id,
                    "region": ec2.meta.region_name,
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "status": instance.get(
                        "State", {}
                    ).get("Name", "unknown"),
                    "operating_system": (
                        instance.get("PlatformDetails")
                        or instance.get("Platform")
                        or "Linux/Unix"
                    )
                })

    return discovered_instances
