from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_efficiency_data", 
    '''function(doc) {
       if (!(doc.quality_assurance.qa_check_process_has_been_run && doc.quality_assurance.qa_accept_run)) {
         return;
       }
       if (!(doc.trigger_efficiency.scaling_err)) return;

       temp = doc.trigger_efficiency;
       emit(parseInt(doc._id), [temp.scaling, temp.scaling_err, 
                                temp.offset,  temp.offset_err]); 
     }
    ''')
