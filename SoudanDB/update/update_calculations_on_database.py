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

    function_list = []

    # Which database are we using?
    # Grab all the modules from the update directory
    current_db_name = '%s.update' % get_current_db_module()
    update_module = my_import(current_db_name)
    for loader,name,ispkg in pkgutil.iter_modules([update_module.__path__[0]]):
        if ispkg: continue
        load = pkgutil.find_loader('%s.%s' % (current_db_name, name))
        mod = load.load_module("%s.%s" % (current_db_name,name))
        for aname in mod.__dict__.keys():
            if inspect.isfunction(getattr(mod, aname)):
                function_list.append(getattr(mod, aname))

    for id in server.get_database():
        run_doc = server.get_doc(id)
        if not run_doc: continue
        must_reinsert = False
        for function in function_list:
            try:
                (run_doc, temp_bool) = function(run_doc)
            except AttributeError:
                # This means the calling function assumed
                # it was a particular type of doc
                temp_bool = False 
                pass
            must_reinsert = must_reinsert or temp_bool
        if must_reinsert:
            print "Updating run number: %s" % run_doc.id
            server.insert_rundoc(run_doc)

if __name__ == '__main__':
    update_calculations_on_database()
