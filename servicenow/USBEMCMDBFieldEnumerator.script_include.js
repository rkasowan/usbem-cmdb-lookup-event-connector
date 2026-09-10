var USBEMCMDBFieldEnumerator = Class.create();
USBEMCMDBFieldEnumerator.prototype = {
    initialize: function () {},

    getFields: function (record) {
        var gr = this._requireCMDBRecord(record);
        var javaFields = gr.getFields();
        var names = [];
        var seen = {};
        var i;
        var name;
        for (i = 0; i < javaFields.size(); i++) {
            name = String(javaFields.get(i).getName() || '');
            if (name && !seen[name]) {
                seen[name] = true;
                names.push(name);
            }
        }
        return names;
    },

    getElements: function (record) {
        var gr = this._requireCMDBRecord(record);
        var elements = gr.getElements();
        var names = [];
        var seen = {};
        var i;
        var count = typeof elements.length === 'number' ? elements.length : elements.size();
        var element;
        var name;
        for (i = 0; i < count; i++) {
            element = typeof elements.length === 'number' ? elements[i] : elements.get(i);
            name = String(element.getName() || '');
            if (name && !seen[name]) {
                seen[name] = true;
                names.push(name);
            }
        }
        return names;
    },

    _requireCMDBRecord: function (record) {
        if (!record || typeof record.getTableName !== 'function') {
            throw new Error('A GlideRecord is required.');
        }
        var tableName = String(record.getTableName() || '');
        if (!this._isCMDBTable(tableName)) {
            throw new Error('Access denied: ' + tableName + ' is not cmdb_ci or an extending table.');
        }
        return record;
    },

    _isCMDBTable: function (tableName) {
        var current = tableName;
        var visited = {};
        var table;
        var parentId;
        while (current && !visited[current]) {
            if (current === 'cmdb_ci') return true;
            visited[current] = true;
            table = new GlideRecord('sys_db_object');
            table.addQuery('name', current);
            table.setLimit(1);
            table.query();
            if (!table.next()) return false;
            parentId = String(table.getValue('super_class') || '');
            if (!parentId) return false;
            table = new GlideRecord('sys_db_object');
            if (!table.get(parentId)) return false;
            current = String(table.getValue('name') || '');
        }
        return false;
    },

    type: 'USBEMCMDBFieldEnumerator'
};
