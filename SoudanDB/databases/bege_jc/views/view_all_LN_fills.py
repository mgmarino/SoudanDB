from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_LN_Fills", \
    '''function(doc) {
       if (doc.ln_data_file) {
         var temp_str = new String(doc.time_of_start_of_fill)
         emit(temp_str.split('T')[0], doc.fill_duration); 
       }
    }
    ''')
