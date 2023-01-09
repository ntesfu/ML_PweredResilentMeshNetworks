import requests
import time
import subprocess
from fabric import Connection # Change try paramiko
import os
import re
import platform


#open the file for writing with columns name initialized



class datacollector():
    def __init__(self):
        self.osystem = platform.system()
        self.filename = 0
        #folder for each session
        while(os.path.isfile(str(self.filename)+".csv")):
            self.filename += 1
        
        self.columns = 'systemTime,' + 'ipAddress,'+  'multiPointRelaySelector,' +'linkCost,' + 'linkQuality,' + 'neighborLinkQuality,' + 'RSSI value,' + 'AVG RSSI value,'+ 'Connected,\n'
        

        self.file = dict()
        self.ssidreg = "KU-AP.*"

#get the connected node ip
        if self.osystem == 'Windows':
            wirelessdata = subprocess.getoutput("netsh wlan show interfaces")
        else:
           wirelessdata = subprocess.getoutput("iw dev")

        ip = re.search(self.ssidreg,wirelessdata).group()
        ip = ip[5::].strip()
        self.links = dict()

        self.rootaddress = "root@10." + ip
        self.node = Connection(host=self.rootaddress, connect_kwargs={"password":"root"})
        #wsl
        self.jsonaddress = 'http://192.168.10.1:9090/all'

        self.macentry = dict()
        self.macentry['10.79.141.204'] = '00:30:1a:4f:8d:cc'
        self.macentry['10.79.141.55'] = '00:30:1a:4f:8d:37'
        self.macentry['10.79.141.35'] = '00:30:1a:4f:8d:23'
        



    def __call__(self):
        self.get_entry()

    def get_entry(self):
        try:
            while (True):
                for i in self.links:
                    self.links[i] = 0
                t = int(time.time() * 1000.0)
                response = requests.get(self.jsonaddress)
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
                    print(mac)


                    rssi[mac] = int(stationdata[i+1][stationdata[i+1].index(':')+1:stationdata[i+1].index('[')].strip()) # Regex
                    avgrssi[mac] = int(stationdata[i+2][stationdata[i+2].index(':')+1:stationdata[i+2].index('[')].strip()) # Regex

                # we take both signal and average signal values

                if (len(data['links'])!=0):
                    for i in data['links']:
                        print(i['remoteIP'])
                        
                        dictdata = dict()  
                        dictdata = {'Systemtime': str(data['systemTime']), 'ip':str(i['remoteIP']), 'mprs':str(data['neighbors'][0]['multiPointRelaySelector']) \
                        , 'linkcost': str(i['linkCost']) ,'LinkQuality':str(i['linkQuality']), 'NQ': str(i['neighborLinkQuality']),'RSSI': rssi[self.macentry[str(i['remoteIP'])]], 'AVGRSSI': avgrssi[self.macentry[str(i['remoteIP'])]]}
                        temp[str(i['remoteIP'])] = dictdata
                        self.to_file_connected(temp, 1,str(i['remoteIP']))
                        self.links[str(i['remoteIP'])] = 1


                    links = [i for i in self.links.keys()]

                    for i in links:
                        if self.links[i] ==0:
                            self.to_file_connected(None, 0,str(i))
                            self.links.pop(i)


                else:
                    #just close the files
                    #means all the nodes have been disconnected
                    #self.to_file_connected(temp, 0)
                    links = [i for i in self.file.keys()]
                    for i in links:
                        self.to_file_connected(None, 0,str(i))

                timedelta = int(time.time()*1000.0) - t 
                time.sleep(2-timedelta/1000.0)
                print(2-timedelta/1000.0)
        except KeyboardInterrupt:
            for i in self.file:
                self.file[i].close()

    def to_file_connected(self,info,value,ip):
        #if connection
        if (value == 1):
            if ip not in self.file:
                print("opening a file!!!!")
                self.file[ip] = open(str(self.filename)+".csv", 'w')
                self.file[ip].write(self.columns)
                self.file[ip].close()
                self.file[ip] = open(str(self.filename)+".csv", 'a')
                self.filename +=1

            
            dataToWrite = info[ip]['Systemtime']+','+ info[ip]['ip'] + ','  + info[ip]['mprs'] + ',' + info[ip]['linkcost'] + ',' + info[ip]['LinkQuality'] + ',' + info[ip]['NQ']  + ',' + str(info[ip]['RSSI']) + ','  + str(info[ip]['AVGRSSI'])  + ',' + str(value) + '\n'
            self.file[ip].write(dataToWrite)
        #if no connection (disconnection or we havent started yet)
        else:
            #there is no link data/ the node just disconnected
            dataToWrite = str(value)+','+ str(value) + ','  + str(value) + ',' + str(value) + ',' + str(value) + ',' + str(value)  + ',' + str(value) + ','  + str(value)  + ',' + str(value) + '\n'
            self.file[ip].write(dataToWrite)
            self.file[ip].close()
            self.file.pop(ip)
            '''
            if self.file is not None:
                dataToWrite = info['Systemtime']+','+ str(0) + ','  + info['mprs'] + ',' + info['linkcost'] + ',' + info['LinkQuality'] + ',' + info['NQ']  + ',' + str(info['RSSI']) + ','  + str(info['AVGRSSI'])  + ',' + str(value) + '\n'
                self.file.write(dataToWrite)
                self.file.close()
                self.file = None
                self.filename += 1
                '''


if __name__=="__main__":
    datacollect = datacollector()
    datacollect()