from unittest.mock import MagicMock, patch

from app.services.aws_discovery import discover_ec2_instances


def test_discovery_returns_empty_list_when_no_instances():
    """Verify that empty AWS accounts are handled correctly."""

    mock_ec2 = MagicMock()
    mock_ec2.meta.region_name = "ap-south-1"
    mock_ec2.get_paginator.return_value.paginate.return_value = [
        {"Reservations": []}
    ]

    with patch(
        "app.services.aws_discovery.boto3.client",
        return_value=mock_ec2
    ) as mock_client:

        result = discover_ec2_instances(region="ap-south-1")

    mock_client.assert_called_once_with(
        "ec2", region_name="ap-south-1"
    )
    assert result == []


def test_discovery_returns_ec2_instance_details():
    """Verify that EC2 details are mapped correctly."""

    mock_ec2 = MagicMock()
    mock_ec2.meta.region_name = "ap-south-1"

    mock_ec2.get_paginator.return_value.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "running"},
                            "PrivateIpAddress": "10.0.1.10",
                            "PublicIpAddress": "13.233.10.20",
                            "PlatformDetails": "Linux/UNIX",
                            "Tags": [
                                {"Key": "Name", "Value": "test-server"}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    with patch(
        "app.services.aws_discovery.boto3.client",
        return_value=mock_ec2
    ):

        result = discover_ec2_instances(region="ap-south-1")

    assert len(result) == 1

    assert result[0] == {
        "name": "test-server",
        "provider": "AWS",
        "instance_id": "i-1234567890abcdef0",
        "region": "ap-south-1",
        "private_ip": "10.0.1.10",
        "public_ip": "13.233.10.20",
        "status": "running",
        "operating_system": "Linux/UNIX"
    }


def test_discovery_uses_instance_id_when_name_tag_is_missing():
    """Verify that instances without a Name tag still have a name."""

    mock_ec2 = MagicMock()
    mock_ec2.meta.region_name = "ap-south-1"

    mock_ec2.get_paginator.return_value.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-abcdef1234567890",
                            "State": {"Name": "stopped"}
                        }
                    ]
                }
            ]
        }
    ]

    with patch(
        "app.services.aws_discovery.boto3.client",
        return_value=mock_ec2
    ):

        result = discover_ec2_instances(region="ap-south-1")

    assert len(result) == 1
    assert result[0]["name"] == "i-abcdef1234567890"
    assert result[0]["status"] == "stopped"
    assert result[0]["private_ip"] is None
    assert result[0]["public_ip"] is None


def test_discovery_processes_multiple_pages():
    """Verify that all paginator pages are processed."""

    mock_ec2 = MagicMock()
    mock_ec2.meta.region_name = "ap-south-1"

    mock_ec2.get_paginator.return_value.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-first",
                            "State": {"Name": "running"}
                        }
                    ]
                }
            ]
        },
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-second",
                            "State": {"Name": "stopped"}
                        }
                    ]
                }
            ]
        }
    ]

    with patch(
        "app.services.aws_discovery.boto3.client",
        return_value=mock_ec2
    ):

        result = discover_ec2_instances(region="ap-south-1")

    assert len(result) == 2
    assert result[0]["instance_id"] == "i-first"
    assert result[1]["instance_id"] == "i-second"
