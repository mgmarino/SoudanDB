from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("final", "all_accepted_runs_with_att", \
    '''
function(doc) {
       var int_of_doc_id = parseInt(doc._id);

       // We inserted an attenuator inline with the Gretina card to
       // give us better energy range (this will definitely hurt our
       // noise performance.  

       // There were two swaps, one by Jerry, and then one later one by 
       // Brian:

       //At 3:08 PM -0600 12/30/09, Brian Anderson wrote:
       //Hi Juan
       //
       //Just a note to let you know that I swapped the attenuator
       //on PNNL at 15:00.

       if(isNaN(int_of_doc_id)) return;
       if (int_of_doc_id < 650) {
         return;
       }
       emit(int_of_doc_id, null); 
     }
    ''')
