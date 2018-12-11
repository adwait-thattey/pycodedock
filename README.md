# pycodedock

[![PyPI version](https://badge.fury.io/py/pycodedock.svg)](https://badge.fury.io/py/pycodedock)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[![Python Version](https://img.shields.io/badge/python-v3.6-green.svg)](https://docs.python.org/3.6/)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[![Docker Version](https://img.shields.io/badge/docker-v18.09-blue.svg)](https://github.com/docker/docker-ce/tree/18.09)

---
**_pycodedock is module that allows you to safely execute untrusted python scripts within docker containers._**  

Underneath it makes use of the docker API.  
Once the scripts have been loaded into the container, no connection whatsoever is maintained with the host machine. This prevents the script inside from interacting with the host system **even if it has administrator privileges** inside the container.

This module works well with multiple parallel threads(in fact it was designed for that purpose). But you should **ensure that all the instances get a unique id** (see usage below).  

The module also allows you to limit the memory or the percentage of CPU that you want to allocate to the script. (See the custom settings part below). **However note that if your kernel does not support swap limit capabilities, the script wont be able to 'swap' itself if it runs out of memory and will directly terminate**

Also take a look at the warnings section at the end before using the module
### Quickstart

#### Step 1:
Firstly make sure you have docker installed and the current user has the necessary privileges to create and destroy containers. Look here for more info:  
[How to install docker](https://duckduckgo.com)  
[Docker Tutorials]()   
[Manage docker as a non root user](https://docs.docker.com/install/linux/linux-postinstall/)   

#### Step 2:
You will need a docker image with python support. You can directly pull the pybuntu image  
`$docker pull pybuntu`  
Or if you prefer, create your own image from dockerfile but make sure it has python installed in it

#### Step 3:
Install pycodedock:    

`$pip install pycodedock`

> Now you can use the following commands to import pydock and get path to script and input file   

```
    >>>from pydock import dock
    >>>script = "<absolute path to the .py python script you want to execute>"
    >>>script_input = "<absolute path to the .txt file containing the input to the script (if required)"
```
>The module simply redirects the contents of the input file to STDIN while executing the code

```
    >>> D = dock.Docker(unique_code,code_file,input_file,time_limit,custom_settings)
```
#### Parameters:
`unique_code`: `string` A string identifying the container. If you are running multiple containers parallely, **make sure all of them have a different unique_code**  

`code_file` : `string` Absolute path to the file containg script. (variable 'script' in this case)  

`input_file`: `string` Absolute path to the file containing the input that will be redirected to STDIN when executing the script  

`time_limit`: `float` The time limit in seconds after which the script will be terminated. (defaults to 1000).  The module makes use of bash timeout command for this. timeout first sends `SIGTERM` to the process, then escalates to `SIGKILL` a few milliseconds later if the process fails to stop.  

`custom_settings`: `dict` : Each container has a set of default settings. You can override those by passing values in this param. Look below in the custom settings section for more details

**Now that you have a docker instance, the next step will be to actually run it**

#### Step 4 :
Note that at this time, container is not running. The following command start the container and execute the code  

` >>> status = D.run()`

This may take time to execute depending on your system and the script  
Once the execution is complete, you can inspect the status. It can mainly have 3 values  
0 - Successful execution  
-1 - Error  
124 - Timeout  
The output and error files are copied to the dir  
 
`>>> D.output_file`  
gives the path of the output file  

`>>> D.error_file`
gives the path to error file in which error dump is written  
Now you can perform normal file ops to get the output/error  

#### Step 5

Once everything is done, it is important to destroy the container and delete residue files  
`>>> D.destroy()`    
This will stop the container and delete all files **including the input and output file**. So make sure you process them or copy them before calling destroy  

### Effects of SIGTERM and SIGKILL  

The module is designed to handle SIGTERM (Cntrl+C) (kill). So if you want to stop the execution of `D.run()` mid-way, you can press Cntrl+C or use the kill command. The module will stop the container , delete all residue files and then exit.    

**However SIGKILL (kill -9) , EOF/SIGSTOP (Cntrl+D) can not be handled. If you press (Cntrl+D or give a kill -9) the module will terminate without getting a chance to clean. If the container is running, it WILL NOT BE STOPPED and residue files WILL NOT BE DELETED**   

To repair this you need to manually stop the containers using `docker stop` and delete the residue folder/files from the directory (_home by default but can be changed in custom settings_). The residue files are in a folder with the `unique_name` that you provided while creating instance.

**_Failing to do the above step may cause an error when you try to run a script in docker next time_**

#### Specifying Custom Settings

Through the `custom_settings` parameter you can overwrite the default settings.  
`custom_settings` is a dictionary that has the following values  

|            Key           	|                                                                                                                                                                                    Description                                                                                                                                                                                    	|                       Default Value                      	|
|:------------------------:	|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:	|:--------------------------------------------------------:	|
|       "DOCKER_ROOT"      	| The Place where temp files are stored during execution. These are the `residue files`  that have been described above. A folder is made with the unique_code as the name.  All files reside inside it during execution. If you wish to modify this , give absolute path to the place where you would like the files to be stored.  Format : "string"                              	| Home Directory                                           	|
|    "DOCKER_MEM_LIMIT"    	| The max amount of memory that the script is allowed to use.  Format : "<number><unit>"  number can be any integer. unit can be any one of the following {"b","k","m","g"} which represents  "bytes","kilobytes", "mega-bytes", "giga-bytes"  Ex : "100m" means limit to 100 MBs, "20000k" means limit to 20000 KBs  Read the warning section about swaps before assigning a limit 	| "1g" Container is allowed to  consume upto 1GB of memory 	|
| "DOCKER_CPU_QUOTA_LIMIT" 	| The limit on the percentage of CPU that the container is allowed to consume.  Format: integer : <percentage>*1000  Example: 5000 denotes 5% of CPU, 13460 would indicate 13.46% of CPU                                                                                                                                                                                            	| 90000 Upto 90% of the CPU can be  used by the container  	|
|    "DOCKER_IMAGE_NAME"   	| The image that is used to build the container. If you specify a custom image , make sure it has python installed  Format: "string"                                                                                                                                                                                                                                                	| "pybuntu"                                                	|  


Example : 
```
    custom_settings = {
        "DOCKER_ROOT": os.path.expanduser("~/some_dir"),
        "DOCKER_MEM_LIMIT": "200m",
        "DOCKER_CPU_QUOTA_LIMIT": "20000",
        "DOCKER_IMAGE_NAME": "pybuntu",
    }
```

### Warnings
1. **If you use a custom container image, ensure it has python installed**
2. **Do not forget to call docker.destroy() in your code after calling docker.run(). If you don't, the container will not stop and residue files will not be cleaned. You will have to do it manually**
3. **Do not terminate the running code with SIGKILL. Instead send SIGTERM and wait for code to end by itself.**
3. **If you kill docker.run() anyway, make sure to perform manual cleanup by stopping the container and removing residue files**
4. **If the code misbehaves or terminates due to any reasons, make sure that cleanup has been properly completed**

**_Lastly, this module is still under alpha stages of development. If you find any bug or vulnerability, please take a few minutes to report it on issues Page_**

