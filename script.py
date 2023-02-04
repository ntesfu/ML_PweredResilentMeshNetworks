import requests
import time
import subprocess
from fabric import Connection # Change try paramiko
import os
import re
import platform
from datetime import date
from multiprocessing import Process, Manager


lossreg = "unreachable"
lossreg2 = "100% loss"
lossreg3 = "Request timed out."



class datacollector():

    def __init__(self):
        self.scenario = input("Enter the scenario:")
        answer = 'n'
        while answer!='y':
            if (os.path.isdir(self.scenario)):
                answer = input(f"The folder {self.scenario} exists do you want to continue writing to it (y,n)?")
                if answer == 'n': self.scenario = input("Enter the scenario:")
            else:
                os.mkdir(self.scenario)
                break

        self.osystem = platform.system()
        self.filename = 0
        #folder for each session
        while(os.path.isfile(os.path.join(self.scenario,str(self.filename))+".csv")):
            self.filename += 1
        
        self.columns = 'systemTime,' + 'ipAddress,'+  'multiPointRelaySelector,' +'linkCost,' + 'linkQuality,' + 'neighborLinkQuality,' + 'RSSI value,' + 'AVG RSSI value,'+ 'Connected,\n'
        

        self.file = dict()
        self.ssidreg = "KU-AP.*"
        
        self.links = dict()


