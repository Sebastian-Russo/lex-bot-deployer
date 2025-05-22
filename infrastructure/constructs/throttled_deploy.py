import math
from constructs import Construct
from typing import List


def throttled_deploy(constructs: List[Construct], parallelism: int = 2) -> None:
    """
    Allows you to control how many resources can be deployed at once
    Use this to slow down your deploy and avoid AWS API Throttling
    If you get an `internal error`, you may want to reduce parallelism

    Args:
        constructs: List of constructs to deploy
        parallelism: Number of parallel deployments, default 2, use 1 for sequential
    """
    """
    This splits your resources into groups based on the parallelism value. With 6 resources and parallelism=2, you'd get 3 resources per chunk.This splits your resources into groups based on the parallelism value. With 6 resources and parallelism=2, you'd get 3 resources per chunk.
    """
    assert parallelism > 0, 'Parallelism must be greater than 0'

    """
    This is the critical part. It creates a chain of dependencies between resources in each chunk:This creates a loop that iterates over the chunks of resources.
    """
    # Create resource chunks which will be deployed sequentially
    chunk_size = math.ceil(len(constructs) / parallelism)
    for i in range(0, len(constructs), chunk_size):
        chunk = constructs[i : i + chunk_size]
        # print(f"Chunk length: {len(chunk)}")

        for index, resource in enumerate(chunk):
            if index > 0:
                previous = chunk[index - 1]
                # print(f"Current: {resource.node.id}, Previous: {previous.node.id}")
                resource.node.add_dependency(previous)
