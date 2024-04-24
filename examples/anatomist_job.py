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
#GPU_FILE=config['SITE']['GPU_FILE']


SSH_FRONTEND=config['SITE']['SSH_FRONTEND']
SSH_LOGIN=config['SITE']['SSH_LOGIN']
SSH_IP=config['SITE']['SSH_IP']

SSH_ENO=config['SITE']['SSH_ENO']

SSL_PUBLIC=config['SITE']['SSL_PUBLIC']
SSL_PRIVATE=config['SITE']['SSL_PRIVATE']

config.read(CASE_config)

CASE=config['CASE']['CASE_NAME']
NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

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
CONTAINER_ANA_LIB=config['CASE']['CONTAINER_ANA_LIB']

OPTIONS=config['CASE']['OPTIONS'].replace("$","").replace('"','')
print("\nOPTIONS from CASE_CONFIG : "+OPTIONS)
OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
OPTIONS="".join(list(map( replaceconf,OPTIONS)))
print("OPTIONS after replacement : "+OPTIONS)


SBATCH_NTASKS=config['CASE']['SBATCH_NTASKS']               # Nombre de processus
SBATCH_time=config['CASE']['SBATCH_time']                   # Temps souhaité pour la réservation
SBATCH_cpus_per_task=config['CASE']['SBATCH_cpus_per_task'] # utilisez 10 coeurs pour obtenir 1/4 de la RAM CPU
SBATCH_gpus=config['CASE']['SBATCH_gpus']
SBATCH_exclusive=eval(config['CASE']['SBATCH_exclusive'])   # Attention utilise la totalité du noeud
SBATCH_partition=config['CASE']['SBATCH_partition']         # Queue

CONTAINERS_PER_GPU=config['CASE']['CONTAINERS_PER_GPU']


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
sys.stdout.flush()
COMMAND_GITS=" bash -c 'cd TiledAnatomist; git checkout Singularity'"
print("command_git Singularity: "+COMMAND_GITS)
os.system(COMMAND_GITS)
sys.stdout.flush()

# Send CASE and SITE files
try:
    client.send_server(LaunchTS+' chmod og-rxw '+JOBPath)
    print("Out of chmod JOBPath : "+ str(client.get_OK()))

    send_file_server(client,TileSet,".", CASE_config, JOBPath)
    CASE_config=os.path.join(JOBPath,CASE_config)
    send_file_server(client,TileSet,".", SITE_config, JOBPath)
    SITE_config=os.path.join(JOBPath,os.path.basename(SITE_config))
    send_file_server(client,TileSet,".", os.path.basename(CASE_DATA_CONFIG), JOBPath)
#    send_file_server(client,TileSet,".", GPU_FILE, JOBPath)

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
sys.stdout.flush()
COMMAND_TiledAnatomist=LaunchTS+COMMAND_GITS
print("Command git checkout Singularity TiledAnatomist "+COMMAND_TiledAnatomist)
sys.stdout.flush()
client.send_server(COMMAND_TiledAnatomist)
print("Out of git checkout Singularity TiledAnatomist : "+ str(client.get_OK()))
sys.stdout.flush()

COMMAND_copy=LaunchTS+" cp -rp TiledAnatomist/patch_nodes_file_with_data.py "+\
               "TiledAnatomist/build_nodes_file "+\
               "TiledAnatomist/icons "+\
               "TiledAnatomist/anatomist_server "+\
               "TiledAnatomist/anatomist_client "+\
               "TiledAnatomist/anatomist_dispatcher "+\
               "TiledAnatomist/"+START_ANA_DISPATCH+" "+\
               "TiledAnatomist/"+CONTAINER_ANA_DISPATCHER+" "+\
               os.path.join(TILESINGULARITYS_DIR,"slurm_singularitys")+" "+\
               "./"


client.send_server(COMMAND_copy)
print("Out of copy scripts from TiledAnatomist : "+ str(client.get_OK()))

