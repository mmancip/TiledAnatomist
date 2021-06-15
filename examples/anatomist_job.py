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

HTTP_FRONTEND=config['SITE']['HTTP_FRONTEND']
HTTP_LOGIN=config['SITE']['HTTP_LOGIN']
HTTP_IP=config['SITE']['HTTP_IP']
init_IP=config['SITE']['init_IP']

config.read(CASE_config)

CASE=config['CASE']['CASE_NAME']
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
def replaceconf(x):
    if (re.search('}',x)):
        varname=x.replace("{","").replace("}","")
        return config['CASE'][varname]
    else:
        return x
OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
OPTIONS="".join(list(map( replaceconf,OPTIONS)))

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
print("Out of copy scripts from TiledCourse : "+ str(client.get_OK()))

# Launch containers HERE
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+DOCKERSPACE_DIR+" "+DOCKER_NAME

print("\nREF_CAS : "+REF_CAS)

COMMANDStop=os.path.join(TILEDOCKERS_path,"stop_dockers")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
print("\n"+COMMANDStop)
sys.stdout.flush()

# Launch dockers
def Run_dockers():
    COMMAND="bash -vx -c \""+os.path.join(TILEDOCKERS_path,"launch_dockers")+" "+REF_CAS+" "+GPU_FILE+" "+HTTP_FRONTEND+":"+HTTP_IP+\
             " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\
             " > "+os.path.join(JOBPath,"output_launch")+" 2>&1 \"" 

    print("\nCommand dockers : "+COMMAND)

    client.send_server(LaunchTS+' '+COMMAND)
    print("Out of launch dockers : "+ str(client.get_OK()))
    sys.stdout.flush()

Run_dockers()
sys.stdout.flush()

# Build nodes.json file from new dockers list
def build_nodes_file():
    print("Build nodes.json file from new dockers list.")
    # COMMAND=LaunchTS+' chmod u+x build_nodes_file '
    # client.send_server(COMMAND)
    # print("Out of chmod build_nodes_file : "+ str(client.get_OK()))

    COMMAND=LaunchTS+' ./build_nodes_file '+os.path.join(JOBPath,CASE_config)+' '+os.path.join(JOBPath,SITE_config)+' '+TileSet
    print("\nCommand dockers : "+COMMAND)

    client.send_server(COMMAND)
    print("Out of build_nodes_file : "+ str(client.get_OK()))
    time.sleep(2)

build_nodes_file()
sys.stdout.flush()
#get_file_client(client,TileSet,JOBPath,"nodes.json",".")
    
time.sleep(2)
# Launch docker tools
def launch_resize(RESOL="1300x520"):
    client.send_server(ExecuteTS+' xrandr --fb '+RESOL)
    print("Out of xrandr : "+ str(client.get_OK()))

launch_resize()

def launch_tunnel():
    # Call tunnel for VNC
    client.send_server(ExecuteTS+' /opt/tunnel_ssh '+HTTP_FRONTEND+' '+HTTP_LOGIN)
    print("Out of tunnel_ssh : "+ str(client.get_OK()))
    # Get back PORT
    for i in range(NUM_DOCKERS):
        i0="%0.3d" % (i+1)
        client.send_server(ExecuteTS+' Tiles=('+containerId(i+1)+') '+
                           'bash -c "cat .vnc/port |xargs -I @ sed -e \"s#port='+SOCKETdomain+i0+'#port=@#\" -i CASE/nodes.json"')
        print("Out of change port %s : " % (i0) + str(client.get_OK()))

    time.sleep(2)
    sys.stdout.flush()
    launch_nodes_json()

launch_tunnel()
sys.stdout.flush()

def launch_vnc():
    client.send_server(ExecuteTS+' /opt/vnccommand')
    print("Out of vnccommand : "+ str(client.get_OK()))

launch_vnc()

def init_wmctrl():
    client.send_server(ExecuteTS+' wmctrl -l -G')
    print("Out of wmctrl : "+ str(client.get_OK()))

init_wmctrl()

def Run_server():
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+
                       CASE_DOCKER_PATH+'anatomist_server '+
                       CONTAINER_PYTHON+' '+
                       CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER)    
    print("Out of anatomist_server : "+ str(client.get_OK()))
        
Run_server()

def Get_server_IP():
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
    return init_IP
    sys.stdout.flush()

init_IP=Get_server_IP()

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
        COMMANDclient= CASE_DOCKER_PATH+'anatomist_client '+CONTAINER_PYTHON+' '+\
                       CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+\
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
                           CASE_DOCKER_PATH+'anatomist_client '+
                           CONTAINER_PYTHON+' '+
                           CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
                           domain+"."+init_IP+' true' )
        print("Out atlas of anatomist_client : %s " % (str(client.get_OK())))
        sys.stdout.flush()

Run_clients()


# execute synchrone ?
def Run_dispatcher():
    COMMAND_DISPATCHER=CASE_DOCKER_PATH+'anatomist_dispatcher '+str(NUM_ANA)+' '+CONTAINER_PYTHON+\
                    ' '+CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+\
                    ' '+CASE_DOCKER_PATH+START_ANA_DISPATCH+' '+os.path.join(CASE_DOCKER_PATH,CASE_DATA_CONFIG)+\
                    ' '+DATA_PATH_DOCKER
    print("COMMAND_DISPATCHER : "+COMMAND_DISPATCHER)
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+'nohup bash -c "'+COMMAND_DISPATCHER+' </dev/null 2>&1 >.vnc/out_dispatcher_$$" &')
    print("Out of anatomist_dispatcher : "+str(client.get_OK()))

Run_dispatcher()
sys.stdout.flush()


def clear_vnc(tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+' x11vnc -R clear-all')
    print("Out of clear-vnc : "+ str(client.get_OK()))

def clear_vnc_all():
    for i in List_anatomist:
        clear_vnc(i-1)
        #clear_vnc(tileId=containerId(i))

clear_vnc_all()

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


def kill_all_containers():
    client.send_server(ExecuteTS+' killall Xvnc')
    print("Out of killall command : "+ str(client.get_OK()))
    client.send_server(LaunchTS+" "+COMMANDStop)
    client.close()
    

launch_actions_and_interact()

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


