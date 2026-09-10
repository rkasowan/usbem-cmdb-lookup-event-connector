# Production transfer inventory

- Event Connector script: `servicenow/USBEMCMDBLookupEventConnector.js`
- Push listener name: `USBEM CMDB Lookup`
- Source: `usbemCmdbLookup`
- Header: `X-USBEM-Connector: usbemCmdbLookup`
- Scoped role: `x_usbna_usb_event.cmdb_lookup_api`
- Target application scope: `USB Event Management` (`x_usbna_usb_event`)
- Authentication: target-owned integration identity; no credential is transported
- Manual step: assign the scoped role to only the approved Observability API identity
- Rollback: deactivate the listener and remove the role assignment

The installer resolves the target scope by its stable scope name and does not transport instance-specific sys_ids.
