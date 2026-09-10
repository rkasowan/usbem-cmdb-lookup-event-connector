#!/usr/bin/env python3
from __future__ import annotations

import json
import re

from deploy import ServiceNow, SCOPE

MARKER = "USBEM_WRAPPER_TEST="
SCRIPT = r"""
(function () {
    var result = {cmdb_allowed: false, non_cmdb_rejected: false, fields_count: 0, elements_count: 0};
    var ci = new GlideRecord('cmdb_ci_business_app');
    ci.setLimit(1);
    ci.query();
    if (!ci.next()) throw 'A Business Application CI is required for the wrapper test.';
    var wrapper = new global.USBEMCMDBFieldEnumerator();
    var fields = wrapper.getFields(ci);
    var elements = wrapper.getElements(ci);
    result.fields_count = fields.length;
    result.elements_count = elements.length;
    result.cmdb_allowed = fields.length > 0 && elements.length > 0;
    try {
        var incident = new GlideRecord('incident');
        wrapper.getFields(incident);
    } catch (expected) {
        result.non_cmdb_rejected = String(expected).indexOf('is not cmdb_ci or an extending table') >= 0;
    }
    gs.print('USBEM_WRAPPER_TEST=' + JSON.stringify(result));
})();
"""


def main() -> None:
    html = ServiceNow().background(SCRIPT, SCOPE)
    match = re.search(r"USBEM_WRAPPER_TEST=(\{[^<\r\n]+\})", html)
    if not match:
        raise RuntimeError("Scoped wrapper test did not return its result marker")
    result = json.loads(match.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    print(json.dumps(result, indent=2))
    assert result["cmdb_allowed"] is True
    assert result["non_cmdb_rejected"] is True
    assert result["fields_count"] > 0
    assert result["elements_count"] > 0


if __name__ == "__main__":
    main()
