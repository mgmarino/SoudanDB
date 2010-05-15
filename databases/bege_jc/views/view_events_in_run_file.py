from couchdb.design import ViewDefinition

"""
Gets the number of times a certain number of events
are found in the file.
"""
def get_view_class():
    return ViewDefinition("analysis", "all_events_in_runfile", \
    '''function(doc) {
       var my_string = doc._id
       if (my_string.search("LN2") != -1) return;
       if (isNaN(parseInt(my_string))) return;
       if (! doc.number_of_entries_in_tier1_root_tree) return;
       emit(doc.number_of_entries_in_tier1_root_tree, 1); 
    }
    ''',
    '''function(key, values, rereduce) {
        return sum(values);
    }
    ''')

