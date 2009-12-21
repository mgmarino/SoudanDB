from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "virgin_start_of_runtime", \
    '''function(doc) {
       if ( doc.local_time_of_start_of_run == null  
            && doc.raw_data_file_tier_0) {
         emit(doc._id, null); 
       }
    }
    ''')
