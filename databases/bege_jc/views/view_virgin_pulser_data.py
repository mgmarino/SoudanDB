from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "virgin_pulser_data", \
    '''function(doc) {
       if ( doc.pulser_run_characteristics.chan_0.sigma.length != 
            doc.pulser_on_set.length) {
         emit(doc._id, null); 
       }
    }
    ''')
