from ..management.soudan_database import SoudanServer
def generate_all_cuts_on_database(force_overwrite=False):
    server = SoudanServer()
   
    # First check to see if the cuts are in the database, and what version they are:
    cuts_dictionary = {}
    for id in server.get_cuts_database():
        cut_doc = server.get_cut(id)
        cuts_dictionary[id] = cut_doc 

    for run_id in server.get_database():
        run_doc = server.get_run(run_id)
        if not run_doc: continue
        must_reinsert = False
        if force_overwrite:
            while len(run_doc.all_cuts) > 0:
                del run_doc.all_cuts[0]
            must_reinsert = True
        
        omit_cuts = []
        # First we update the cuts that have been performed
        # before
        for id, cut_doc in cuts_dictionary.items():
            for dictionary in run_doc.all_cuts: 
                desc = dictionary['description_of_cut']
                version = dictionary['version_of_cut']
                if desc == id:
                    omit_cuts.append(id)
                    if version != cut_doc.rev:
                        # We must reperform the cut
                        must_reinsert = True
                        dictionary['passes_cut'] = cut_doc.\
                          generate_cut_for_run_doc(run_doc)
                        dictionary['version_of_cut'] = cut_doc.rev
                        dictionary['string_of_cut'] = cut_doc.string_of_cut

        # Now we update the cuts that haven't been done
        for id, cut_doc in cuts_dictionary.items():
            if id in omit_cuts: continue
            must_reinsert = True
            temp_dict = {}
            temp_dict['description_of_cut'] = id
            temp_dict['version_of_cut'] = cut_doc.rev
            temp_dict['string_of_cut'] = cut_doc.string_of_cut
            temp_dict['passes_cut'] = cut_doc.generate_cut_for_run_doc(run_doc)
            run_doc.all_cuts.append(temp_dict)
             
        if not run_doc.quality_assurance.qa_check_process_has_been_run:
            must_reinsert = True
        if must_reinsert:
            run_doc.quality_assurance.qa_check_process_has_been_run = True
            run_doc.quality_assurance.qa_accept_run = True
            for dictionary in run_doc.all_cuts: 
                passes_cut = dictionary['passes_cut']
                if not passes_cut:
                    run_doc.quality_assurance.qa_accept_run = False
                  
            print "Updating run %s" % run_id
            server.insert_rundoc(run_doc)
