from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("final", "first_efficiency_runs", \
    '''
function(doc) {
       if (doc.ln_data_file) return;
       var beginning_int = 20091203000000;
       var int_of_doc_id = parseInt(doc._id);
 

       // First number is the analog pulser setting
       // The second is the time.
       var pulser_list = [
         [ 40, 150257],
         [ 45, 150837],
         [ 50, 151204],
         [100, 151552],
         [150, 151911],
         [200, 152235],
         [250, 152554],
         [300, 152909],
         [ 38, 153251],
         [ 36, 153624],
         [ 34, 154024],
         [ 32, 154355],
         [ 30, 154726],
         [ 28, 155353]
       ];
       var int_of_doc_id = parseInt(doc._id);

       // When we emit, we return the pulser value as the key
       // and the run number as the value.
       for (i=0;i<pulser_list.length;i++) {
           if (pulser_list[i][1] + beginning_int == int_of_doc_id) {
               emit(pulser_list[i][0], int_of_doc_id);
               return; // Get out
           } 
       }
     }
    ''')
