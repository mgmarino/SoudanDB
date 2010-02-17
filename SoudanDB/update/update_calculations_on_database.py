from ..management.soudan_database import SoudanServer, get_current_db_module
import pkgutil
import inspect
import re
def update_calculations_on_database():
    server = SoudanServer()
    
    def my_import(name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    # Which database are we using?
    # Grab all the modules from the update directory
    module_list = []
    current_db_name = '%s.update' % get_current_db_module()
    update_module = my_import(current_db_name)
    for loader,name,ispkg in pkgutil.iter_modules([update_module.__path__[0]]):
        if ispkg: continue
        load = pkgutil.find_loader('%s.%s' % (current_db_name, name))
        mod = load.load_module("%s.%s" % (current_db_name,name))
        module_list.append(mod)

    print "Performing the following updates: " 
    must_cycle = False
    for amod in module_list: 
        # Get the view to use
        view = amod.get_view()
        list_of_docs = view(server.get_database())
        print "  %s" % amod.__name__
        for id in list_of_docs:
            run_doc = server.get_doc(id.id)
            if not run_doc: 
                print "    Error finding %s" % id.id
                continue
            (run_doc, must_reinsert) = amod.update_rundoc(run_doc)
            if must_reinsert:
                must_cycle = True
                print "    Updating run number: %s" % run_doc.id
                server.insert_rundoc(run_doc)

    if must_cycle:
        print "Some documents were updated, cycling again to resolve all updates"
        update_calculations_on_database()
