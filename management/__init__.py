module_dict =  globals()
class ServerSingleton:
    _soudan_server = None
    @classmethod
    def set_server(cls, server):
        cls._soudan_server = server
    @classmethod
    def get_server(cls):
        return cls._soudan_server() 

class CurrentDBSingleton:
    _current_database_module = None
    @classmethod
    def set_current_db_module(cls, db_module):
        cls._current_database_module = db_module 
    @classmethod
    def get_current_db_module(cls):
        return cls._current_database_module 
 
module_dict[ServerSingleton.__name__] = ServerSingleton
module_dict[CurrentDBSingleton.__name__] = CurrentDBSingleton
