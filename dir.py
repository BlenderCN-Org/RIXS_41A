import os
from os import path

'''
@ Class Dir manages directorys while using BlueMagpie for data-saving/logging/macro.
  when Dir module is called, it automatically generates a saving structure as below.

@ Default data-saving structure
===============================================================
(top) username -- data  -- img 
               -- macro
               -- log
               -- **new_folder1 -- img  (by mkdir "new_folder1", 
                                         which has a default img folder inside)
===============================================================

@ dir(): provides path needed in BlueMagpie saving/logging functions.

@ mkdir(): make a new folder.

'''
class Dir():
    def __init__(self, username='user'):
        super().__init__()
        self.root_dir = os.getcwd() # where the TPS_BlueMagpie.py is located
        self.dir_name = username
        self.file_no = 0
        self.dict = {}          # prepare empty dictionary
        self.__dirs__()         # setup default dirs including data/img/macro/log

    def __dirs__(self):
        self.project_dir = self.root_dir + os.sep + self.dir_name + os.sep
        self.macro_dir = self.project_dir + 'macro' + os.sep
        self.log_dir = self.project_dir +'log' + os.sep
        self.data_dir = self.project_dir + 'data' + os.sep
        self.img_dir = self.data_dir + 'img' + os.sep
        self.saving_dir = self.data_dir     

        if not path.exists(self.dir_name):
            os.mkdir(self.dir_name)
            os.makedirs(self.macro_dir)
            os.makedirs(self.log_dir)
            os.makedirs(self.data_dir)
            os.makedirs(self.img_dir)

        d = {'log':self.log_dir, 
             'macro':self.macro_dir, 
             'img':self.img_dir,
             'data':self.data_dir}
        self.dict.update(d)

    def path(self, dirname):       # return path
        return self.dict[dirname]
        
    def mkdir(self, dirname):      # mkdir based on current saving_dir
        dirpath = self.saving_dir + dirname
        if not path.isdir(dirpath):
            os.makedirs(dirpath)
            self.saving_dir = dirpath + os.sep
            self.dict[dirname] = dirpath
        else:
            print('{} already exist'.format(dirname))

    def check(self, dirname):     # check path exist
        if dirname in self.dict:
            return True
        else:
            return False
    
    def data(self):
        return self.saving_dir
# test code for running dir.py independetly

#if __name__ == '__main__':
#    test = Dir('test2') #activate
#    if test.path('macro')[0]:
#        print(test.dir('macro')[1])
#    if test.path('happy')[0]:
#        print(test.dir('happy'))
#    else:
#        print('no happy found')
#    test.mkdir('happy')
#    if test.path('happy')[0]:
#        print(test.dir('happy'))
#    else:
#        print('no happy found')
#    test.mkdir('happy')




