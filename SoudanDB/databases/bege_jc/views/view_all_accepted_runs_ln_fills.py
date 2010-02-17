from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("final", "all_accepted_runs_ln_fills", \
    '''
function(doc) {
       var int_of_doc_id = parseInt(doc._id);
       if (!isNaN(int_of_doc_id)) { 
         if (int_of_doc_id < 20091204180000) {
           return;
         }
       }
       if (doc.ln_data_file) { 
           var temp_str = new String(doc._id);
           emit(parseInt(temp_str.split('.')[0]), 'LN');
           return;
       }

       if (isNaN(int_of_doc_id)) return;
       // We don't accept any runs before 4 December.  
       // The runs before this were with a different DAQ system.
       // i.e. no digitized pulses.
       if (int_of_doc_id < 20091204180000) {
         return;
       }
       // choose a date to analyze until.
       if (int_of_doc_id > 20100208180000) {
         return;
       }
       // Juan ran a calibration run on the 17th of Dec, from his email:
       //Mike, you'll notice the file today at 12:31 is large. We performed a
       //scanning pulser calibration extending all the way out to the maximum
       //range of ch2 (I had limited measurements to the range of ch1, and want
       //to see how rise times compare with those in the known peaks up there
       //in energy)
       if (int_of_doc_id == 20091217123128 ||
           int_of_doc_id == 20091217123841) {
         return;
       }
       emit(int_of_doc_id, [doc.output_data_file_tier_2.lfn,
                                doc.root_data_file_tier_1.pfn]); 
     }
    ''')
