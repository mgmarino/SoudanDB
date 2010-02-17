from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "LN_Fills_with_attachment", \
    '''function(doc) {
         if (!doc.ln_data_file) return;
         if (!doc._attachments) return;
         emit(doc._id, null); 
      }
    ''')
