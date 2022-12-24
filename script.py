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
        

        self.file = None
        self.ssidreg = "KU-AP.*"

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


    def __call__(self):
        self.get_entry()

    def get_entry(self):
        try:
            while (True):
                t = int(time.time() * 1000.0)
                response = requests.get(self.jsonaddress)
                data= response.json()
                temp = dict()

                stationdata = self.node.run("iw dev wlp1s0 station dump | grep -E 'Station|signal'").stdout.splitlines()
                #stationdata holds the station data and the signal values

                rssi = int(stationdata[1][stationdata[1].index(':')+1:stationdata[1].index('[')].strip()) # Regex
                avgrssi = int(stationdata[2][stationdata[2].index(':')+1:stationdata[2].index('[')].strip()) # Regex

                # we take both signal and average signal values

                if (len(data['links'])!=0):

                    dictdata = dict()  
                    dictdata = {'Systemtime': str(data['systemTime']), 'ip':str(data['neighbors'][0]['ipAddress']), 'mprs':str(data['neighbors'][0]['multiPointRelaySelector']) \
                    , 'linkcost': str(data['links'][0]['linkCost']) ,'LinkQuality':str(data['links'][0]['linkQuality']), 'NQ': str(data['links'][0]['neighborLinkQuality']),'RSSI': rssi, 'AVGRSSI': avgrssi}
                    temp[str(data['neighbors'][0]['ipAddress'])] = dictdata
                    self.to_file_connected(temp, 1)

                else:
                    #means the node has been disconnected
                    self.to_file_connected(temp, 0)

                timedelta = int(time.time()*1000.0) - t 
                time.sleep(2-timedelta/1000.0)
                print(2-timedelta/1000.0)
        except KeyboardInterrupt:
            self.file.close()

    def to_file_connected(self,info,value):
        #if connection
        if (value == 1):
            if self.file is None:
                self.file = open(str(self.filename)+".csv", 'w')
                self.file.write(self.columns)
                self.file.close()
                self.file = open(str(self.filename)+".csv", 'a')


            dataToWrite = info['Systemtime']+','+ info['ip'] + ','  + info['mprs'] + ',' + info['linkcost'] + ',' + info['LinkQuality'] + ',' + info['NQ']  + ',' + str(info['RSSI']) + ','  + str(info['AVGRSSI'])  + ',' + str(value) + '\n'
            self.file.write(dataToWrite)
        #if no connection (disconnection or we havent started yet)
        else:
            #there is no link data/ the node just disconnected
            if self.file is not None:
                dataToWrite = info['Systemtime']+','+ str(0) + ','  + info['mprs'] + ',' + info['linkcost'] + ',' + info['LinkQuality'] + ',' + info['NQ']  + ',' + str(info['RSSI']) + ','  + str(info['AVGRSSI'])  + ',' + str(value) + '\n'
                self.file.write(dataToWrite)
                self.file.close()
                self.file = None
                self.filename += 1


if __name__=="__main__":
    datacollect = datacollector()
    datacollect()