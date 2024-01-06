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

TILEDVIZ_DIR=config['SITE']['TILEDVIZ_DIR']
TILESINGULARITYS_DIR=os.path.join(TILEDVIZ_DIR,"TVConnections/Singularity")
TilesScriptsPath=TILESINGULARITYS_DIR
SPACE_DIR=config['SITE']['SPACE_DIR']
#NOVNC_URL=config['SITE']['NOVNC_URL']
GPU_FILE=config['SITE']['GPU_FILE']

SSH_FRONTEND=config['SITE']['SSH_FRONTEND']
SSH_LOGIN=config['SITE']['SSH_LOGIN']
SSH_IP=config['SITE']['SSH_IP']

SSL_PUBLIC=config['SITE']['SSL_PUBLIC']
SSL_PRIVATE=config['SITE']['SSL_PRIVATE']

config.read(CASE_config)

CASE=config['CASE']['CASE_NAME']
NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

CASE_DOCKER_PATH=config['CASE']['CASE_DOCKER_PATH']

network=config['CASE']['network']
nethost=config['CASE']['nethost']
domain=config['CASE']['domain']

OPTIONssh=config['CASE']['OPTIONssh']
SOCKETdomain=config['CASE']['SOCKETdomain']

SINGULARITY_NAME=config['CASE']['SINGULARITY_NAME']

DATA_PATH=config['CASE']['DATA_PATH']
DATA_MOUNT_SINGULARITY=config['CASE']['DATA_MOUNT_SINGULARITY']
DATA_PATH_SINGULARITY=config['CASE']['DATA_PATH_SINGULARITY']
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
COMMAND_GIT="git clone https://github.com/mmancip/TiledAnatomist.git"
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
    send_file_server(client,TileSet,".", "list_hostsgpu", JOBPath)

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
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+SPACE_DIR+" "+SINGULARITY_NAME

print("\nREF_CAS : "+REF_CAS)

COMMANDStop=os.path.join(TILESINGULARITYS_DIR,"stop_singularitys")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
print("\n"+COMMANDStop)
sys.stdout.flush()

# Launch singularitys
def Run_singularitys():
    COMMAND="bash -c \""+os.path.join(TILESINGULARITYS_DIR,"launch_singularitys")+" "+REF_CAS+" "+GPU_FILE+" "+SSH_FRONTEND+":"+SSH_IP+" "+TILEDVIZ_DIR+" "+TILESINGULARITYS_DIR+\
             " TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\
             " > "+os.path.join(JOBPath,"output_launch")+" 2>&1 \"" 
#             " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\

    logging.warning("\nCommand singularitys : "+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    state=client.get_OK()
    logging.warning("Out of launch singularity : "+ str(state))
    sys.stdout.flush()
    stateVM=(state == 0)
    return stateVM

try:
    stateVM=Run_singularitys()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()


    
try:
    if (stateVM):
        build_nodes_file()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()


time.sleep(2)
# Launch singularity tools
if (stateVM):
    all_resize("1920x1080")


try:
    if (stateVM):
        stateVM=launch_tunnel()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
print("after launch tunnel servers %r" % (stateVM))

try:
    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()
except:
    print("nodes.json doesn't exists !")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()

print("after read nodes.json %r" % (stateVM))

try:
    if (stateVM):
        stateVM=launch_vnc()
except:
    print("Problem when launch vnc !")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()

print("after launch vnc servers %r" % (stateVM))


def Run_server():
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+
                       os.path.join(CASE_DOCKER_PATH,'anatomist_server')+' '+
                       CONTAINER_PYTHON+' '+
                       os.path.join(CASE_DOCKER_PATH,CONTAINER_ANA_DISPATCHER))
    print("Out of anatomist_server : "+ str(client.get_OK()))
    sys.stdout.flush()

try:
    if (stateVM):
        Run_server()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)

def Get_server_IP():
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+
                       'bash -c "'+os.path.join(TILEDVIZ_DIR,'TVConnections/get_ip.sh')+'; cp .vnc/myip CASE/serverip"')
    #'scp .vnc/myip '+HTTP_LOGIN+'@'+HTTP_FRONTEND+':'+JOBPath+'"')
    print("Out of get ip : "+ str(client.get_OK()))
    sys.stdout.flush()
    get_file_client(client,TileSet,JOBPath,"serverip",".")
    # while( get_file_client(client,TileSet,JOBPath,"serverip",".") < 0):
    #     time.sleep(1)
    #     pass
    try:
        with open("serverip",'r') as fserverip:
            init_IP=fserverip.read().replace(domain+'.',"").replace("\n","")
            print("Server ip : "+domain+'.'+init_IP)
            sys.stdout.flush()
    except:
        print("Cannot retreive server ip.")        
        sys.stdout.flush()
        init_IP="1.1.1.1"
        pass
    return init_IP
    sys.stdout.flush()

try:
    if (stateVM):
        init_IP=Get_server_IP()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)

List_anatomist=range(2,NUM_ANA+1)
    
# Give the anatomist_client command to the whole list : 
#   (obsolete : list(map(containerId, List_anatomist)) and too long list for message)
# client.send_server(bExecuteTS+' Tiles='+str(List_anatomist)+' '+
#     CASE_DOCKER_PATH+'anatomist_client '+
#     CONTAINER_PYTHON+' '+
#     CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
#     domain+"."+init_IP)

