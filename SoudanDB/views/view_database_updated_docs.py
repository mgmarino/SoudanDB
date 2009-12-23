from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("management", "all_database_updated_docs", \
    '''function(doc) {
        if (doc.time_of_last_update) { 
            emit(doc._id, null);
        }
     }
    ''')
