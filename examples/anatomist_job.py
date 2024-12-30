#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys,os,time
import code
import argparse
import re, datetime
import json

if (os.path.exists("config.tar")):
    os.system("tar xf config.tar")

SITE_config='./site_config.ini'
CASE_config="./case_config.ini"

actions_file=open("/home/myuser/actions.json",'r')
tiles_actions=json.load(actions_file)
#launch_actions()

config = configparser.ConfigParser()
config.optionxform = str

config.read(SITE_config)

TILEDOCKERS_path=config['SITE']['TILEDOCKER_DIR']
DOCKERSPACE_DIR=config['SITE']['DOCKERSPACE_DIR']
#NOVNC_URL=config['SITE']['NOVNC_URL']
GPU_FILE=config['SITE']['GPU_FILE']

SSH_FRONTEND=config['SITE']['SSH_FRONTEND']
SSH_LOGIN=config['SITE']['SSH_LOGIN']
SSH_IP=config['SITE']['SSH_IP']
init_IP=config['SITE']['init_IP']

config.read(CASE_config)

CASE=config['CASE']['CASE_NAME']
App="OpenGL Display"

NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

CASE_DOCKER_PATH=config['CASE']['CASE_DOCKER_PATH']

network=config['CASE']['network']
nethost=config['CASE']['nethost']
domain=config['CASE']['domain']

OPTIONssh=config['CASE']['OPTIONssh']
SOCKETdomain=config['CASE']['SOCKETdomain']

DOCKER_NAME=config['CASE']['DOCKER_NAME']

DATA_PATH=config['CASE']['DATA_PATH']
DATA_MOUNT_DOCKER=config['CASE']['DATA_MOUNT_DOCKER']
DATA_PATH_DOCKER=config['CASE']['DATA_PATH_DOCKER']
HAVE_ATLAS=bool(int(config['CASE']['HAVE_ATLAS'].replace('\"','')))
CASE_DATA_CONFIG=config['CASE']['CASE_DATA_CONFIG']

START_ANA_DISPATCH=config['CASE']['START_ANA_DISPATCH']
CONTAINER_PYTHON=config['CASE']['CONTAINER_PYTHON']
CONTAINER_ANA_DISPATCHER=config['CASE']['CONTAINER_ANA_DISPATCHER']

OPTIONS=config['CASE']['OPTIONS'].replace("$","").replace('"','')
print("\nOPTIONS from CASE_CONFIG : "+OPTIONS)
OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
OPTIONS="".join(list(map( replaceconf,OPTIONS)))
print("OPTIONS after replacement : "+OPTIONS)

if HAVE_ATLAS:
    NUM_ANA=NUM_DOCKERS-1
else:
    NUM_ANA=NUM_DOCKERS
NumMaxClient=NUM_ANA-1

CreateTS='create TS='+TileSet+' Nb='+str(NUM_DOCKERS)

client.send_server(CreateTS)

COMMANDStop="echo 'JobID is not defined.'"

# Global commands
# Execute on each/a set of tiles
ExecuteTS='execute TS='+TileSet+" "
# Launch a command on the frontend
LaunchTS='launch TS='+TileSet+" "+JOBPath+' '

# Build ANATOMIST dir
# client.send_server(LaunchTS+" mkdir "+CASE)
# print("Out of mkdir %s : %s" % (CASE, str(client.get_OK())))
#CASEdir=os.path.join(JOBPath,CASE)
#LaunchTSC='launch TS='+TileSet+" "+CASEdir+' '

# get TiledAnatomist package from Github
COMMAND_GIT="git clone -q https://github.com/mmancip/TiledAnatomist.git"
print("command_git : "+COMMAND_GIT)
os.system(COMMAND_GIT)

# Send CASE and SITE files
try:
    client.send_server(LaunchTS+' chmod og-rxw '+JOBPath)
    print("Out of chmod JOBPath : "+ str(client.get_OK()))

    send_file_server(client,TileSet,".", CASE_config, JOBPath)
    CASE_config=os.path.join(JOBPath,CASE_config)
    send_file_server(client,TileSet,".", SITE_config, JOBPath)
    SITE_config=os.path.join(JOBPath,os.path.basename(SITE_config))
    send_file_server(client,TileSet,".", os.path.basename(CASE_DATA_CONFIG), JOBPath)
    send_file_server(client,TileSet,".", GPU_FILE, JOBPath)

