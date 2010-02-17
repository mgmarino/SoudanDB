from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_virgin_livetime", \
    '''function(doc) {
       var int_of_doc_id = parseInt(doc._id);
       if(isNaN(int_of_doc_id)) return;
       if (!doc.livetime.run_milliseconds) { 
           emit(doc._id, null);
       }
     }
    ''')
