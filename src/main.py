import requests
import json
from gql import Client, client, gql
from gql.transport.requests import RequestsHTTPTransport


def taiga_authentication(taiga_url, login, passwd):
    taiga_auth = requests.post(
        taiga_url + '/api/v1/auth', 
        headers={
            'Content-Type': 'application/json'
        }, 
        data=json.dumps({
            'password': passwd,
            'type': 'normal',
            'username': login
        })
    )

    if taiga_auth.status_code // 100 == 2:
        return taiga_auth.json()['auth_token']
    else:
        return None


def get_taiga_info(taiga_url, project_slug, token):
    info = requests.get(
        taiga_url + '/api/v1/projects/by_slug?slug=' + project_slug,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }
    )

    if info.status_code // 100 == 2 and 'members' in info.json():
        return info.json()['members']
    else:
        return None


def make_client(wiki_url, wiki_token):
    transport = RequestsHTTPTransport(
        url=wiki_url+'/graphql',
        headers={
            'Authorization': 'Bearer ' + wiki_token
        }
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True
    )

    return client


def make_pages(members, client, roles, path):
    for member in members:
        if member['role_name'].lower() in roles or 'all' in roles:
            res = client.execute(gql(f"""
                mutation {{
                    pages {{
                        create(
                            content: "## {member['full_name']}\\n![avatar]({member['photo']})",
                            description: "Member of Project School",
                            editor: "markdown",
                            isPublished: true,
                            isPrivate: false,
                            locale: "ru",
                            path: "{path}{member['username'].lower()}",
                            tags: ["{member['role_name']}"],
                            title: "{member['full_name']}"
                        ) {{
                            responseResult {{
                                succeeded
                                message
                            }}
                        }}
                    }}
                }}
            """))
            print('Page was created.')





with open('settings.ini', 'r') as file:
    login = file.readline()[6:].strip()
    passwd = file.readline()[9:].strip()
    wiki_token = file.readline()[11:].strip()
    taiga_url = file.readline()[10:].strip()
    wiki_url = file.readline()[9:].strip()
    project_slug = file.readline()[13:].strip()
    path = file.readline()[5:].strip()
    roles = file.readline()[6:].strip()

roles = roles.split(',')
roles = [elem.lower().strip() for elem in roles]

taiga_token = taiga_authentication(taiga_url, login, passwd)

if taiga_token == None:
    print('Taiga auth: NOT OK')
else:
    print('Taiga auth: OK')

    taiga_members = get_taiga_info(taiga_url, project_slug, taiga_token)

    if taiga_members == None:
        print("Project's info: NOT OK")
    else:
        print("Project's info: OK")

        client = make_client(wiki_url, wiki_token)
        make_pages(taiga_members, client, roles, path)

        print('Done.')