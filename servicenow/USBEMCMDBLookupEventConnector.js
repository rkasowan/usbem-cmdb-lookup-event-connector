(function process(/*RESTAPIRequest*/ request, body) {
    var REQUIRED_ROLE = 'x_usbna_usb_event.cmdb_lookup_api';
    var MAX_TOTAL_MATCHES = 100;

    function text(value) {
        return value === null || typeof value === 'undefined' ? '' : String(value);
    }

    function trim(value) {
        return text(value).replace(/^\s+|\s+$/g, '');
    }

    function contains(list, value) {
        var i;
        for (i = 0; i < list.length; i++) {
            if (list[i] === value) return true;
        }
        return false;
    }

    function parseJson(value, label) {
        if (typeof value !== 'string') return value;
        try {
            return JSON.parse(value);
        } catch (ex) {
            throw new Error(label + ' must be valid JSON when supplied as a string.');
        }
    }

    function parseBody(raw) {
        var parsed = parseJson(raw, 'Request body');
        if (!parsed || typeof parsed !== 'object' || parsed instanceof Array) {
            throw new Error('Request body must be a JSON object.');
        }
        return parsed;
    }

    function ciIdentifier(input) {
        var identifier = input.ci_identifier;
        if (!identifier || typeof identifier !== 'object' || identifier instanceof Array) {
            throw new Error('ci_identifier is required and must be a nested JSON object.');
        }
        return identifier;
    }

    function isCmdbClass(tableName) {
        var current = tableName;
        var visited = {};
        var dbo;
        var parent;
        while (current && !visited[current]) {
            if (current === 'cmdb_ci') return true;
            visited[current] = true;
            dbo = new GlideRecord('sys_db_object');
            dbo.addQuery('name', current);
            dbo.setLimit(1);
            dbo.query();
            if (!dbo.next()) return false;
            parent = dbo.getValue('super_class');
            if (!parent) return false;
            dbo = new GlideRecord('sys_db_object');
            if (!dbo.get(parent)) return false;
            current = text(dbo.getValue('name'));
        }
        return false;
    }

    function resolveCiType(value) {
        var requested = trim(value);
        var dbo = new GlideRecord('sys_db_object');
        var matches = [];
        var tableName;
        dbo.addQuery('name', requested).addOrCondition('label', requested);
        dbo.setLimit(3);
        dbo.query();
        while (dbo.next()) {
            tableName = text(dbo.getValue('name'));
            if (isCmdbClass(tableName)) matches.push({name: tableName, label: text(dbo.getValue('label'))});
        }
        if (!matches.length) throw new Error('ci_type must be a valid CMDB class name or exact display name.');
        if (matches.length > 1) throw new Error('ci_type display name is ambiguous; use the technical class name.');
        return matches[0];
    }

    function validateIdentifier(gr, identifier) {
        var field;
        var count = 0;
        for (field in identifier) {
            if (!identifier.hasOwnProperty(field)) continue;
            count++;
            if (!gr.isValidField(field)) {
                throw new Error('Identifier field ' + field + ' is not valid for ' + gr.getTableName() + '.');
            }
            if (!trim(identifier[field])) {
                throw new Error('Identifier values cannot be blank (field ' + field + ').');
            }
        }
        if (!count) throw new Error('ci_identifier cannot be empty.');
    }

    function fieldValue(gr, field) {
        return {
            value: text(gr.getValue(field)),
            display_value: text(gr.getDisplayValue(field))
        };
    }

    function serialize(gr) {
        var record = { table: gr.getTableName(), sys_id: text(gr.getUniqueValue()), fields: {} };
        var elements = gr.getFields();
        var i;
        var field;
        var item;
        for (i = 0; i < elements.size(); i++) {
            field = text(elements.get(i).getName());
            if (!field || !gr.isValidField(field)) continue;
            item = fieldValue(gr, field);
            record.fields[field] = item;
        }
        record.display_value = text(gr.getDisplayValue());
        return record;
    }

    function lookup(tableName, identifier) {
        var records = [];
        var truncated = false;
        var field;
        var gr;
        gr = new GlideRecord(tableName);
        validateIdentifier(gr, identifier);
        for (field in identifier) {
            if (identifier.hasOwnProperty(field)) gr.addQuery(field, trim(identifier[field]));
        }
        gr.setLimit(MAX_TOTAL_MATCHES + 1);
        gr.query();
        while (gr.next()) {
            if (records.length >= MAX_TOTAL_MATCHES) {
                truncated = true;
                break;
            }
            records.push(serialize(gr));
        }
        return { records: records, truncated: truncated };
    }

    var payload = {};
    try {
        if (!gs.hasRole(REQUIRED_ROLE) && !gs.hasRole('admin')) {
            if (typeof status !== 'undefined') status = 403;
            return JSON.stringify({ success: false, status: 'forbidden', message: 'The ' + REQUIRED_ROLE + ' role is required.' });
        }
        payload = parseBody(body);
        var ciTypeInput = trim(payload.ci_type);
        if (!ciTypeInput) throw new Error('ci_type is required.');
        var resolvedType = resolveCiType(ciTypeInput);
        var ciType = resolvedType.name;
        var identifier = ciIdentifier(payload);
        var result = lookup(ciType, identifier);
        return JSON.stringify({
            success: true,
            status: 'ok',
            requested_ci_type: ciTypeInput,
            ci_type: ciType,
            ci_type_display_name: resolvedType.label,
            ci_identifier: identifier,
            match_count: result.records.length,
            truncated: result.truncated,
            records: result.records
        });
    } catch (ex) {
        if (typeof status !== 'undefined') status = 400;
        return JSON.stringify({ success: false, status: 'error', message: text(ex && ex.message ? ex.message : ex) });
    }
})(request, body);