except:
    print("Error sending files !")
    traceback.print_exc(file=sys.stdout)
    try:
        code.interact(banner="Try sending files by yourself :",local=dict(globals(), **locals()))
    except SystemExit:
        pass


COMMAND_TiledAnatomist=LaunchTS+COMMAND_GIT
client.send_server(COMMAND_TiledAnatomist)
print("Out of git clone TiledAnatomist : "+ str(client.get_OK()))

COMMAND_copy=LaunchTS+" cp -rp TiledAnatomist/anatomist_server "+\
               "TiledAnatomist/anatomist_client "+\
               "TiledAnatomist/anatomist_dispatcher "+\
               "TiledAnatomist/patch_nodes_file_with_data.py "+\
               "TiledAnatomist/build_nodes_file "+\
               "TiledAnatomist/"+START_ANA_DISPATCH+" "+\
               "TiledAnatomist/"+CONTAINER_ANA_DISPATCHER+" "+\
               "TiledAnatomist/icons "+\
               "./"

client.send_server(COMMAND_copy)
print("Out of copy scripts from TiledAnatomist : "+ str(client.get_OK()))

# Launch containers HERE
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+DOCKERSPACE_DIR+" "+DOCKER_NAME

print("\nREF_CAS : "+REF_CAS)

COMMANDStop=os.path.join(TILEDOCKERS_path,"stop_dockers")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
print("\n"+COMMANDStop)
sys.stdout.flush()

try:
    stateVM=Run_dockers()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()


# Get password file with right number of lines (NUM_DOCKERS)
out_get=0
try:
    out_get=get_file_client(client,TileSet,JOBPath,"list_dockers_pass",".")
    logging.warning("out get list_dockers_pass : "+str(out_get))
except:
    pass
try:
    count=0
    while( int(out_get) <= 0):
        time.sleep(10)
        os.system('mv list_dockers_pass list_dockers_pass_')
        out_get=get_file_client(client,TileSet,JOBPath,"list_dockers_pass",".")
        logging.warning("out get list_dockers_pass : "+str(out_get))
        count=count+1
        if (count > 10):
            logging.error("Error create list_dockers_pass. Job stopped.")
            kill_all_containers()
            sys.exit(0)
except:
    pass

size=0
try:
    with open('list_dockers_pass') as f:
        size=len([0 for _ in f])
except:
    pass

while(size != NUM_DOCKERS):
    time.sleep(10)
    os.system('mv list_dockers_pass list_dockers_pass_')
    try:
        out_get=get_file_client(client,TileSet,JOBPath,"list_dockers_pass",".")
    except:
        pass
    try:
        with open('list_dockers_pass') as f:
            size=len([0 for _ in f])
    except:
        pass

logging.warning("list_dockers_pass OK %d %d" % (size,NUM_DOCKERS))


try:
    if (stateVM):
        build_nodes_file()
        
        while(os.path.getsize("nodes.json_init") < 50):
            time.sleep(5)
            logging.warning("nodes.json_init to small. Try another build.")
            build_nodes_file()
            if (os.path.getsize("nodes.json_init") < 50):
                logging.error("Something has gone wrong with build_nodes_file 2.")
                kill_all_containers()
            else:
                break

    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
logging.warning("after build_nodes_json %r" % (stateVM))
#get_file_client(client,TileSet,JOBPath,"nodes.json",".")

try:
    if (stateVM):
        nodes_json_init()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
logging.warning("after nodes_json_init %r" % (stateVM))

try:
    if (stateVM):
        stateVM=share_ssh_key()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
logging.warning("after share ssh keys %r" % (stateVM))

time.sleep(2)

logging.warning("Before launch_tunnel.")

try:
    if (stateVM):
        stateVM=launch_tunnel()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    #kill_all_containers()
print("after launch tunnel servers %r" % (stateVM))

try:
    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()
except:
    print("nodes.json doesn't exists !")
    print("ls -la")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    #kill_all_containers()

print("after read nodes.json %r" % (stateVM))

try:
    if (stateVM):
        stateVM=launch_vnc()
except:
    print("Problem when launch vnc !")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    #kill_all_containers()

print("after launch vnc servers %r" % (stateVM))

