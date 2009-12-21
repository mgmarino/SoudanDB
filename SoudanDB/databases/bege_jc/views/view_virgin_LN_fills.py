from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "virgin_LN_Fills", \
    '''function(doc) {
       if ( doc.ln_data_file && 
            !doc.ln_data_file.last_mod_time) {
         emit(doc._id, null); 
       }
    }
    ''')
