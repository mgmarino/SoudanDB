from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("final", "old_runs", \
    '''
function(doc) {
       if (doc.ln_data_file) return;
       var int_of_doc_id = parseInt(doc._id);
       if (isNaN(int_of_doc_id)) return;

       // We don't accept any runs before 4 December.  
       // The runs before this were with a different DAQ system.
       // i.e. no digitized pulses.
       if (int_of_doc_id >= 20091201000000) {
         return;
       }
       emit(parseInt(doc._id), [doc.output_data_file_tier_2.lfn,
                                doc.root_data_file_tier_1.pfn]); 
     }
    ''')
