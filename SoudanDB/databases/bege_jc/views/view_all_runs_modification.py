from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_runs_modification", \
    '''function(doc) {
       var my_string = doc._id
       if (my_string.search("LN2") != -1) return;
       if (isNaN(parseInt(my_string))) return;
         emit(doc._id, [[doc.raw_data_file_tier_0.pfn, doc.raw_data_file_tier_0.last_mod_time],
                        [doc.root_data_file_tier_1.pfn, doc.root_data_file_tier_1.last_mod_time],
                        [doc.output_data_file_tier_2.pfn, doc.output_data_file_tier_2.last_mod_time]]); 
    }
    ''')