# Launch containers HERE
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+SPACE_DIR+" "+SINGULARITY_NAME

print("\nREF_CAS : "+REF_CAS)

#COMMANDStop=os.path.join(TILESINGULARITYS_DIR,"stop_singularitys")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
#print("\n"+COMMANDStop)
#sys.stdout.flush()

def sed_slurm(sed_string):
    COMMAND="bash -c \"sed -i "+os.path.join(JOBPath,"slurm_singularitys")+\
        " -e '"+sed_string+"'\"" #+\
    #        " > "+os.path.join(JOBPath,"output_sed_slurm")+datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-")+" 2>&1 \""
    logging.warning("\nCommand sed slurm_singularitys : \n"+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    state=client.get_OK()
    logging.warning("Out of sed slurm_singularity : "+ str(state))
    return state

JobID=-1
# Launch singularitys
def Run_singularitys():
    global JobID
    stateVM=True
    # Slurm config
    stateVM=stateVM and (sed_slurm("s&NUM=NUM_DOCKERS&NUM="+str(NUM_DOCKERS)+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&ntasks=NTASKS&ntasks="+SBATCH_NTASKS+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&SBATCH --time=TIME&SBATCH --time="+SBATCH_time+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&SBATCH --cpus-per-task=TASKS&SBATCH --cpus-per-task="+SBATCH_cpus_per_task+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&SBATCH --gres=gpu:GPUS&SBATCH --gres=gpu:"+SBATCH_gpus+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&NGPUS=GPUS&NGPUS="+SBATCH_gpus+"&") == 0)
    SBATCH_nodes=str(int((NUM_DOCKERS-1)/(int(SBATCH_gpus)*int(CONTAINERS_PER_GPU)))+1)
    logging.warning("Number of nodes asked :"+SBATCH_nodes)
    stateVM=stateVM and (sed_slurm("s&SBATCH --nodes=NODES&SBATCH --nodes="+SBATCH_nodes+"&") == 0)
    if (SBATCH_exclusive):
        STRING_EXCLUSIVE="s&##SBATCH --exclusive&#SBATCH --exclusive&"
        stateVM=stateVM and (sed_slurm(STRING_EXCLUSIVE) == 0)
    stateVM=stateVM and (sed_slurm("s&SBATCH --partition=PARTITION&SBATCH --partition="+SBATCH_partition+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&DATE=DATE&DATE="+DATE+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&DIR=/dockerspace&DIR="+SPACE_DIR+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&SINGULARITY_NAME=ubuntu18_icewm.sif&SINGULARITY_NAME="+SINGULARITY_NAME+"&") == 0)
    #stateVM=stateVM and (sed_slurm("s&FRONTENDIP=frontend:192.168.0.254&FRONTENDIP="+SSH_FRONTEND+":"+SSH_IP+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&TILEDVIZ_DIR=/TiledViz&TILEDVIZ_DIR="+TILEDVIZ_DIR+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&TILESINGULARITYS_path=/TiledViz/TVConnections/Singularity&TILESINGULARITYS_path="+TilesScriptsPath+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&TileSetP=55555&TileSetP=TileSetPort&") == 0)
    stateVM=stateVM and (sed_slurm("s&FRONTEND=192.168.0.1&FRONTEND="+UserFront+"@"+Frontend+"&") == 0)
    stateVM=stateVM and (sed_slurm("s&OPTIONS=OTHER_OPTIONS&OPTIONS="+OPTIONS+"&") == 0)

    COMMAND="bash -c \"sbatch "+os.path.join(JOBPath,"slurm_singularitys")+\
             " > "+os.path.join(JOBPath,"output_submit")+" 2>&1 \"" 
    logging.warning("\nCommand singularitys : "+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    state=client.get_OK()
    logging.warning("Out of launch singularity : "+ str(state))
    sys.stdout.flush()
    stateVM=stateVM and (state == 0)
    time.sleep(20)

    get_file_client(client,TileSet,JOBPath,"output_submit",".")
    try:
        with open("output_submit",'r') as fsubmit:
            JobID=fsubmit.read().replace("Submitted batch job ","").replace("\n","")
            print("Job ID : "+JobID)
            sys.stdout.flush()
    except:
        print("Cannot retreive Slurm job ID.")
        sys.stdout.flush()
        JobID="0"
        stateVM=False
        pass
    sys.stdout.flush()
    time.sleep(20)
    #code.interact(banner="Test squeue interactive :",local=dict(globals(), **locals()))

    notstarted=True
    COMMAND="bash -c \"squeue -j "+JobID+" > "+os.path.join(JOBPath,"output_squeue")+" 2>&1 \"" 
    logging.warning("\nCommand squeue : "+COMMAND)
    # time wait for scheduling
    twait=2
    # max time wait in seconds
    mwait=600
    # iter
    i=0
    while(notstarted):
        if (i>mwait/twait):
            logging.error("Scheduler never run after max time wait %d and %d iterations." % (mwait,i))
            sys.stdout.flush()
            return False
            
        client.send_server(LaunchTS+' '+COMMAND)
        state=client.get_OK()
        logging.warning("Out of launch squeue : "+ str(state))
        sys.stdout.flush()
        stateVM=stateVM and (state == 0)
        if (not stateVM):
            logging.error("Cannot retreive squeue output.")
            sys.stdout.flush()
            return False
        
        try:
            get_file_client(client,TileSet,JOBPath,"output_squeue",".")
            #JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
            squeuestr=r'(?P<jobid>\d+)\s+(?P<partition>\w+)\s+(?P<name>\w+)\s+(?P<user>\w+)\s+(?P<state>[A-Z]*)\s+(?P<time>\S+)\s+(?P<nodes>\d+)\s+(?P<nodelist>\S+)\s*'
            squeue_re = re.compile(r''+squeuestr)
            with open("output_squeue",'r') as fsqueue:
                alllines=fsqueue.readlines()
                if (len(alllines)>1):
                    lastline=alllines[-1]
                    ore_squeue=squeue_re.search(lastline)
                    print(str(ore_squeue.groups()))
                    State=ore_squeue.group("state")
                    logging.warning("State queue Running detected : "+State)
                    if (State == 'R'):
                        notstarted=False
            sys.stdout.flush()
            stateVM=stateVM and (state == 0)
        except:
            logging.error("Cannot retreive Slurm job status.")
            sys.stdout.flush()
            stateVM=False
            return False
            #COMMAND="bash -c --start \"squeue -j "+JobID+" > "+os.path.join(JOBPath,"output_squeue")+" 2>&1 \""
            #JOBID PARTITION     NAME     USER ST          START_TIME  NODES SCHEDNODES           NODELIST(REASON)
            #squeuestr=r'(?P<jobid>\d+)\s+(?P<partition>\w+)\s+(?P<name>\w+)\s+(?P<user>\w+)\s+(?P<state>[A-Z][A-Z])\s+(?P<startdate>\S+)\s+(?P<nodes>\d+)\s+(?P<schednodes>\S+)\s+(?P<nodelist>\S+)\s*'
            #StartDate=ore_squeue.group("startdate")
            #Remain=(datetime.datetime.strptime(StartDate, '%Y-%m-%dT%H:%M:%S')-datetime.datetime.now()).total_seconds()
            #print("Remain seconds :"+str(Remain))
            #            print("Cannot retreive Slurm job StartDate.")
        time.sleep(twait)
        os.system("rm ./output_squeue")
        i=i+1
    # Wait for start submission
    #time.sleep(Remain)

    logging.warning("Job is running : wait 10s for singularity launched.")
    time.sleep(10)

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


# Launch singularity tunnels
def launch_tunnel():
    global TilesScriptsPath
    logging.warning("Singularity TilesScriptsPath : %s" % (TilesScriptsPath))
    logging.warning("Frontend Home in anatomist_job: "+HomeFront)
    stateVM=True
    
    # Share ssh connection keys whith tiles
    # TODO : secure that action ?
    totbyte=0
    filesize=os.path.getsize(sshKeyPath)
    connectionkey=os.path.join(HomeFront,".ssh/id_rsa_connection")
    os.system("cp "+sshKeyPath+".pub "+os.path.join(Home,".ssh/authorized_keys"))
    packet_id_length=MSGsize-200
    with open(sshKeyPath,'rb') as privatek:
        l = '\\\"'+str(privatek.read(packet_id_length).replace(b"\n",b""),"utf-8")+'\\\"'
        COMMANDid=LaunchTS+' bash -c "echo '+l+' > '+connectionkey+'; chmod 600 '+connectionkey+'"'
        logging.warning("Send id_rsa with \"%s\"." % (COMMANDid) )
        client.send_server(COMMANDid)
        state=client.get_OK()
        stateVM=stateVM and (state == 0)
        while (l):
            totbyte=totbyte+packet_id_length
            rest=filesize-totbyte;
            if (rest > packet_id_length ):
                l = '\\\"'+str(privatek.read(packet_id_length).replace(b"\n",b""),"utf-8")+'\\\"'
                COMMANDid=LaunchTS+' bash -c "echo '+l+' >> '+connectionkey+'"'
                logging.warning("Send id_rsa with %s." % (COMMANDid) )
                client.send_server(COMMANDid)
                state=client.get_OK()
                stateVM=stateVM and (state == 0)
            else:
                if (rest > 0):
                    l = '\\\"'+str(privatek.read(rest).replace(b"\n",b""),"utf-8")+'\\\"'
                    COMMANDid=LaunchTS+' bash -c "echo '+l+' >> '+connectionkey+'"'
                    logging.warning("Send id_rsa with %s." % (COMMANDid) )
                    client.send_server(COMMANDid)
                    state=client.get_OK()
                    stateVM=stateVM and (state == 0)
                break
    logging.warning("Out of id_rsa : "+ str(stateVM))
    COMMANDid=LaunchTS+' bash -c "sed -e \\\"s&KEY-----&KEY-----\\\\n&\\\" -e \\\"s&-----END&\\\\n-----END&\\\" -i '+connectionkey+'"'
    logging.warning("Send id_rsa with %s." % (COMMANDid) )
    client.send_server(COMMANDid)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    with open(sshKeyPath+'.pub','rb') as publick:
        l = '\\\"'+str(publick.read().replace(b"\n",b""),"utf-8")+'\\\"'
        COMMANDid=LaunchTS+' bash -c "echo '+l+' > '+connectionkey+'.pub"'
        logging.warning("Send id_rsa.pub with %s." % (COMMANDid) )
        client.send_server(COMMANDid)
        state=client.get_OK()
        stateVM=stateVM and (state == 0)
    logging.warning("Out of id_rsa.pub : "+ str(stateVM))
    if (not stateVM):
        logging.error("!! Error send id_rsa.!!")
        return stateVM

    with open("listPortsTiles.pickle", 'rb') as file_pi:
        listPortsTilesIE=pickle.load(file_pi)
    # Call tunnel for VNC
    for i in range(NUM_DOCKERS):
        i0="%0.3d" % (i+1)
        TILEi=ExecuteTS+' Tiles=('+containerId(i+1)+') '
        internPort=listPortsTilesIE[str(i)][0]
        WebServerHost=listPortsTilesIE["TiledVizHost"]
        ServerTSPortSSH=listPortsTilesIE["TiledVizConnectionPort"]
        COMMANDi=' ssh-agent '+TilesScriptsPath+'/tunnel_ssh '+SSH_FRONTEND+' '+SSH_LOGIN+' '+str(internPort)+' '+WebServerHost+' '+str(ServerTSPortSSH)+' -i '+connectionkey
        #COMMANDi=' '+TilesScriptsPath+'/tunnel_ssh '+SSH_FRONTEND+' '+SSH_LOGIN+' '+str(internPort)+' '+WebServerHost+' '+str(ServerTSPortSSH)+' -i '+connectionkey
        logging.warning("%s | %s" % (TILEi, COMMANDi)) 
        client.send_server(TILEi+COMMANDi)
        state=client.get_OK()
        stateVM=(state == 0)
    if (not stateVM):
        print("!! Error launch_tunnel.!!")
        return stateVM
    sys.stdout.flush()
    
    # Update nodes.json locally
    JsonFile="nodes.json_init"
    logging.error("Before read  : "+ str(JsonFile))
    with open(JsonFile) as json_tiles_file:
        nodes_json=json.loads(json_tiles_file.read())
    for tilei in range(NUM_DOCKERS):
        nodeurl=nodes_json["nodes"][tilei]["url"]
        nodeurl=re.sub(r'https://[^/]*',r'https://'+listPortsTilesIE["TiledVizHost"],nodeurl)
        nodeurl=re.sub(r'host=[^&]*',r'host='+listPortsTilesIE["TiledVizHost"],nodeurl)
        oldport=int(re.sub(r'.*port=([^&]*)&.*',r'\1',nodeurl))
        tileip=oldport % 1000 - 1
        logging.warning("tile %d update nodes.json : new url %s with old port %d" % (tilei, nodeurl, oldport)) 
        if ( str(tileip) in listPortsTilesIE):
            extern=listPortsTilesIE[str(tileip)][1]
            nodes_json["nodes"][tilei]["url"]=re.sub(r'port=[^&]*',r'port='+str(extern),nodeurl)
            logging.warning("tile %d : new url %s" % (tilei,nodes_json["nodes"][tilei]["url"])) 
        sys.stdout.flush()
    logging.error("Before write nodes.json")
    with open("nodes.json",'w') as nodesf:
        nodesf.write(json.dumps(nodes_json))
    logging.warning("Out of tunnel_ssh : "+ str(stateVM))
    return stateVM

time.sleep(2)
# Launch singularity tools
if (stateVM):
    all_resize("1920x1080")

logging.warning("Before launch_tunnel.")

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
    COMMANDserver=os.path.join(JOBPath,'anatomist_server')+' '+\
                       CONTAINER_PYTHON+' '+\
                       os.path.join(JOBPath,CONTAINER_ANA_DISPATCHER)+' '+\
                       CONTAINER_ANA_LIB
    print("COMMAND server |%s|" % (COMMANDserver))
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+
                       COMMANDserver)
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
    global stateVM
    client.send_server(ExecuteTS+' Tiles=('+containerId(1)+') '+
                       'bash -c "'+os.path.join(TILESINGULARITYS_DIR,'get_ip.sh '+SSH_ENO)+
                       '; cp $HOME/.vnc/myip '+os.path.join(JOBPath,'serverip')+'"')
    #'scp .vnc/myip '+HTTP_LOGIN+'@'+HTTP_FRONTEND+':'+JOBPath+'"')
    OutIP=client.get_OK()
    print("Out of get ip : "+ str(OutIP))
    if (OutIP):
        stateVM=False
        sys.stdout.flush()
        return "1.1.1.1"
    
    get_file_client(client,TileSet,JOBPath,"serverip",".")
    # while( get_file_client(client,TileSet,JOBPath,"serverip",".") < 0):
    #     time.sleep(1)
    #     pass
    try:
        with open("serverip",'r') as fserverip:
            init_IP=fserverip.read().replace("\n","") #.replace(domain+'.',"").replace("\n","")
            print("Server ip : "+init_IP)
            sys.stdout.flush()
    except:
        print("Cannot retreive server ip.")        
        sys.stdout.flush()
        init_IP="1.1.1.1"
        stateVM=False
        pass
    sys.stdout.flush()
    return init_IP


try:
    if (stateVM):
        init_IP=Get_server_IP()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)

List_anatomist=range(2,NUM_ANA+1)
    

def Run_clients():
    # Split the list :
    splv=10
    # for i in range(int(NUM_ANA/splv+1)):
        # sublist=list(map(List_anatomist.__getitem__, range(i*splv,min((i+1)*splv,NumMaxClient))))
        # #print(str(sublist))
        # if (len(sublist) == 0):
        #     break
        # arglist=list(map(containerId, sublist))
        #print(str(arglist))

    for i in range(2,NUM_ANA+1):
        COMMANDclient=os.path.join(JOBPath,'anatomist_client')+' '+\
                      CONTAINER_PYTHON+' '+\
                      os.path.join(JOBPath,CONTAINER_ANA_DISPATCHER)+' '+\
                      CONTAINER_ANA_LIB+' '+init_IP
        print("Command %d of anatomist_client : %s " % (i,COMMANDclient))
        sys.stdout.flush()
        # client.send_server(ExecuteTS+' Tiles=('+containerId(i)+') '+COMMANDclient)
        client.send_server(ExecuteTS+' Tiles=('+containerId(i)+') bash -c "cd '+JOBPath+'; SINGULARITYID=%03d ' % (i)+COMMANDclient+'"')
        #client.send_server(ExecuteTS+' Tiles='+str(arglist)+' '+COMMANDclient)
        print("Out %d of anatomist_client : %s " % (i,str(client.get_OK())))
        sys.stdout.flush()
        
    if HAVE_ATLAS:
        COMMANDclient=os.path.join(JOBPath,'anatomist_client')+' '+\
                      CONTAINER_PYTHON+' '+\
                      os.path.join(JOBPath,CONTAINER_ANA_DISPATCHER)+' '+\
                      CONTAINER_ANA_LIB+' '+init_IP+' true'
        print("Command %d of anatomist_client : %s " % (NUM_ANA+1,COMMANDclient))
        sys.stdout.flush()
        client.send_server(ExecuteTS+' Tiles=('+containerId(NUM_ANA+1)+') '+COMMANDclient)
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
    COMMAND_DISPATCHER=os.path.join(JOBPath,'anatomist_dispatcher')+' '+str(NUM_ANA)+' '+\
                       CONTAINER_PYTHON+' '+\
                       os.path.join(JOBPath,CONTAINER_ANA_DISPATCHER)+' '+\
                       CONTAINER_ANA_LIB+' '+\
                       os.path.join(JOBPath,START_ANA_DISPATCH)+' '+\
                       os.path.join(JOBPath,CASE_DATA_CONFIG)+\
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
    global JobID
    # Send a file-signal for the slurm job to end sleeping and finished
    COMMAND="bash -c \"touch "+os.path.join(JOBPath,"end_slurm_singularitys")+"'\"" #+\
    logging.warning("\nCommand end slurm_singularitys : \n"+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    #state=client.get_OK()
    #logging.warning("Out of end slurm_singularity : "+ str(state))
    time.sleep(20)

    COMMANDStop="bash -c \"scancel "+str(JobID)+\
             " > "+os.path.join(JOBPath,"output_submit")+" 2>&1 \"" 
    logging.warning("\nCommand stop singularitys : "+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    #state=client.get_OK()
    #logging.warning("Out of stop singularity : "+ str(state))
    sys.stdout.flush()
    #stateVM=stateVM and (state == 0)

    # stateVM=True
    # client.send_server(ExecuteTS+' killall -9 Xvfb')
    # state=client.get_OK()
    # print("Out of killall xvfb command : "+ str(state))
    # client.send_server(LaunchTS+" "+COMMANDStop)
    # state=client.get_OK()
    # print("Out of COMMANDStop : "+ str(state))
    # stateVM=(state == 0)
    # time.sleep(2)
    Remove_TileSet()
    return stateVM
         

#isActions=True
launch_actions_and_interact()

try:
    print("isActions: "+str(isActions))
except:
    print("isActions not defined.")


# COMMAND="rm -rf $HOME/.vnc"
# client.send_server(ExecuteTS+COMMAND)
# client.get_OK()

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


