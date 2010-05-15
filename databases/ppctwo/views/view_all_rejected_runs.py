from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_rejected_runs", 
    '''function(doc) {
       if(doc.quality_assurance.qa_check_process_has_been_run && doc.quality_assurance.qa_accept_run) {
         return;
       }
       emit(parseInt(doc._id), null); 
     }
    ''')
