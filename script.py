import requests
import json
import time

#open the file for writing with columns name initialized
file = open("data.csv", 'w')
columns = 'systemTime,' + 'ipAddress,'+ 'clusterHeadSelector,' + 'multiPointRelaySelector,' +'linkCost,' + 'linkQuality,' + 'neighborLinkQuality,' + 'Connected,\n'
file.write(columns)
file.close()


def get_entry():
    
    #Open file to append new data
    file = open("data.csv", 'a')

    
    prev = dict()
    
    for i in range(50): #the number of data we need to collect
        response = requests.get('http://192.168.10.1:9090/all')
        data= response.json()
        temp = dict()
        for i in range(len(data['neighbors'])): #goes through every neighbor
            #collect it to temp
            dictdata = dict()  
            dictdata = {'Systemtime': str(data['systemTime']), 'ip':str(data['neighbors'][i]['ipAddress']), "Is_cluster": str(data['neighbors'][i]['clusterHeadSelector']) , 'mprs':str(data['neighbors'][i]['multiPointRelaySelector']) \
            , 'linkcost': str(data['links'][i]['linkCost']) ,'LinkQuality':str(data['links'][i]['linkQuality']), 'NQ': str(data['links'][i]['neighborLinkQuality'])}
            
            temp[str(data['neighbors'][i]['ipAddress'])] = dictdata 

            #we check
            
            
            
        #we check
        if prev == {}:
            prev = temp
            print("Empty")
            print(dictdata['Systemtime'])
        
        
        else:
            k=list(prev.keys())
            for i in k:
                if i in temp.keys():
                    #write the entry to file with att=1
                    to_file_connected(prev[i], file,1)

                    #update whats on the prev and remove it from temp
                    prev[i] = temp.pop(i)


                else:
                    #write to file with att=0
                    to_file_connected(prev[i],file,0)
                    #pop from prev
                    prev.pop(i)



            if len(temp) != 0 : #new node connected
                for i in temp.keys():
                    prev[i]=temp[i]
            
            temp = dict()
        time.sleep(2)

    file.close()

def to_file_connected(info, file, value):
    #open file
    dataToWrite = info['Systemtime']+','+ info['ip'] + ',' + info["Is_cluster"] + ',' + info['mprs'] + ',' + info['linkcost'] + ',' + info['LinkQuality'] + ',' + info['NQ']  + ',' + str(value) + '\n'
    file.write(dataToWrite)




print("Test 1")

get_entry()