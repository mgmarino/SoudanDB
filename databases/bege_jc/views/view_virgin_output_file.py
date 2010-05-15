from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "virgin_output_file", \
    '''function(doc) {
       if ( doc.output_data_file_tier_2 && 
            !doc.output_data_file_tier_2.last_mod_time) {
         emit(doc._id, null); 
       }
    }
    ''')
