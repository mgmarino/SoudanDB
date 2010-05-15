from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_start_of_runtime_virgin_docs", \
    '''function(doc) {
        if ( !run_doc.time_of_start_of_run ) {
            emit(doc._id, null);
        }
     }
    ''')
