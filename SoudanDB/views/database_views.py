from SoudanDB.management.soudan_database import SoudanServer 

def insert_view_into_database(view):
    """
    Function inserts a view into the database.
    Type of view should be an couchdb.schema.ViewDefinition 
    """
    
    server = SoudanServer()
    view.sync(server.get_database())
