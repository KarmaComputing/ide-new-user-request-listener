#!/bin/bash

set -xuo pipefail


# Chuck some request at the endpoint and verify we get a username back
curl -H "x-forwarded-for: 10.0.0.1" http://127.0.0.1:5123/new-username | grep -E '{"username": "[A-Za-z0-9]*{13}"'

RETURN_CODE=$?
echo $RETURN_CODE

if [ $RETURN_CODE -ne 0 ];then
  echo new-username test failed
  exit 1
fi

echo Pass
