from couchdb.design import ViewDefinition

def get_view_class():
    return ViewDefinition("analysis", "all_events_in_ROI", 
    '''function(doc) {
       if (!(doc.noise_check.events_in_region_point6_to_10_keV && 
             doc.noise_check.events_in_region_10_to_70_keV)) {
         return;
       }
       emit(parseInt(doc._id), 
         [doc.noise_check.events_in_region_point6_to_10_keV, 
          doc.noise_check.events_in_region_10_to_70_keV]); 
     }
    ''')
