import requests
import json
import time

#open the file for writing with columns name initialized
file = open("data.csv", 'w')
columns = 'systemTime,' + 'ipAddress,'+ 'clusterHeadSelector,' + 'multiPointRelaySelector,' +'linkCost,' + 'linkQuality,' + 'neighborLinkQuality,\n'
file.write(columns)
file.close()

def get_entry():
    response = requests.get('http://192.168.10.1:9090/all')
    print(response)
    data= response.json()

    #Open file to append new data
    file = open("data.csv", 'a')    
    for i in range(len(data['neighbors'])):
        dataToWrite = str(data['systemTime']) + ',' +str(data['neighbors'][i]['ipAddress']) + ','+ str(data['neighbors'][i]['clusterHeadSelector']) + ','+ str(data['neighbors'][i]['multiPointRelaySelector']) \
        + ',' + str(data['links'][i]['linkCost']) + ',' + str(data['links'][i]['linkQuality'])+ ',' + str(data['links'][i]['neighborLinkQuality']) + '\n'
        file.write(dataToWrite)

    file.close()

for i in range(1,5):
    get_entry()
    time.sleep(2)