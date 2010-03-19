from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_pulser_data_virgin_docs", \
    '''function(doc) {
        if ( !run_doc.pulser_data.sigma ) {
            emit(doc._id, null);
        }
     }
    ''')
