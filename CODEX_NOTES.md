# Current state

- Deployed 2026-09-10 to the PDI as Event push listener `USBEM CMDB Lookup`.
- Source and header value: `usbemCmdbLookup`.
- Endpoint: `/api/sn_em_connector/em/inbound_event?source=usbemCmdbLookup`.
- Scoped authorization role: `x_usbna_usb_event.cmdb_lookup_api`; role assignment is intentionally manual.
- Listener sys_id: `cca4e5fc939fc7d0c8ebf85bdd03d681`.
- Push instance sys_id: `9ca4e5fc939fc7d0c8ebf85bdd03d68b`.
- Connector script record sys_id: `3744a1bc939fc7d0c8ebf85bdd03d66f`.
- Validated display class `Business Application` -> `cmdb_ci_business_app` and technical class `cmdb_ci_server`.
- The only accepted lookup input is the singular nested `ci_identifier` object. Its fields use AND semantics and may name any valid inherited/class field. Results serialize all fields with raw and display values.
- Scoped runtime compatibility: field enumeration uses `sys_dictionary` over the CI inheritance hierarchy. Do not introduce `GlideRecord.getFields()` or `getElements()`.
