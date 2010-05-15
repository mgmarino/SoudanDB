from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "live_time_of_all_accepted_runs", \
    '''function(doc) {
       var int_of_doc_id = parseInt(doc._id);
       if(isNaN(int_of_doc_id)) return;
       if (int_of_doc_id >= 560) {
         return;
       }
       if (int_of_doc_id == 331 || 
           int_of_doc_id == 332) {
         return;
       }

       emit(parseInt(doc._id), doc.livetime.run_milliseconds/1000); 
     }
    ''')
#,
#    '''
#    function (key, values, rereduce) {
#       return sum(values);
#    }''')
