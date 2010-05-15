from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_livetime_virgin_docs", \
    '''function(doc) {
        if ( !run_doc.livetime.run_seconds ) {
            emit(doc._id, null);
        }
     }
    ''')
