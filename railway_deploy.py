import requests
import json
import sys

TOKEN = 'b40660ce-f0e1-4d19-af83-9be03c3d736f'
WORKSPACE_ID = '2b8a045f-4354-494b-977b-3769b9c4e196'
GITHUB_REPO = 'stevekrontz-dev/project-iris'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

def gql(query, variables=None):
    r = requests.post('https://backboard.railway.app/graphql/v2', 
                      json={'query': query, 'variables': variables or {}}, headers=headers)
    return r.json()

# Step 1: Create project
print("Creating IRIS project...")
result = gql('''
mutation {
    projectCreate(input: { 
        name: "iris"
        description: "IRIS Research Collaboration Platform"
        workspaceId: "''' + WORKSPACE_ID + '''"
    }) {
        id
        name
    }
}
''')

if 'errors' in result:
    print(f"Error: {json.dumps(result, indent=2)}")
    sys.exit(1)

PROJECT_ID = result['data']['projectCreate']['id']
print(f"Created project: {PROJECT_ID}")

# Step 2: Get default environment ID
print("Getting environment...")
result = gql('''
query($projectId: String!) {
    project(id: $projectId) {
        environments {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
}
''', {'projectId': PROJECT_ID})

ENV_ID = result['data']['project']['environments']['edges'][0]['node']['id']
print(f"Environment ID: {ENV_ID}")

print(f"\n✅ Project created successfully!")
print(f"   Project ID: {PROJECT_ID}")
print(f"   Environment ID: {ENV_ID}")
print(f"\n   Dashboard: https://railway.app/project/{PROJECT_ID}")
