from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_run_noise_virgin_docs", \
    '''function(doc) {
        if ( !run_doc.noise_check.events_in_region_point6_to_10_keV ) {
            emit(doc._id, null);
        }
     }
    ''')
