from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "start_time_of_all_accepted_runs", \
    '''function(doc) {
       if (!(doc.quality_assurance.qa_check_process_has_been_run && doc.quality_assurance.qa_accept_run)) {
         return;
       }
       emit(parseInt(doc._id), doc.time_of_start_of_run); 
     }
    ''')
#,
#    '''
#    function (key, values, rereduce) {
#       return sum(values);
#    }''')
