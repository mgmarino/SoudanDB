from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_threshold_average", 
    '''function(doc) {
       if (!(doc.quality_assurance.qa_check_process_has_been_run && doc.quality_assurance.qa_accept_run)) {
         return;
       }
       if (!(doc.trigger_efficiency.scaling)) return;

       temp = doc.trigger_efficiency;
       emit('scaling', temp.scaling); 
       emit('scaling_sq', temp.scaling*temp.scaling); 
       emit('offset', temp.offset); 
       emit('offset_sq', temp.offset*temp.offset); 
       emit('length', 1); 
     }
    ''',
    '''function(key, values, rereduce) {
        return sum(values);
    }
    '''
    )
