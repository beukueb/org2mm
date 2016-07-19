#!/bin/env python3
#General imports
from PyOrgMode import PyOrgMode
from urllib import request
import json

def syncBasecamps(orgfile,orgoutfile,bc_settings):
    #Load org file
    orgbase = PyOrgMode.OrgDataStructure()
    orgbase.load_from_file(orgfile)

    if not orgoutfile:
        orgoutfile = orgfile.replace('.org','_bcsync.org')
    
    #Set todo states -> this should be pushed to PyOrgMode
    todostates = set()
    donestates = set()
    # refactor to use orgbase.set_todo_states?
    for c in orgbase.root.content:
        if type(c) == str and c.startswith('#+TODO'):
            todone = False
            for s in c.split()[1:]:
                if s == '|':
                    todone = True
                    continue
                donestates.add(s) if todone else todostates.add(s)
    orgbase = PyOrgMode.OrgDataStructure()
    for s in todostates: orgbase.add_todo_state(s)
    for s in donestates: orgbase.add_done_state(s)
    orgbase.load_from_file(orgfile)
    bc_settings['todostates'] = todostates

    #Load basecamp projects
    projects = getBasecampProjects(bc_settings)
    bc_settings['projects'] = projects
    
    #Search for first order (*) elements linked to a basecamp
    for node in orgbase.root.content:
        if type(node) == PyOrgMode.OrgNode.Element:
            for c in node.content:
                if type(c) == PyOrgMode.OrgDrawer.Element:
                    for p in c.content:
                        if p.name == 'basecamp':
                            syncBasecamp(node,basecamp=p.value,bc_settings=bc_settings)
    #Include other basecamp todos
    includeBCassignedTodos(bc_settings,orgbase)

    #Save new org file
    orgbase.save_to_file(orgoutfile)                            

def syncBasecamp(node,basecamp,bc_settings):
    #Retrieve basecampID
    for c in node.content:
        if type(c) == PyOrgMode.OrgDrawer.Element:
            basecampID = False
            for p in c.content:
                if p.name == 'basecampID':
                    basecampID = p.value
            if not basecampID:
                basecampID = getBasecampID(bc_settings['projects'],basecamp)
                prop = PyOrgMode.OrgDrawer.Property(name='basecampID',
                                                    value=str(basecampID))
                prop.indent = ' '+' '*node.level
                c.append(prop)
    #Retrieve todosets
    req = request.Request('https://3.basecampapi.com/{}/projects/{}.json'.format(
        bc_settings['ACCOUNT_ID'],basecampID))
        #app['url'].replace('.json','/todolists.json'))
    req.add_header('Authorization','Bearer {}'.format(
        bc_settings['ACCESS_TOKEN']))
    r = request.urlopen(req)
    project = json.loads(r.read().decode())
    for app in project['dock']:
        if app['name'] == 'todoset':
            todosetID = app['id']
            req = request.Request(app['url'].replace('.json','/todolists.json'))
    req.add_header('Authorization','Bearer {}'.format(
        bc_settings['ACCESS_TOKEN']))
    r = request.urlopen(req)
    todosets = json.loads(r.read().decode())
    todosets = {ts['name'][9:]:ts for ts in todosets}
    #Current year for new todolists
    from datetime import date
    from itertools import count
    year = date.today().year
    todoCounter = count(sum((int(todosets[ts]['name'].split()[0]) == year
                             for ts in todosets)))
    #Loop org node todolists
    for tl in node.content:
        if type(tl) == PyOrgMode.OrgNode.Element:
            if not tl.heading in todosets:
                bctl = '{} {:03} {}'.format(year,next(todoCounter),tl.heading)
                data = {'name':bctl}
                data = repr(data).replace("'",'"').encode()
                req = request.Request(
                    'https://3.basecampapi.com/{}/buckets/{}/todosets/{}/todolists.json'.format(
                        bc_settings['ACCOUNT_ID'],basecampID,todosetID),data=data)
                req.add_header('Authorization','Bearer {}'.format(
                    bc_settings['ACCESS_TOKEN']))
                req.add_header('Content-Type','application/json')
                r = request.urlopen(req)
                newTodolist = json.loads(r.read().decode())
                todosets[tl.heading] = newTodolist
            #Loop org node todoitems
            req = request.Request(
                    'https://3.basecampapi.com/{}/buckets/{}/todolists/{}/todos.json'.format(
                        bc_settings['ACCOUNT_ID'],basecampID,todosets[tl.heading]['id']))
            req.add_header('Authorization','Bearer {}'.format(
                    bc_settings['ACCESS_TOKEN']))
            r = request.urlopen(req)
            bctodos = json.loads(r.read().decode())
            bctodos = {bcn['content']:bcn for bcn in bctodos}
            for ti in tl.content:
                if type(ti) == PyOrgMode.OrgNode.Element:
                    if not ti.heading in bctodos:
                        data = json.dumps({'content': ti.heading}).encode()
                        req = request.Request(
                            'https://3.basecampapi.com/{}/buckets/{}/todolists/{}/todos.json'.format(
                                bc_settings['ACCOUNT_ID'],basecampID,todosets[tl.heading]['id']),
                            data=data)
                        req.add_header('Authorization','Bearer {}'.format(
                            bc_settings['ACCESS_TOKEN']))
                        req.add_header('Content-Type','application/json')
                        r = request.urlopen(req)
                        newTodo = json.loads(r.read().decode())
                        bctodos[ti.heading] = newTodo
                    #Update todo state if needed
                    try:
                        if (ti.todo in bc_settings['todostates']) == bctodos[ti.heading]['completed']:
                            data = json.dumps({'content': ti.heading}).encode()
                            req = request.Request(
                                'https://3.basecampapi.com/{}/buckets/{}/todos/{}/completion.json'.format(
                                    bc_settings['ACCOUNT_ID'],basecampID,bctodos[ti.heading]['id']),
                                data=data,method='DELETE' if ti.todo in bc_settings['todostates'] else 'POST')
                            req.add_header('Authorization','Bearer {}'.format(
                                bc_settings['ACCESS_TOKEN']))
                            req.add_header('Content-Type','application/json')
                            r = request.urlopen(req)
                    except AttributeError:
                        pass
    

