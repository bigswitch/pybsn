#!/usr/bin/env python
"""
Example demonstrating retry configuration with pybsn.connect()

This example shows how to configure automatic retries for failed HTTP requests
to improve reliability when connecting to BigDB.
"""
import argparse

from urllib3.util.retry import Retry

import pybsn

parser = argparse.ArgumentParser(description="Demonstrate retry configuration")
parser.add_argument("--host", "-H", type=str, default="127.0.0.1", help="Controller IP/Hostname to connect to")
parser.add_argument("--user", "-u", type=str, default="admin", help="Username")
parser.add_argument("--password", "-p", type=str, default="adminadmin", help="Password")

args = parser.parse_args()


def example_simple_retry():
    """Example 1: Simple integer retry count (retries GET requests 3 times)"""
    print("Example 1: Simple integer retry count")
    client = pybsn.connect(args.host, args.user, args.password, retries=3)

    # This will retry up to 3 times on connection errors or certain HTTP status codes
    # By default, only idempotent methods (GET, HEAD, OPTIONS, TRACE) are retried
    switches = client.root.core.switch()
    print(f"  Found {len(switches)} switches")


def example_custom_retry():
    """Example 2: Custom Retry object with specific configuration"""
    print("\nExample 2: Custom Retry with status codes and backoff")

    # Configure retry with:
    # - 5 total retry attempts
    # - Exponential backoff with 1 second base delay
    # - Retry on specific HTTP status codes (503, 504)
    retry_config = Retry(
        total=5,
        backoff_factor=1,  # Wait 1s, 2s, 4s, 8s, 16s between retries
        status_forcelist=[503, 504],  # Retry on Service Unavailable and Gateway Timeout
    )

    client = pybsn.connect(args.host, args.user, args.password, retries=retry_config)

    # This will retry on 503/504 errors with exponential backoff
    switches = client.root.core.switch()
    print(f"  Found {len(switches)} switches with custom retry config")


def example_retry_non_idempotent():
    """Example 3: Retry non-idempotent methods (use with caution!)"""
    print("\nExample 3: Retry non-idempotent methods (POST, PUT, PATCH, DELETE)")

    # By default, only safe/idempotent methods are retried
    # To retry POST/PUT/PATCH/DELETE, explicitly configure allowed_methods
    # WARNING: Only use this if your operations are truly idempotent!
    retry_config = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[503],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Include non-idempotent methods
    )

    client = pybsn.connect(args.host, args.user, args.password, retries=retry_config)

    # Now POST/PUT/PATCH/DELETE operations will also retry on failures
    # Use with caution - ensure your operations are idempotent!
    switches = client.root.core.switch()
    print(f"  Found {len(switches)} switches (with non-idempotent retry enabled)")


def example_no_retry():
    """Example 4: No retry (default behavior)"""
    print("\nExample 4: No retry (default behavior)")

    # Default behavior - no automatic retries
    client = pybsn.connect(args.host, args.user, args.password)

    # Failures will raise immediately without retry
    switches = client.root.core.switch()
    print(f"  Found {len(switches)} switches (no retry)")


if __name__ == "__main__":
    print("=== pybsn Retry Configuration Examples ===\n")

    # Run all examples
    example_simple_retry()
    example_custom_retry()
    example_retry_non_idempotent()
    example_no_retry()

    print("\n=== Examples completed ===")
