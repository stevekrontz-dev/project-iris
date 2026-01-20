import requests
import json

headers = {
    'Authorization': 'Bearer b40660ce-f0e1-4d19-af83-9be03c3d736f',
    'Content-Type': 'application/json'
}

# Get workspaces directly
query = '''
query {
    me {
        id
        email
        workspaces {
            id
            name
        }
    }
}
'''
r = requests.post('https://backboard.railway.app/graphql/v2', 
                  json={'query': query}, headers=headers)
print(json.dumps(r.json(), indent=2))
