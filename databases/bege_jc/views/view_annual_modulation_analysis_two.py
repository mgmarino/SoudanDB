from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("second", "annual_modulation", 
    '''
function(doc) {
       if (doc.ln_data_file) return;
       var int_of_doc_id = parseInt(doc._id);
       if (isNaN(int_of_doc_id)) return;

       // We don't accept any runs before 4 December.  
       // The runs before this were with a different DAQ system.
       // i.e. no digitized pulses.
       if (int_of_doc_id < 20091204180000) {
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
       // Detector put to sleep for power outage, down a week
       if (int_of_doc_id > 20100315120053 &&
           int_of_doc_id < 20100319180006) {
         return;
       }

       // DAQ range shifted
       if (int_of_doc_id > 20100209000053 &&
           int_of_doc_id < 20100215120006) {
         return;
       }


       // Soudan Fire
       if (int_of_doc_id > 20110415000000 && 
           int_of_doc_id < 20110607000000) {
         return;
       }

       // End of analysis 2 June 2012
       if (int_of_doc_id > 20120602000000) {
         return;
       }
       emit(parseInt(doc._id), [doc.output_data_file_tier_2.lfn,
                                doc.root_data_file_tier_1.pfn]); 
     }
    ''')
