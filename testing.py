from multiprocessing import Process, Manager
import time
class test():
    def __init__(self):
        self.data = 5

    def process1(self,data,k):
        try:
            while(True):
                data[k] += k
                print("Changed")
                time.sleep(2)
        except KeyboardInterrupt:
            print("stopping")

    def process2(self):
        
        processes = dict()
        k=0
        try:
            with Manager() as manager:
                data = manager.dict()
                while(True):
                    if k%3 == 0:
                        data[k] = 0
                        processes[k] = Process(target = self.process1, args=(data,k,))
                        processes[k].start()
                        
                    print(data)
                    time.sleep(1)
                    k+=1
        except KeyboardInterrupt:
            print("stopping")
            #processes[k].join()

    def __call__(self):
        self.process2()


if __name__=="__main__":
    testing = test()
    testing()