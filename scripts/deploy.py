#!/usr/bin/env python3
from __future__ import annotations

import base64
import http.cookiejar
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
CONNECTOR_FILE = PROJECT / "servicenow" / "USBEMCMDBLookupEventConnector.js"
SOURCE = "usbemCmdbLookup"
NAME = "USBEM CMDB Lookup"
SCOPE = "x_usbna_usb_event"
ROLE = "x_usbna_usb_event.cmdb_lookup_api"


def load_env() -> None:
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


class ServiceNow:
    def __init__(self) -> None:
        load_env()
        self.instance = os.environ["servicenow_instance"].rstrip("/")
        token = base64.b64encode(
            f"{os.environ['servicenow_user']}:{os.environ['servicenow_password']}".encode()
        ).decode()
        self.headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Basic " + token}

    def get(self, table: str, query: str, fields: str, limit: int = 20) -> list[dict]:
        url = f"{self.instance}/api/now/table/{table}?" + urllib.parse.urlencode({
            "sysparm_query": query, "sysparm_fields": fields, "sysparm_limit": str(limit)
        })
        with urllib.request.urlopen(urllib.request.Request(url, headers=self.headers), timeout=60) as response:
            return json.load(response)["result"]

    def background(self, script: str) -> None:
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        opener.open(self.instance + "/login.do", timeout=60).read()
        login = urllib.parse.urlencode({
            "user_name": os.environ["servicenow_user"], "user_password": os.environ["servicenow_password"], "sys_action": "sysverb_login"
        }).encode()
        opener.open(urllib.request.Request(self.instance + "/login.do", data=login, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=60).read()
        html = opener.open(self.instance + "/sys.scripts.do", timeout=60).read().decode("utf-8", "replace")
        match = re.search(r'name=["\']sysparm_ck["\'][^>]*value=["\']([^"\']+)', html) or re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']sysparm_ck', html)
        if not match:
            raise RuntimeError("Could not obtain the background-script CSRF token")
        data = urllib.parse.urlencode({"sysparm_ck": match.group(1), "runscript": "Run script", "sys_scope": "global", "script": script}).encode()
        opener.open(urllib.request.Request(self.instance + "/sys.scripts.do", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=240).read()


def installer(script_source: str) -> str:
    return """(function () {
var SOURCE = __SOURCE__, NAME = __NAME__, SCOPE = __SCOPE__, ROLE = __ROLE__, SCRIPT = __SCRIPT__;
function getOne(table, query) { var gr = new GlideRecord(table); gr.addEncodedQuery(query); gr.setLimit(1); gr.query(); return gr.next() ? gr : null; }
function set(gr, field, value) { if (gr.isValidField(field)) gr.setValue(field, value); }
function upsert(table, query, values) { var gr = getOne(table, query), exists = !!gr, key; if (!gr) { gr = new GlideRecord(table); gr.initialize(); } for (key in values) if (values.hasOwnProperty(key)) set(gr, key, values[key]); return String(exists ? gr.update() : gr.insert()); }
var scope = getOne('sys_scope', 'scope=' + SCOPE); if (!scope) throw 'Required scope not found: ' + SCOPE;
var scopeId = String(scope.getUniqueValue());
var roleId = upsert('sys_user_role', 'name=' + ROLE, {name: ROLE, description: 'Allows an approved integration identity to use the bounded USBEM CMDB lookup connector.', sys_scope: scopeId, sys_package: scopeId});
var scriptId = upsert('ecc_agent_script_include', 'name=' + SOURCE, {name: SOURCE, active: 'true', description: NAME + ' single-file read-only connector.', script: SCRIPT});
var listenerId = upsert('sn_em_connector_listener', 'source=' + SOURCE, {name: NAME, source: SOURCE, event_source_label: SOURCE, header_name: 'X-USBEM-Connector', header_value: SOURCE, type: '1', order: '100', active: 'true', description: 'Bounded CMDB lookup for approved Observability API identities.', script: SCRIPT, mid_server_script_include: scriptId});
var pushId = upsert('sn_em_connector_push_instance', 'name=' + SOURCE, {name: SOURCE, push_connector_definition: listenerId, active: 'true', latest_external_payloads: 'false', url: '/api/sn_em_connector/em/inbound_event?source=' + SOURCE, description: NAME});
gs.print(JSON.stringify({role: roleId, script: scriptId, listener: listenerId, push_instance: pushId}));
})();""".replace("__SOURCE__", json.dumps(SOURCE)).replace("__NAME__", json.dumps(NAME)).replace("__SCOPE__", json.dumps(SCOPE)).replace("__ROLE__", json.dumps(ROLE)).replace("__SCRIPT__", json.dumps(script_source))


def main() -> None:
    sn = ServiceNow()
    sn.background(installer(CONNECTOR_FILE.read_text(encoding="utf-8")))
    result = {
        "scope": sn.get("sys_scope", f"scope={SCOPE}", "sys_id,name,scope,version", 1),
        "role": sn.get("sys_user_role", f"name={ROLE}", "sys_id,name,description,sys_scope", 1),
        "listener": sn.get("sn_em_connector_listener", f"source={SOURCE}", "sys_id,name,source,active,header_name,header_value,sys_scope,mid_server_script_include", 1),
        "push_instance": sn.get("sn_em_connector_push_instance", f"name={SOURCE}", "sys_id,name,active,url,push_connector_definition", 1),
        "endpoint": f"{sn.instance}/api/sn_em_connector/em/inbound_event?source={SOURCE}",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
