from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_virgin_starttime", \
    '''function(doc) {
       var int_of_doc_id = parseInt(doc._id);
       if(isNaN(int_of_doc_id)) return;
        if (!doc.local_time_of_start_of_run) { 
            emit(doc._id, null);
        }
     }
    ''')