time.sleep(2)
# Launch docker tools
if (stateVM):
    all_resize("1300x520")

reallaunch=True
def Run_server(launch=False):
    COMMAND_Server=ExecuteTS+' Tiles=('+containerId(1)+') '+\
                       CASE_DOCKER_PATH+'anatomist_server '+\
                       CONTAINER_PYTHON+' '+\
                       CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER
    print("COMMAND_Server: \n"+COMMAND_Server)
    if (launch):
        client.send_server(COMMAND_Server)
        print("Out of anatomist_server : "+ str(client.get_OK()))
    else:
        print("Run server : Run_server(True)")
        
Run_server(reallaunch)

def Get_server_IP():
    init_IP="0"
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+
                       'bash -c "/usr/local/bin/get_ip.sh; cp .vnc/myip CASE/serverip"')
    #'scp .vnc/myip '+HTTP_LOGIN+'@'+HTTP_FRONTEND+':'+JOBPath+'"')
    print("Out of get ip : "+ str(client.get_OK()))
    get_file_client(client,TileSet,JOBPath,"serverip",".")
    # while( get_file_client(client,TileSet,JOBPath,"serverip",".") < 0):
    #     time.sleep(1)
    #     pass
    try:
        with open("serverip",'r') as fserverip:
            init_IP=fserverip.read().replace(domain+'.',"").replace("\n","")
            print("Server ip : "+domain+'.'+init_IP)
    except:
        print("Cannot retreive server ip.")
        pass
    sys.stdout.flush()
    return init_IP

init_IP=Get_server_IP()

List_anatomist=range(2,NUM_ANA+1)

# Give the anatomist_client command to the whole list :
#   (obsolete : list(map(containerId, List_anatomist)) and too long list for message)
# client.send_server(bExecuteTS+' Tiles='+str(List_anatomist)+' '+
#     CASE_DOCKER_PATH+'anatomist_client '+
#     CONTAINER_PYTHON+' '+
#     CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
#     domain+"."+init_IP)

def Run_clients(launch=False):
    # Split the list :
    splv=8
    for i in range(int(NUM_ANA/splv+1)):
        sublist=list(map(List_anatomist.__getitem__, range(i*splv,min((i+1)*splv,NumMaxClient))))
        #print(str(sublist))
        if (len(sublist) == 0):
            break
        arglist=list(map(containerId, sublist))
        #print(str(arglist))
        COMMANDclient= CASE_DOCKER_PATH+'anatomist_client '+CONTAINER_PYTHON+' '+\
                       CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+\
                       domain+"."+init_IP
        sys.stdout.flush()
        print("Command %d of anatomist_client : %s " % (i,COMMANDclient))
        if (launch):
            client.send_server(ExecuteTS+' Tiles='+str(arglist)+' '+COMMANDclient)
            print("Out %d of anatomist_client : %s " % (i,str(client.get_OK())))
        sys.stdout.flush()
        
    if HAVE_ATLAS:
        COMMAND_ATLAS=ExecuteTS+' Tiles=('+containerId(NUM_ANA+1)+') '+\
                           CASE_DOCKER_PATH+'anatomist_client '+\
                           CONTAINER_PYTHON+' '+\
                           CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+\
                           domain+"."+init_IP+' true'
        print("COMMAND_ATLAS : "+COMMAND_ATLAS)
        if (launch):
            client.send_server(COMMAND_ATLAS)
            print("Out atlas of anatomist_client : %s " % (str(client.get_OK())))
        
        sys.stdout.flush()
    if (not launch):
        print("Run clients : Run_clients(True)")

try:
    if (stateVM):
        Run_clients(reallaunch)
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)

taglist=os.path.join(CASE_DOCKER_PATH,CASE_DATA_CONFIG)

# execute synchrone ?
def Run_dispatcher(launch=False):
    COMMAND_DISPATCHER=CASE_DOCKER_PATH+'anatomist_dispatcher '+str(NUM_ANA)+' '+CONTAINER_PYTHON+\
                    ' '+CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+\
                    ' '+CASE_DOCKER_PATH+START_ANA_DISPATCH+' '+taglist+\
                    ' '+DATA_PATH_DOCKER
    print("COMMAND_DISPATCHER : "+COMMAND_DISPATCHER)
    if (launch):
        client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+'nohup bash -c "'+COMMAND_DISPATCHER+' </dev/null 2>&1 >.vnc/out_dispatcher_$$" &')
        print("Out of anatomist_dispatcher : "+str(client.get_OK()))
    else:
        print("Run dispatcher : Run_dispatcher(True)")

