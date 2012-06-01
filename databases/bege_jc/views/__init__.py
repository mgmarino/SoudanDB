import SoudanDB.views
import pkgutil
dirname = SoudanDB.views.__path__[0]
__path__.insert(0, dirname)
module_dict = globals()
current_db_name = SoudanDB.views.__name__
# Now export all submodules
__all__ = []
for loader,name,ispkg in pkgutil.walk_packages( __path__ ):
    if ispkg: continue
    __all__.append(name)
    module = loader.find_module(name).load_module(name)
    module_dict[name] = module