def Run_clients():
    # Split the list :
    splv=10
    for i in range(int(NUM_ANA/splv+1)):
        sublist=list(map(List_anatomist.__getitem__, range(i*splv,min((i+1)*splv,NumMaxClient))))
        #print(str(sublist))
        if (len(sublist) == 0):
            break
        arglist=list(map(containerId, sublist))
        #print(str(arglist))
        COMMANDclient=os.path.join(CASE_DOCKER_PATH,'anatomist_client')+' '+\
                       CONTAINER_PYTHON+' '+\
                       os.path.join(CASE_DOCKER_PATH,CONTAINER_ANA_DISPATCHER)+' '+\
                       domain+"."+init_IP
        sys.stdout.flush()
        print("Command %d of anatomist_client : %s " % (i,COMMANDclient))
        client.send_server(ExecuteTS+' Tiles='+str(arglist)+' '+COMMANDclient)
        print("Out %d of anatomist_client : %s " % (i,str(client.get_OK())))
        sys.stdout.flush()

        # client.send_server(bExecuteTS+' '+
        #     CASE_DOCKER_PATH+'anatomist_client '+
        #     CONTAINER_PYTHON+' '+
        #     CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
        #     domain+"."+init_IP)
        
    if HAVE_ATLAS:
        client.send_server(ExecuteTS+' Tiles=('+containerId(NUM_ANA+1)+') '+
                           os.path.join(CASE_DOCKER_PATH,'anatomist_client')+' '+
                           CONTAINER_PYTHON+' '+
                           os.path.join(CASE_DOCKER_PATH,CONTAINER_ANA_DISPATCHER)+' '+
                           domain+"."+init_IP+' true' )
        print("Out atlas of anatomist_client : %s " % (str(client.get_OK())))
        sys.stdout.flush()

try:
    if (stateVM):
        Run_clients()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)


# execute synchrone ?
def Run_dispatcher():
    COMMAND_DISPATCHER=os.path.join(CASE_DOCKER_PATH,'anatomist_dispatcher')+str(NUM_ANA)+' '+\
                       CONTAINER_PYTHON+' '+\
                       os.path.join(CASE_DOCKER_PATH,CONTAINER_ANA_DISPATCHER)+' '+\
                       os.path.join(CASE_DOCKER_PATH,START_ANA_DISPATCH)+' '+\
                       os.path.join(CASE_DOCKER_PATH,CASE_DATA_CONFIG)+\
                    ' '+DATA_PATH_SINGULARITY
    print("COMMAND_DISPATCHER : "+COMMAND_DISPATCHER)
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+'nohup bash -c "'+COMMAND_DISPATCHER+' </dev/null 2>&1 >.vnc/out_dispatcher_$$" &')
    print("Out of anatomist_dispatcher : "+str(client.get_OK()))

try:
    if (stateVM):
        Run_dispatcher()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)


if (stateVM):
    init_wmctrl()

# def clear_vnc(tileNum=-1,tileId='001'):
#     if ( tileNum > -1 ):
#         TilesStr=' Tiles=('+containerId(tileNum+1)+') '
#     else:
#         TilesStr=' Tiles=('+tileId+') '
#     client.send_server(ExecuteTS+TilesStr+' x11vnc -R clear-all')
#     print("Out of clear-vnc : "+ str(client.get_OK()))

# def clear_vnc_all():
#     for i in List_anatomist:
#         clear_vnc(i-1)
#         #clear_vnc(tileId=containerId(i))


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
    COMMAND=os.path.join(TILESINGULARITYS_DIR,"movewindows")+' subject: -b toggle,fullscreen'
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '            
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    client.get_OK()

def showGUI(tileNum=-1,tileId='001'):
    COMMAND=os.path.join(TILESINGULARITYS_DIR,"movewindows")+' Anatomist -b toggle,above'
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '            
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+COMMAND)
    client.get_OK()


def kill_all_containers():
    stateVM=True
    client.send_server(ExecuteTS+' killall -9 Xvfb')
    state=client.get_OK()
    print("Out of killall command : "+ str(state))
    client.send_server(LaunchTS+" "+COMMANDStop)
    state=client.get_OK()
    print("Out of COMMANDStop : "+ str(state))
    stateVM=(state == 0)
    time.sleep(2)
    Remove_TileSet()
    return stateVM
    

#isActions=True
launch_actions_and_interact()

try:
    print("isActions: "+str(isActions))
except:
    print("isActions not defined.")

kill_all_containers()
    
sys.exit(0)

for i in List_anatomist:
    client.send_server(ExecuteTS+' Tiles=('+containerId(i)+') '+
                       os.path.join(TILESINGULARITYS_DIR,"movewindows")+' subject: -b remove,maximized_vert,maximized_horz')
    client.get_OK()



for i in List_anatomist:
    client.send_server(ExecuteTS+' Tiles=('+containerId(i)+') '+
                       os.path.join(TILESINGULARITYS_DIR,"movewindows")+' subject: -b add,fullscreen')
    client.get_OK()


