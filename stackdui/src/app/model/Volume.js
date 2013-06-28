Ext.define('stackdio.model.Volume', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',               type: 'int' }
        ,{ name: 'cloud_provider',  type: 'int' }
        ,{ name: 'size_in_gb',      type: 'float' }
        ,{ name: 'title',           type: 'string' }
        ,{ name: 'description',     type: 'string' }
    ]


    ,proxy: {
        type: 'rest',
        url: '/api/snapshots/',
        reader: {
            type: 'json',
            root: 'results'
        },
        headers: {
            "Authorization": "Basic " + Base64.encode('testuser:password')
        },
        pageParam: undefined,
        limitParam: undefined,
        startParam: undefined
    }
});