#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys,os,time
import code
import argparse
import re, datetime

# HPC Machine working directory
#In TVConnection :
# DATE=re.sub(r'\..*','',datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-"))
# TiledVizPath='/login/.tiledviz'
# JOBPath='/login/.tiledviz/ANATOMIST_'+DATE

# CASE_NAME in case_config:
#CASE="ANATOMIST"
#In TVConnection : TileSet="Leonie64"
SITE_config='./site_config.ini'
CASE_config="./case_config.ini"

if __name__ == '__main__':
    
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
    #print("OPTIONS before replacement : "+str(OPTIONS))

    OPTIONS="".join(list(map( replaceconf,OPTIONS)))
    print("OPTIONS after replacement : "+OPTIONS)
    
    if HAVE_ATLAS:
        NUM_ANA=NUM_DOCKERS-1
    else:
        NUM_ANA=NUM_DOCKERS
    NumMaxClient=NUM_ANA-1

    CreateTS='create TS='+TileSet+' Nb='+str(NUM_DOCKERS)

    client.send_server(CreateTS)

    # Build ANATOMIST dir
    client.send_server('launch TS='+TileSet+" "+JOBPath+" mkdir "+CASE)
    print("Out of mkdir %s : %s" % (CASE, str(client.get_OK())))
    CASEdir=os.path.join(JOBPath,CASE)

    # get TiledAnatomist package from Github
    os.system("git clone https://github.com/mmancip/TiledAnatomist.git ANATOMIST")
    #("tar xfz ANATOMIST.tgz")
    
    command='launch TS='+TileSet+" "+TiledVizPath+" cp -p build_qr "+os.path.join(JOBPath,'..')
    print("cp build_qr : %s" % (command))
    client.send_server(command)
    print("Out of cp build_qr : %s" % (str(client.get_OK())))

    send_file_server(client,TileSet,"ANATOMIST","anatomist_server",JOBPath)
    send_file_server(client,TileSet,"ANATOMIST","anatomist_client",JOBPath)
    send_file_server(client,TileSet,"ANATOMIST","anatomist_dispatcher",JOBPath)
    send_file_server(client,TileSet,"ANATOMIST","build_nodes_file", JOBPath)
    send_file_server(client,TileSet,"ANATOMIST",START_ANA_DISPATCH,JOBPath)
    send_file_server(client,TileSet,"ANATOMIST",CONTAINER_ANA_DISPATCHER,JOBPath)

    ANATOMISTicons=os.path.join(JOBPath,"icons")
    client.send_server('launch TS='+TileSet+" "+JOBPath+" mkdir icons")
    print("Out of mkdir %s : %s" % (ANATOMISTicons, str(client.get_OK())))

    for (dirpath, dirname, filelist) in os.walk("ANATOMIST/icons"):
        for filename in filelist:
            print("Send %s to icons" % (str(filename)))        
            send_file_server(client,TileSet,"ANATOMIST/icons",filename,ANATOMISTicons)


    # Send CASE and SITE files
    send_file_server(client,TileSet,".", CASE_config, CASEdir)
    CASE_config=os.path.join(CASEdir,CASE_config)
    send_file_server(client,TileSet,".", SITE_config, JOBPath)
    SITE_config=os.path.join(JOBPath,os.path.basename(SITE_config))
    send_file_server(client,TileSet,".", os.path.basename(CASE_DATA_CONFIG), CASEdir)
    send_file_server(client,TileSet,".", "list_hostsgpu", CASEdir)

    # Launch containers HERE
    REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+DOCKERSPACE_DIR+" "+DOCKER_NAME

    print("\nREF_CAS : "+REF_CAS)

    COMMANDStop=os.path.join(TILEDOCKERS_path,"stop_dockers")+" "+REF_CAS+" "+os.path.join(CASEdir,GPU_FILE)
    print("\n"+COMMANDStop)

    # Launch dockers
    COMMAND=os.path.join(TILEDOCKERS_path,"launch_dockers")+" "+REF_CAS+" "+GPU_FILE+" "+HTTP_FRONTEND+":"+HTTP_IP+\
             " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS

    print("\nCommand dockers : "+COMMAND)

    client.send_server('launch TS='+TileSet+" "+CASEdir+' '+COMMAND)
    #code.interact(local=locals())
    print("Out of launch dockers : "+ str(client.get_OK()))

    # Build nodes.json file from new dockers list
    COMMAND='launch TS='+TileSet+" "+CASEdir+' ../build_nodes_file '+CASE_config+' '+SITE_config
    print("\nCommand dockers : "+COMMAND)

    client.send_server(COMMAND)
    print("Out of build_nodes_file : "+ str(client.get_OK()))

    get_file_client(client,TileSet,CASEdir,"nodes.json",".")
        
    # Launch docker tools
    client.send_server('execute TS='+TileSet+' /opt/tunnel_ssh '+SOCKETdomain+' '+HTTP_FRONTEND+' '+HTTP_LOGIN)
    print("Out of tunnel_ssh : "+ str(client.get_OK()))
    
    client.send_server('execute TS='+TileSet+' /opt/vnccommand')
    print("Out of vnccommand : "+ str(client.get_OK()))

    client.send_server('execute TS='+TileSet+' xrandr --fb 1300x520')
    print("Out of xrandr : "+ str(client.get_OK()))

    client.send_server('execute TS='+TileSet+' wmctrl -l -G')
    print("Out of wmctrl : "+ str(client.get_OK()))


    client.send_server('execute TS='+TileSet+' Tiles=('+containerId(1)+') '+
                       CASE_DOCKER_PATH+'anatomist_server '+
                       CONTAINER_PYTHON+' '+
                       CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER)
    print("Out of anatomist_server : "+ str(client.get_OK()))

    
    List_anatomist=range(2,NUM_ANA+1)
        
    # Give the anatomist_client command to the whole list : 
    #   (obsolete : list(map(containerId, List_anatomist)) and too long list for message)
    # client.send_server(b'execute TS='+TileSet+' Tiles='+str(List_anatomist)+' '+
    #     CASE_DOCKER_PATH+'anatomist_client '+
    #     CONTAINER_PYTHON+' '+
    #     CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
    #     domain+"."+init_IP)

    # Split the list :
    splv=10
    for i in range(int(NUM_ANA/splv+1)):
        sublist=list(map(List_anatomist.__getitem__, range(i*splv,min((i+1)*splv,NumMaxClient))))
        #print(str(sublist))
        if (len(sublist) == 0):
            break
        arglist=list(map(containerId, sublist))
        #print(str(arglist))

        client.send_server('execute TS='+TileSet+' Tiles='+str(arglist)+' '+
                           CASE_DOCKER_PATH+'anatomist_client '+
                           CONTAINER_PYTHON+' '+
                           CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
                           domain+"."+init_IP)
        print("Out %d of anatomist_client : %s " % (i,str(client.get_OK())))

    # client.send_server(b'execute TS='+TileSet+' '+
    #     CASE_DOCKER_PATH+'anatomist_client '+
    #     CONTAINER_PYTHON+' '+
    #     CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
    #     domain+"."+init_IP)
    
    if HAVE_ATLAS:
        client.send_server('execute TS='+TileSet+' Tiles=('+containerId(NUM_ANA+1)+') '+
                           CASE_DOCKER_PATH+'anatomist_client '+
                           CONTAINER_PYTHON+' '+
                           CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+' '+
                           domain+"."+init_IP+' true' )
        print("Out atlas of anatomist_client : %s " % (str(client.get_OK())))

    # execute synchrone ?
    COMMAND_SERVER=CASE_DOCKER_PATH+'anatomist_dispatcher '+str(NUM_ANA)+' '+CONTAINER_PYTHON+\
                    ' '+CASE_DOCKER_PATH+CONTAINER_ANA_DISPATCHER+\
                    ' '+CASE_DOCKER_PATH+START_ANA_DISPATCH+' '+os.path.join(CASE_DOCKER_PATH,CASE_DATA_CONFIG)+\
                    ' '+DATA_PATH_DOCKER
    print("COMMAND_SERVER : "+COMMAND_SERVER)
    client.send_server('execute TS='+TileSet+' Tiles=('+containerId(1)+') '+COMMAND_SERVER)
    print("Out of anatomist_dispatcher : "+str(client.get_OK()))

    try:
        code.interact(banner="Code interact :",local=dict(globals(), **locals()))
    except SystemExit:
        pass
    
    client.send_server('execute TS='+TileSet+' killall Xvnc')
    print("Out of killall command : "+ str(client.get_OK()))

    client.send_server('launch TS='+TileSet+" "+JOBPath+" "+COMMANDStop)
    client.close()
    sys.exit(0)
    
    for i in List_anatomist:
        client.send_server('execute TS='+TileSet+' Tiles=('+containerId(i)+') '+
                           '/opt/movewindows  subject: -b remove,maximized_vert,maximized_horz')
        client.get_OK()


    for i in List_anatomist:
        client.send_server('execute TS='+TileSet+' Tiles=('+containerId(i)+') '+
                           '/opt/movewindows Anatomist -b toggle,above')
        client.get_OK()


    for i in List_anatomist:
        client.send_server('execute TS='+TileSet+' Tiles=('+containerId(i)+') '+
                           '/opt/movewindows  subject: -b add,fullscreen')
        client.get_OK()


    for i in List_anatomist:
        client.send_server('execute TS='+TileSet+' Tiles=('+containerId(i)+') '+
                           '/opt/movewindows subject: -b toggle,fullscreen')
        client.get_OK()

        
    client.send_server('execute TS='+TileSet+' killall Xvnc')
    print("Out of killall command : "+ str(client.get_OK()))

    client.close()
