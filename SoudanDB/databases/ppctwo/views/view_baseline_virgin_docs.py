from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_baseline_virgin_docs", \
    '''function(doc) {
        if ( !doc.baseline_dict.chi_square ) {
            emit(doc._id, null);
        }
     }
    ''')
