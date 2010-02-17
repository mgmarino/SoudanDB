from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "files_of_all_accepted_runs", 
    '''function(doc) {
       if(!(doc.quality_assurance.qa_check_process_has_been_run && doc.quality_assurance.qa_accept_run)) {
         return;
       }
       emit(parseInt(doc._id), [doc.output_data_file_tier_3.high_energy.lfn, doc.output_data_file_tier_3.low_energy.lfn]); 
     }
    ''')
