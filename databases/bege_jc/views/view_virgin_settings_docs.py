from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_virgin_settings_docs", \
    '''function(doc) {
        if (doc.settings_data_file &&
            doc.run_settings.length == 0 ) { 
            emit(doc._id, null);
        }
     }
    ''')