Run_dispatcher(reallaunch)
sys.stdout.flush()

NUM_DATA=NUM_DOCKERS-1
jtaglist=json.load(open(CASE_DATA_CONFIG))

def next_element(tileNum=-1):
    global NUM_DATA
    tileId=str(containerId(tileNum+1))
    NUM_DATA=NUM_DATA+1
    if (len(jtaglist["data_list"]) > NUM_DATA):
        data=jtaglist["data_list"][NUM_DATA]

        nodes["nodes"][tileNum]["title"]=data["subject"]
        if ("variable" in nodes["nodes"][tileNum]):
            nodes["nodes"][tileNum]["variable"]="ID-"+tileId+"_"+data["subject"]
        nodes["nodes"][tileNum]["comment"]=str(data)
        if ("usersNotes" in nodes["nodes"][tileNum]):
            nodes["nodes"][tileNum]["usersNotes"]=str(data)
        nodes["nodes"][tileNum]["tags"]=data["tags"]
        
        nodesf=open("nodes.json",'w')
        nodesf.write(json.dumps(nodes))
        nodesf.close()
        
        
        COMMAND_NEXT='/opt/brainvisa/bin/python/start_ana_dispatcher.py -s '+str(data["subject"])+\
                    ' -i '+str(tilenum)+\
                    ' -a '+CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+\
                    ' -d '+DATA_PATH_DOCKER
        print("COMMAND_NEXT : "+COMMAND_NEXT)
        
        client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+'nohup bash -c "'+COMMAND_NEXT+' </dev/null 2>&1 >.vnc/out_next_$$" &')
        print("Out of anatomist_next : "+str(client.get_OK()))
        
        # CommandTSK=ExecuteTS+TilesStr+COMMANDKill
        # client.send_server(CommandTSK)
        # client.get_OK()


if (stateVM):
    init_wmctrl()

# def clear_vnc(tileNum=-1,tileId='001'):
#     if ( tileNum > -1 ):
#         TilesStr=' Tiles=('+containerId(tileNum+1)+') '
#     else:
#         TilesStr=' Tiles=('+tileId+') '
#     client.send_server(ExecuteTS+TilesStr+' x11vnc -R clear-all')
#     print("Out of clear-vnc : "+ str(client.get_OK()))

try:
    if (stateVM):
        clear_vnc_all()
except:
    traceback.print_exc(file=sys.stdout)


def launch_changesize(RESOL="1920x1080",tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    COMMAND=ExecuteTS+TilesStr+' xrandr --fb '+RESOL
    print("call server with : "+COMMAND)
    client.send_server(COMMAND)
    print("server answer is "+str(client.get_OK()))

def launch_smallsize(tileNum=-1,tileId='001'):
    print("Launch launch_changesize smallsize for tile "+str(tileNum))
    launch_changesize(tileNum=tileNum,RESOL="1300x520")

def launch_bigsize(tileNum=-1,tileId='001'):
    print("Launch launch_changesize bigsize for tile "+str(tileNum))
    launch_changesize(tileNum=tileNum,RESOL="2000x800")

def fullscreenApp(tileNum=-1,tileId='001'):
    COMMAND='/opt/movewindows subject: -b toggle,fullscreen'
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '            
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    client.get_OK()

def showGUI(tileNum=-1,tileId='001'):
    COMMAND='/opt/movewindows Anatomist -b toggle,above'
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '            
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    client.get_OK()


launch_actions_and_interact()

try:
    print("isActions: "+str(isActions))
except:
    print("isActions not defined.")

kill_all_containers()
    
sys.exit(0)

for i in List_anatomist:
    client.send_server(ExecuteTS+' Tiles=('+containerId(i)+') '+
                       '/opt/movewindows  subject: -b remove,maximized_vert,maximized_horz')
    client.get_OK()



for i in List_anatomist:
    client.send_server(ExecuteTS+' Tiles=('+containerId(i)+') '+
                       '/opt/movewindows  subject: -b add,fullscreen')
    client.get_OK()


