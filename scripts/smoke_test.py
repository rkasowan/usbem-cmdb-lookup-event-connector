#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
for raw in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

instance = os.environ["servicenow_instance"].rstrip("/")
token = base64.b64encode(f"{os.environ['servicenow_user']}:{os.environ['servicenow_password']}".encode()).decode()
url = instance + "/api/sn_em_connector/em/inbound_event?source=usbemCmdbLookup"
headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Basic " + token, "X-USBEM-Connector": "usbemCmdbLookup"}

payload = {"ci_type": "cmdb_ci", "ci_identifiers": [{"name": "__USBEM_LOOKUP_EXPECTED_MISS__"}, {"sys_id": "00000000000000000000000000000000"}]}
request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
with urllib.request.urlopen(request, timeout=60) as response:
    result = json.load(response)
if "result" in result:
    envelope = result["result"]
    if not isinstance(envelope, dict) or len(envelope) != 1:
        raise RuntimeError("Unexpected Event Connector response envelope")
    result = json.loads(next(iter(envelope.values())))
if "success" not in result:
    raise RuntimeError("Unexpected connector response: " + json.dumps(result))
assert result["success"] is True
assert result["identifier_count"] == 2
assert result["match_count"] == 0
assert len(result["identifier_results"]) == 2
print(json.dumps({"http_status": 200, "success": result["success"], "identifier_count": result["identifier_count"], "match_count": result["match_count"]}, indent=2))
