from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_runs", \
    '''function(doc) {
       var my_string = doc._id
       if (my_string.search("LN2") != -1) return;
       if (isNaN(parseInt(my_string))) return;
       emit(doc._id, null); 
    }
    ''')
