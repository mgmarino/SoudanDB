from ..management.soudan_database import SoudanServer, CutDocumentClass  
class MGCut(object):
    """
    Base class which is inserted into the database.  A later daemon will go
    through and run the cuts on documents that need it.
    """

    def get_description_of_cut(self):
        return ""

    def get_verbose_description_of_cut(self):
        return ""

    def get_string_of_cut(self):
        """
        Returns a cut to be parsed and run later on.  Any references that
        the string makes must be to items in the document in the database.
        For example, if a document has an item like "passes_cut" in the root
        or the document, one could return 'not passes_cut'.

        Furthermore, if there is a dictionary in the document like:

   "noise_check": {
       "events_in_region_10_to_70_keV": 20,
       "events_in_region_point6_to_10_keV": 20
   }
        
        then the string could return a cut like 
        "not noise_check.events_in_region_10_to_70_keV > 25"

        Available modules are math and ROOT.
        """
        return ""

       
def insert_cut_into_database(cut):
    """
    Function inserts a cut into the database for later processing.
    Type of cut should be an MGCut
    """
    
    server = SoudanServer()
    
    cut_doc = server.get_cut(cut.get_description_of_cut())
    if not cut_doc:
        cut_doc = CutDocumentClass()
        cut_doc._set_id(cut.get_description_of_cut())

    cut_doc.string_of_cut = cut.get_string_of_cut()
    cut_doc.verbose_description_of_cut = cut.get_verbose_description_of_cut()

    server.insert_cut(cut_doc)
    

