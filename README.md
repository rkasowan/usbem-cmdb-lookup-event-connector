# USBEM CMDB Lookup Event Connector

A narrowly governed, read-only Event Management push connector that lets an approved Observability integration resolve CIs without direct CMDB table access.

## Endpoint

`POST /api/sn_em_connector/em/inbound_event?source=usbemCmdbLookup`

Required header: `X-USBEM-Connector: usbemCmdbLookup`

The authenticated integration user must have `x_usbna_usb_event.cmdb_lookup_api`. Do not grant that role to interactive users or broad groups.

## Request contract

One Event-style identifier object:

```json
{
  "ci_type": "Business Application",
  "ci_identifier": {"serial_number": "ABC123", "name": "app01"}
}
```

`ci_type` accepts either the technical class name (`cmdb_ci_server`) or its exact display name (`Business Application`). The fields inside one identifier object are combined with AND, matching Event Management's JSON `ci_identifier` shape. Every real field inherited or defined on the selected class can be used. A JSON-encoded string is also accepted.

## Guardrails

- Exact matches only; no caller-supplied encoded queries or operators.
- `ci_type` must be a real class extending `cmdb_ci`.
- Identifier keys must resolve to real fields on the selected CI class. Caller-supplied operators and encoded queries are not accepted.
- Maximum 100 matching records per response; `truncated` reports when the limit is reached.
- Matching records include every field available on the resolved class, with raw and display values. Field names are resolved from `sys_dictionary` across the class hierarchy; the connector does not call scoped-prohibited `getFields()` or `getElements()` APIs.
- The endpoint is service-mediated access. It does not grant Table API or list access to CMDB.

## Deployment and rollback

Run `python3 scripts/deploy.py`. Assign the role only to the intended API identity, then use the smoke examples in `scripts/smoke_test.py`.

Rollback by deactivating the `USBEM CMDB Lookup` listener and removing the role from the integration identity. No CMDB records are created or changed.

## Global field-enumeration wrapper

`global.USBEMCMDBFieldEnumerator` safely wraps the otherwise scope-sensitive `GlideRecord.getFields()` and `GlideRecord.getElements()` methods. Both wrapper methods return a plain JavaScript array of technical field names. They reject every GlideRecord whose table is not `cmdb_ci` or a descendant.

```javascript
var ci = new GlideRecord('cmdb_ci_server');
ci.setLimit(1);
ci.query();
ci.next();

var fields = new global.USBEMCMDBFieldEnumerator().getFields(ci);
var elements = new global.USBEMCMDBFieldEnumerator().getElements(ci);
```

The Script Include is Global, accessible from all application scopes with caller tracking, and has an explicit allowed execute privilege for `x_usbna_usb_event`. The table restriction is enforced again inside every public method.

The two methods intentionally preserve their underlying platform behavior. On the validation Business Application record, `getFields()` returned 115 unique names while `getElements()` returned 116. Prefer `getElements()` when the caller needs the most complete enumeration on this instance.
