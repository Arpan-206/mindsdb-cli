import mindsdb_sdk
from PyInquirer import prompt, Separator
from rich import print


def init():
    """
    Initialize the mindsdb cli
    """
    auth_type = prompt({
        'type': 'list',
        'name': 'auth_type',
        'message': 'Which type of instance do you want to connect to?',
        'choices': ['Local Server', 'Cloud Server', 'MindsDB Pro']
    })
    server = None

    if auth_type['auth_type'] == 'Local Server':
        connect_ip = prompt({
            'type': 'input',
            'name': 'connect_ip',
            'message': 'What is the IP of the server you want to connect to?',
            'default': 'http://165.22.218.150:47334/'
        })
        server = mindsdb_sdk.connect(connect_ip['connect_ip'])
    elif auth_type['auth_type'] == 'Cloud Server':
        connect_data = prompt([{
            'type': 'input',
            'name': 'domain',
            'message': 'What is the domain of the instance you want to connect to?',
        },
            {
            'type': 'input',
            'name': 'login',
            'message': 'What is your login?',
        },
            {
            'type': 'password',
            'name': 'password',
            'message': 'What is your password?',
        }])
        server = mindsdb_sdk.connect(
            connect_data['domain'], connect_data['login'], connect_data['password'])
    elif auth_type['auth_type'] == 'MindsDB Pro':
        connect_data = prompt([{
            'type': 'input',
            'name': 'ip',
            'message': 'What is the IP of the instance you want to connect to?',
        },
            {
            'type': 'input',
            'name': 'login',
            'message': 'What is your login?',
        },
            {
            'type': 'password',
            'name': 'password',
            'message': 'What is your password?',
        },
            {
            'type': 'confirm',
            'name': 'is_managed',
            'message': 'Is this instance managed by MindsDB?',
            'default': True
        }])
        server = mindsdb_sdk.connect(
            connect_data['ip'], connect_data['login'], connect_data['password'], is_managed=connect_data['is_managed'])

    # Select a db
    db = prompt({
        'type': 'input',
        'name': 'db',
        'message': f'Which database (0 till {len(server.list_databases()) - 1}) do you want to use?',
        'default': '0',
        'validate': lambda val: int(val) < len(server.list_databases())
    })

    database = server.list_databases()[int(db['db'])]

    return server, database


def table_functions(server: mindsdb_sdk.Server, db: mindsdb_sdk.database.Database):
    """
    The function that handles table functions
    """

    table_action = prompt({
        'type': 'list',
        'name': 'action',
        'message': 'What do you want to do?',
        'choices': ['Create a table', 'Run query', 'List tables']
    })
    if table_action['action'] == "List tables":
        print(db.list_tables())
        after_init(server, db)

    query_p = prompt({
        'type': 'editor',
        'name': 'query',
        'message': 'What query do you want to run?',
        'default': 'SELECT * FROM table_name',
        'eargs': {
                'editor': 'nano',
                'ext': '.sql'
        }
    })

    query = db.query(query_p['query'])

    if table_action['action'] == "Create a table":
        name = prompt({
            'type': 'input',
            'name': 'name',
            'message': 'What name do you want to give to the table?',
            'default': 'table_name'
        })
        db.create_table(name['name'], query)
        print(f"Created table with query: {query_p['query']}")
        after_init(server, db)

    elif table_action['action'] == "Run query":
        data = query.fetch()
        print(data)
        after_init(server, db)


def view_functions(project: mindsdb_sdk.project.Project, db: mindsdb_sdk.database.Database):
    action = prompt({
        'type': 'list',
        'name': 'action',
        'message': 'What do you want to do?',
        'choices': ['List views', 'Get a view', 'Create a view', 'Delete a view', 'Get data from a view', Separator(), 'Back']
    })

    view = None

    if action['action'] == "List views":
        views = project.list_views()
        print(views)
        view_functions(project, db)

    elif action['action'] == "Get a view":
        view_name = prompt({
            'type': 'input',
            'name': 'name',
            'message': 'What is the name of the view?',
        })
        view = project.get_view(view_name['name'])
        print(view)
        view_functions(project, db)

    elif action['action'] == "Create a view":
        view_details = prompt([{
            'type': 'input',
            'name': 'name',
            'message': 'What is the name of the view?',
        },
            {
            'type': 'editor',
            'name': 'query',
            'message': 'What query do you want to run?',
            'default': 'SELECT * FROM table_name',
            'eargs': {
                'editor': 'nano',
                'ext': '.sql'
            }
        }])
        view = project.create_view(
            view_details['name'], sql=db.query(view_details['query']))
        print(view)
        view_functions(project, db)

    elif action['action'] == "Delete a view":
        view_name = prompt([{
            'type': 'input',
            'name': 'name',
            'message': 'What is the name of the view?',
        },
            {
            'type': 'confirm',
            'name': 'confirm',
            'message': 'Are you sure you want to delete this view?',
            'default': False
        }])
        if not view_name['confirm']:
            view_functions(project, db)
        project.drop_view(view_name['name'])
        print("View deleted")
        view_functions(project, db)

    elif action['action'] == "Get data from a view":
        if not view:
            view_name = prompt({
                'type': 'input',
                'name': 'name',
                'message': 'What is the name of the view?',
            })
            view = project.get_view(view_name['name'])

        data = view.fetch()
        print(data)
        view_functions(project, db)

    elif action['action'] == "Back":
        project_functions(project, db)


def project_functions(project: mindsdb_sdk.project.Project, db: mindsdb_sdk.database.Database):
    """
    The function that handles project functions
    """
    act_type = prompt({
        'type': 'list',
        'name': 'action',
        'message': 'What do you want to use?',
        'choices': ['Run a query', 'View actions', 'Model actions', Separator(), 'Exit']
    })

    if act_type['action'] == "Exit":
        return

    elif act_type['action'] == "Run a query":
        query_p = prompt({
            'type': 'editor',
            'name': 'query',
            'message': 'What query do you want to run?',
            'default': 'SELECT * FROM table_name',
            'eargs': {
                'editor': 'nano',
                'ext': '.sql'
            }
        })
        query = project.query(query_p['query'])
        data = query.fetch()
        print(data)
        project_functions(project)

    elif act_type['action'] == "View actions":
        view_functions(project, db)


def after_init(server: mindsdb_sdk.Server, db: mindsdb_sdk.database.Database):
    """
    The function that runs after init
    """

    action = prompt({
        'type': 'list',
        'name': 'action',
        'message': 'What do you want to do?',
        'choices': ['Table Functions', 'Project Functions', Separator(), 'Exit']
    })

    if action['action'] == "Exit":
        return

    elif action['action'] == "Project Functions":
        project_name = prompt({
            'type': 'input',
            'name': 'name',
            'message': 'What is the name of the project you want to select?',
            'default': 'project_name'
        })
        project = server.get_project(project_name['name'])
        project_functions(project, db)

    elif action['action'] == "Table Functions":
        table_functions(server, db)


def main():
    server, database = init()
    after_init(server, database)


if __name__ == '__main__':
    main()
