from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_numentries_virgin_docs", \
    '''function(doc) {
        if ( !run_doc.number_of_entries_in_tier1_root_tree ) {
            emit(doc._id, null);
        }
     }
    ''')
