from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_virgin_docs", \
    '''function(doc) {
        if (!doc.raw_data_file_tier_0.last_mod_time ||
            !doc.root_data_file_tier_1.last_mod_time ||
            !doc.output_data_file_tier_2.last_mod_time) {
            emit(doc._id, null);
        }
     }
    ''')