def getBasecampProjects(bc_settings):
    req = request.Request('https://3.basecampapi.com/{}/projects.json'.format(
        bc_settings['ACCOUNT_ID']))
    req.add_header('Authorization','Bearer {}'.format(
        bc_settings['ACCESS_TOKEN']))
    r = request.urlopen(req)
    projects = json.loads(r.read().decode())
    return projects
    
def getBasecampID(projects,basecamp):
    for project in projects:
        if project['name'] == basecamp:
            basecampID = project['id']
            return basecampID

def includeBCassignedTodos(bc_settings,orgbase,assignee='Christophe Van Neste'):
    bctodo_present = False
    for bctodo_node in orgbase.root.content:
        if (type(bctodo_node) == PyOrgMode.OrgNode.Element and
            bctodo_node.heading == 'Basecamp todos'):
            bctodo_present = True
            bctodo_node.content = []
            break
    if not bctodo_present:
        bctodo_node = PyOrgMode.OrgNode.Element()
        bctodo_node.level = 1
        bctodo_node.heading = 'Basecamp todos'
        orgbase.root.append(bctodo_node)
    for project in bc_settings['projects']:
        pname = project['name']
        prid = project['id']
        for app in project['dock']:
            if app['name'] == 'todoset':
                req = request.Request(app['url'].replace('.json','/todolists.json'))
                req.add_header('Authorization','Bearer {}'.format(bc_settings['ACCESS_TOKEN']))
                r = request.urlopen(req)
                todosets = json.loads(r.read().decode())
                for todoset in todosets:
                    req = request.Request(todoset['todos_url'])
                    req.add_header('Authorization','Bearer {}'.format(bc_settings['ACCESS_TOKEN']))
                    r = request.urlopen(req)
                    todos = json.loads(r.read().decode())
                    for todo in todos:
                        for assigneed in todo['assignees']:
                            if assigneed['name'] == assignee:
                                ntodo = PyOrgMode.OrgNode.Element()
                                ntodo.heading = '{} -> {} -> {}'.format(
                                    pname,todoset['name'],todo['content'])
                                ntodo.level = 2
                                bctodo_node.append(ntodo)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sync org outline to basecamp.')
    parser.add_argument('outline', help='org outline file')
    parser.add_argument('output', help='output filename', nargs='?')
    #parser.add_argument('-u','--user_account',type=int,help='Basecamp user account ID')
    #parser.add_argument('-a','--access_code',help='Basecamp access code')

    #argv = parser.parse_args('todo_outline.org'.split())
    argv = parser.parse_args()

    #Fixed settings
    ##format { 'ACCOUNT_ID': int, 'ACCESS_TOKEN': str }
    import pickle
    bc_settings = pickle.load(open('/home/christophe/repos/org2mm/bc_settings.pickle','rb'))

    syncBasecamps(argv.outline,argv.output,bc_settings)
