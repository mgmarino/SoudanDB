from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "virgin_runtime", \
    '''function(doc) {
       if ( doc.livetime && 
            !doc.livetime.run_milliseconds) {
         emit(doc._id, null); 
       }
    }
    ''')
