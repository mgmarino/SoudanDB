from couchdb.design import ViewDefinition

"""
Gets the number of times a certain number of events
are found in the file.
"""
def get_view_class():
    return ViewDefinition("analysis", "all_events_in_runfile", \
    '''function(doc) {
       if (doc.ln_data_file) return;
       var int_of_doc_id = parseInt(doc._id);
       if (isNaN(int_of_doc_id)) return;
       // We don't accept any runs before 4 December.  
       // The runs before this were with a different DAQ system.
       // i.e. no digitized pulses.
       if (int_of_doc_id < 20091204180000) {
         return;
       }
       if (! doc.number_of_entries_in_tier1_root_tree) return;
       emit(doc.number_of_entries_in_tier1_root_tree, 1); 
    }
    ''',
    '''function(key, values, rereduce) {
        return sum(values);
    }
    ''')

