from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_noise_data", 
    '''function(doc) {
       if (!(doc.quality_assurance.qa_check_process_has_been_run && doc.quality_assurance.qa_accept_run)) {
         return;
       }
       if (!(doc.pulser_data.sigma)) return;

       temp = doc.pulser_data;
       emit('sigma', temp.sigma); 
       emit('sigma_sq', temp.sigma*temp.sigma); 
       emit('mean', temp.mean); 
       emit('mean_sq', temp.mean*temp.mean); 
       emit('length', 1); 
     }
    ''',
    '''function(key, values, rereduce) {
        return sum(values);
    }
    '''
    )