#get the connected node ip
        if self.osystem == 'Windows':
            wirelessdata = subprocess.getoutput("netsh wlan show interfaces")
        else:
           wirelessdata = subprocess.getoutput("iw dev")

        ip = re.search(self.ssidreg,wirelessdata).group()
        ip = ip[5::].strip()

        self.rootaddress = "root@10." + ip
        self.node = Connection(host=self.rootaddress, connect_kwargs={"password":"root"})
        #wsl
        self.jsonaddress = 'http://192.168.10.1:9090/all'

        self.macentry = dict()
        self.macentry['10.79.141.204'] = '00:30:1a:4f:8d:cc'
        self.macentry['10.79.141.55'] = '00:30:1a:4f:8d:37'
        self.macentry['10.79.141.35'] = '00:30:1a:4f:8d:23'
        self.macentry['10.79.141.25'] = '00:30:1a:4f:8d:19'
        self.macentry['10.79.141.53'] = '00:30:1a:4f:8d:35'
        self.macentry['10.79.141.23'] = '00:30:1a:4f:8d:17'
        self.macentry['10.79.141.18'] = '00:30:1a:4f:8d:12'
        self.macentry['10.79.141.56'] = '00:30:1a:4f:8d:38'
        



    def __call__(self):
        self.get_entry()
            

    def get_entry(self):
        with Manager() as manager:
            Connected_links = manager.dict()
            pinging_processes = dict()
            string_ip = manager.list()
            try:
                while (True):
                    for i in self.links:
                        self.links[i] = 0
                    t = int(time.time() * 1000.0)
                    try:
                        response = requests.get(self.jsonaddress, timeout=2)
                        response.raise_for_status()
                    
                        if response.status_code != 200:
                            continue
                        data= response.json()
                        temp = dict()
                        stationdata = []
                        stationdata = self.node.run("iw dev wlp1s0 station dump | grep -E 'Station|signal'").stdout.splitlines()
                        #stationdata holds the station data and the signal values
                        rssi = dict()
                        avgrssi = dict()

                        for i in range(0,len(stationdata),3):
                            #get the mac address
                            mac = stationdata[i][stationdata[i].index('n')+1:stationdata[i].index('(')].strip()


                            rssi[mac] = int(stationdata[i+1][stationdata[i+1].index(':')+1:stationdata[i+1].index('[')].strip()) # Regex
                            avgrssi[mac] = int(stationdata[i+2][stationdata[i+2].index(':')+1:stationdata[i+2].index('[')].strip()) # Regex

                        # we take both signal and average signal values

                        if (data is not None and len(data['links'])!=0):
                            

                            for i in data['links']:
                                if i['remoteIP'] not in Connected_links.keys():
                                    string_ip.append(str(i['remoteIP']))
                                    Connected_links[i['remoteIP']] = 1
                                    #test = string_ip.pop()
                                    #process = Process(target = pingnodes, args=(Connected_links,))
                                    #process.start()
                                    #process.join()
                                    pinging_processes[str(i['remoteIP'])] = Process(target = pingnodes, args=(Connected_links,str(i['remoteIP']),))
                                    pinging_processes[str(i['remoteIP'])].start()


                                elif Connected_links[i['remoteIP']] == -1:
                                    Connected_links[i['remoteIP']] = 1
                                    #making a process for each ip
                                print(i['remoteIP'])
                                
                                dictdata = dict()  
                                if (self.macentry[str(i['remoteIP'])] in rssi.keys()):
                                    dictdata = {'Systemtime': str(data['systemTime']), 'ip':str(i['remoteIP']), 'mprs':str(data['neighbors'][0]['multiPointRelaySelector']) \
                                    , 'linkcost': str(i['linkCost']) ,'LinkQuality':str(i['linkQuality']), 'NQ': str(i['neighborLinkQuality']),\
                                        'RSSI': rssi[self.macentry[str(i['remoteIP'])]], 'AVGRSSI': avgrssi[self.macentry[str(i['remoteIP'])]]}
                                
                                else:
                                    dictdata = {'Systemtime': str(data['systemTime']), 'ip':str(i['remoteIP']), 'mprs':str(data['neighbors'][0]['multiPointRelaySelector']) \
                                    , 'linkcost': str(i['linkCost']) ,'LinkQuality':str(i['linkQuality']), 'NQ': str(i['neighborLinkQuality']),'RSSI': None, 'AVGRSSI': None}
                                

                                temp[str(i['remoteIP'])] = dictdata
                                print(f"Writing {Connected_links[i['remoteIP']]} to ip {i['remoteIP']}")
                                self.to_file_connected(temp, Connected_links[i['remoteIP']],str(i['remoteIP']))
                                self.links[str(i['remoteIP'])] = 1


                            links = [i for i in self.links.keys()]

                            for i in links:
                                if self.links[i] == 0:
                                    self.file[i].close()
                                    self.links.pop(i)
                                    Connected_links[i] = -1#
                                    self.file.pop(i)


                        else:
                            #just close the files
                            #means all the nodes have been disconnected
                            # links = [i for i in self.file.keys()]
                            for i in self.file:
                                self.file[i].close()
                            # for i in links:
                            #     self.to_file_connected(None, 0,str(i))

                        
                    

                        
                    
                    except Exception as e:
                        print(e.args)
                        continue
                    timedelta = int(time.time()*1000.0) - t 
                    if timedelta/1000.0<2:
                        print(f"took {timedelta/1000.0} seconds to complete the request")
                        time.sleep(2-timedelta/1000.0)
                    
            except KeyboardInterrupt:
                for i in self.file:
                    self.file[i].close()
                for i in pinging_processes.values():
                    i.join()



        for i in pinging_processes.values():
            i.join()

    def to_file_connected(self,info,value,ip):
        #if connection
        if ip not in self.file:
            self.file[ip] = open(os.path.join(self.scenario,str(self.filename))+".csv", 'w')
            self.file[ip].write(self.columns)
            self.file[ip].close()
            self.file[ip] = open(os.path.join(self.scenario,str(self.filename))+".csv", 'a')
            self.filename +=1



        
        dataToWrite = info[ip]['Systemtime']+','+ info[ip]['ip'] + ','  + info[ip]['mprs'] + ',' + info[ip]['linkcost'] + ',' + info[ip]['LinkQuality'] + ',' + info[ip]['NQ']  + ',' + str(info[ip]['RSSI']) + ','  + str(info[ip]['AVGRSSI'])  + ',' + str(value) + '\n'
        self.file[ip].write(dataToWrite)

def pingnodes(Connected_links,string_ip):
    try:
        
        ip = string_ip
        while(True):
            command = f"ping {ip} -w 1000 -n 6"
            print(f"Pinging {ip}")
            output = subprocess.getoutput(command)
            checkout2 = re.search(lossreg2,output)
            checkout = re.search(lossreg,output)
            checkout3 = re.search(lossreg3,output)
            if checkout is not None or checkout2 is not None or checkout3 is not None:
                print(f"{ip} has been disconnected")
                Connected_links[str(ip)] = 0
            elif checkout is None and checkout2 is None and checkout3 is None:
                Connected_links[str(ip)] = 1
    except KeyboardInterrupt:
        print("+++++++++++++++++=========Stopping pinging devices=========+++++++++++++++")


            


if __name__=="__main__":
    datacollect = datacollector()
    datacollect()