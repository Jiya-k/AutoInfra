import boto3


def discover_ec2_instances(region: str | None = None) -> list[dict]:
    """
    Discover EC2 instances in a specific AWS region.
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


def get_available_regions() -> list[str]:
    """
    Retrieve AWS regions that are available to the account.

    Regions with opt-in status 'not-opted-in' are excluded.
    """

    ec2 = boto3.client("ec2")

    response = ec2.describe_regions(AllRegions=True)

    available_regions = []

    for region in response.get("Regions", []):
        opt_in_status = region.get("OptInStatus")

        if opt_in_status in ("opt-in-not-required", "opted-in"):
            available_regions.append(region["RegionName"])

    return sorted(available_regions)


def discover_ec2_instances_across_regions(
    regions: list[str] | None = None
) -> dict:
    """
    Discover EC2 instances across multiple AWS regions.

    Each region is processed independently. A failure in one
    region does not prevent discovery in the remaining regions.
    """

    if regions is None:
        regions = get_available_regions()

    successful_regions = []
    failed_regions = []
    discovered_instances = []

    for region in regions:
        try:
            instances = discover_ec2_instances(region=region)

            discovered_instances.extend(instances)
            successful_regions.append(region)

        except Exception as error:
            failed_regions.append({
                "region": region,
                "error": str(error)
            })

    return {
        "regions_checked": len(regions),
        "successful_regions": successful_regions,
        "failed_regions": failed_regions,
        "discovered": len(discovered_instances),
        "instances": discovered_instances
    }
