#!/bin/bash
set -euxo pipefail

# Purpose in life:
# Generate a username for ide users

USER_SUFFIX=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 13; echo)
USER_SUFFIX=$(echo "$USER_SUFFIX" | tr '[:upper:]' '[:lower:]')

echo "$USER_SUFFIX"
