from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("final", "all_accepted_runs", \
    '''
function(doc) {
       var int_of_doc_id = parseInt(doc._id);

       // Juan ran a calibration run on the 17th of Dec, from his email:
       //Mike, you'll notice the file today at 12:31 is large. We performed a
       //scanning pulser calibration extending all the way out to the maximum
       //range of ch2 (I had limited measurements to the range of ch1, and want
       //to see how rise times compare with those in the known peaks up there
       //in energy)
       if(isNaN(int_of_doc_id)) return;
       if (int_of_doc_id == 331 || 
           int_of_doc_id == 332) {
         return;
       }
       emit(int_of_doc_id, null); 
     }
    ''')
