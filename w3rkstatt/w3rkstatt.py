#!/usr/bin/env python3
#Filename: w3rkstatt.py

"""
(c) 2020 Volker Scheithauer
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice (including the next paragraph) shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

https://opensource.org/licenses/GPL-3.0
# SPDX-License-Identifier: GPL-3.0-or-later
For information on SDPX, https://spdx.org/licenses/GPL-3.0-or-later.html

Werkstatt Python Core Tools 
Provide core functions for Werkstatt related python scripts

Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20210513      Volker Scheithauer    Tranfer Development from other projects
20210513      Volker Scheithauer    Add Password Encryption

"""



import logging
import os, json, socket, platform, errno, shutil, uuid, re
import time, datetime
import pandas as pd
import urllib
import json
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
from os.path import expanduser



from io import StringIO
from pathlib import Path
from urllib.parse import urlparse


try:
    # Cryptodome
    pass
    from base64 import b64encode, b64decode
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad, unpad
    from Cryptodome.Random import get_random_bytes
except:
    # Crypto ?
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Random import get_random_bytes

_modVer = "2.0"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = False
_SecureDebug = False

# Global functions
def getCurrentFolder():
    '''
    Get the current folder 

    :return: the current path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A
    '''
    path=str(os.path.dirname(os.path.abspath(__file__)))
    return path

def getParentFolder(folder):
    '''
    Get the parent folder of given path

    :param str folder: a given path
    :return: the parent path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''    
    parentFolder = str(Path(folder).parent)
    return parentFolder

def getFiles(path,pattern):
    '''
    Get the all files in a given folder matching search pattern

    :param str path: a given path
    :param str pattern: a given search pattern
    :return: files
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    files = []
    with os.scandir(path) as listOfEntries:  
        for entry in listOfEntries:
            if entry.is_file():                
                if entry.name.endswith(pattern):
                    if _localDebug:
                        logger.debug('Core: File Name: %s', entry.name)                   
                    file = os.path.join(path, entry.name)
                    files.append(file)                                               
    return files 

def concatPath(path,folder):
    '''
    Concateneate path and folder

    :param str path: a given path
    :param str folder: a given folder name
    :return: path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    value = str(os.path.join(path, folder))
    return value

def getFileStatus(path):   
    '''
    Check if file exists

    :param str path: a given file name, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    return os.path.isfile(path)

def getFolderStatus(path):   
    '''
    Check if folder exists

    :param str path: a given folder, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    return os.path.exists(path)

def createFolder(path):
    '''
    Create folder, if it does not exist

    :param str path: a given folder, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: OSError
    :raises TypeError: N/A    
    '''       
    sFolderStatus = getFolderStatus(path)
    if not sFolderStatus:
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

def getFileName(path):
    '''
    Get file name from fully qualified file path

    :param str path: a given file, fully qualified
    :return: file name
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    fileName = str(os.path.basename(path))
    return fileName

def getFileJson(file):
    '''
    Read json file content

    :param str file: a given json formatted file, fully qualified
    :return: file name
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    with open(file) as f:
        data = json.load(f)
    return data    

def getFilePathLocal(file):
    '''
    Get parent folder of file, fully qualified

    :param str file: a given file name, fully qualified
    :return: parent folder
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''        
    return os.path.join(getCurrentFolder(),file)

def getFileDate(path):
    '''
    Get file date, fully qualified

    :param str path: a given file name, fully qualified
    :return: file date
    :rtype: datetime
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    try:
        fTime = os.path.getmtime(path)
    except OSError:
        fTime = 0
    fileTime = datetime.datetime.fromtimestamp(fTime)
    return fileTime    

def getEpoch(timeVal,timeFormat):
    '''
    Get epoch from provided time 

    :param datetime timeVal: time
    :param str timeFormat: time format
    :return: epoch
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    epoch = int(time.mktime(time.strptime(timeVal, timeFormat)))
    return epoch

def getTime():
    '''
    Get time  

    :return: epoch
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''   
    ts = datetime.datetime.now().timestamp()
    return ts

def getCurrentDate(timeFormat=""):
    '''
    Get current date  

    :param str timeFormat: time format
    :return: string
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    if len(timeFormat) < 1:
        tf = _timeFormat
    else:
        tf = timeFormat

    ts = datetime.datetime.now()
    dt = ts.strftime(tf)
    return dt

def addTimeDelta(date,delta,timeFormat=""):
    '''
    Add delta to given date  

    :param str dt: date string
    :param str delta: time delta int
    :param str timeFormat: time format
    :return: string
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    ''' 

    if len(timeFormat) < 1:
        tf = _timeFormat
    else:
        tf = timeFormat
    #  '%Y-%m-%dT%H:%M:%S'
    epoch = getEpoch(timeVal=date,timeFormat=timeFormat)
    dtDY  = int(time.strftime('%Y', time.localtime(epoch)))
    dtDM  = int(time.strftime('%m', time.localtime(epoch)))
    dtDD  = int(time.strftime('%d', time.localtime(epoch)))
    dtTH  = int(time.strftime('%H', time.localtime(epoch)))
    dtTM  = int(time.strftime('%M', time.localtime(epoch)))
    dtTS  = int(time.strftime('%S', time.localtime(epoch)))    
    dltDt = datetime.datetime(dtDY,dtDM,dtDD,dtTH,dtTM,dtTS) + datetime.timedelta(days=delta)
    value = dltDt.strftime(tf)

    return value

def jsonValidator(data):
    '''
    Check if content is valid json

    :param str data: json content
    :return: status
    :rtype: boolean
    :raises ValueError: see log file
    :raises TypeError: N/A    
    '''       
    try:
        json.loads(data)
        return True
    except ValueError as error:
        logger.error('Script: Invalid json: %s', error)
        return False    

def readFile(file):
    '''
    Read file content

    :param str file: a given file name, fully qualified
    :return: content
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''         
    lines = []
    i = 0
    with open(file, encoding='windows-1252') as fp:
            line = fp.readline()    
            while line:
                i +=1
                lines.append(line)
                line = fp.readline()
    fp.close
    return lines

def readHtmlFile(file):
    '''
    Read file content

    :param str file: a given file name, fully qualified
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''         
    lines = ""
    i = 0
    # with open(file, encoding='windows-1252') as fp:
    #         lines = fp.readlines()    
    # fp.close

    with open(file, 'r', encoding='UTF-8') as file:
        lines = file.read().replace('\n', '')    

    return lines    

def writeJsonFile(file,content):
    '''
    Write file content

    :param str file: a given file name, fully qualified
    :param str content: file content
    :return: status
    :rtype: boolean
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''   
    status = True
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
    except ValueError as error:
        status = False
        logger.error('Script: Invalid json: %s', error)
   
    
    return status
    
def getJsonValue(path,data):
    '''
    Extract data from json content using jsonPath

    :param str path: jsonPath expression
    :param dict data: json content
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    jpexp = parse(path)
    match = jpexp.find(data)
    try:
        value = match[0].value
    except:
        value = ""
    
    return value

def jsonTranslateValues(data):
    '''
    Replace predefined str in json content

    :param str data: jsonPath expression
    :return: content
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    # data = str(data)

    if jsonValidator(data=data):

        jData = json.loads(data)
        if isinstance(jData, dict):
            for key in jData:
                if jData[key] is False:
                    jData[key] = 'false'
                if jData[key] is True:
                    jData[key] = 'true'                    
                if jData[key] is None:
                    jData[key] = 'null'

            # for (key, value) in jData.items():
            #     if value == "False":
            #         value = "false"
            #     elif value == "True":
            #         value = "true"
            #     elif value == "None":
            #         value = "null"
            #     jData[key] = value

        sData = str(jData).replace("'",'"')

        # data = data.replace('False', 'false')
        # data = data.replace('True', 'true')
        # data = data.replace('None', 'null')
        # data = data.replace("'",'"')
        # data = data.replace("\n",'')
    pass
    return sData

def jsonTranslateValuesAdv(data):
    '''
    Replace predefined str in json content

    :param str data: jsonPath expression
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    data = str(data)
    data = data.replace('False', 'false')
    data = data.replace('True', 'true')
    data = data.replace('None', 'null')
    data = data.replace("'",'"')
    data = data.replace("\\n",'')
    data = data.replace("\\t",'')
    data = data.replace("\n",'')
    data = data.replace("\\",'')
    return data    

def jsonTranslateValues4Panda(data):
    '''
    Replace predefined str in json content

    :param str data: jsonPath expression
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    data = str(data)
    data = data.replace('False', "'false'")
    data = data.replace('True', "'true'")
    data = data.replace('None', "'null'")
    data = data.replace("'",'"')
    data = data.replace("\n",'')
    return data  

def sTranslate4Json(data):
    '''
    Replace predefined str in json content

    :param str data: json string
    :return: content
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    sData = str(data)
    xData = sData.replace("None","null")
    xData = xData.replace("True","true")
    xData = xData.replace("False","false")
    xData = xData.replace("True","true")

    return xData

def dTranslate4Json(data):
    '''
    Replace predefined str in dict content

    :param str data: json string
    :return: content
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''   

    sData = str(data)
    xData = sData.replace("None","null")
    xData = xData.replace("True","true")
    xData = xData.replace("False","false")
    xData = xData.replace("'",'"')

    return xData

def extract(data, arr, key):
    '''
    Extract value from content

    :param str data: json content
    :param arrray arr: json content
    :param str key: jsonPath expression
    :return: content
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                extract(v, arr, key)
            elif k == key:
                arr.append(v)
    elif isinstance(data, list):
        for item in data:
            extract(item, arr, key)
    return arr

def jsonExtractValues(data, key):
    '''
    Extract data from json content

    :param str data: json content
    :param str key: string to search for
    :return: content
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''         
    arr = []
    results = extract(data, arr, key)
    return results

def jsonExtractSimpleValue(data, key):
    '''
    Extract data from json content

    :param str data: json content
    :param str key: string to search for
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    value =""
    try:
        data = json.loads(data)
        value = data[key]
    except ValueError as error:
        logger.error('Script: Invalid json: %s', error)
    else:
        value = data[key]

    return value

def jsonMergeObjects(* argv):
    '''
    Merge json content

    :param str *: json content
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    data_list = []
    json_data = {}
    for arg in argv:
        json_data = json.loads(str(arg))
        data_list.append(json_data)
    json_data = json.dumps(data_list)
    if _localDebug:
        logger.debug('Core: JSON Merge: %s', json_data) 
    return json_data

def encodeUrl(data):
    '''
    Encode url

    :param str data: url
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''          
    data = str(data)
    data = urllib.parse.quote(data)
    return data

def getHostIP(hostname):
    '''
    Get IP address for given hostname

    :param str hostname: hostname
    :return: ip address
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''          
    if _localDebug:
        logger.debug('Script: Get IP of Host Name: %s', hostname)
    
    try:
        ip = str(socket.gethostbyname(hostname))
        if _localDebug:
            logger.debug('Script: Host IP: %s', ip)
        return ip

    except socket.gaierror as exp: 
        # Issues on MAC OS System Platform
        logger.error('Script: Get Host IP Socket Error: %s', exp)
        try: 
            ip = socket.gethostbyname(hostname+ '.local')
            if _localDebug:
                logger.debug('Script: Host IP with .local: %s', ip)
            return ip
        except: pass
    except: pass

def getHostName():
    '''
    Get hostname of current system

    :return: hostname
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    try:
        data = socket.gethostname() 
        hostName = data
        return hostName
    except Exception as exp:
        logger.error('Script: Get Hostname Socket Error: %s', exp)
        return False

def getHostFqdn(hostname):
    '''
    Get full qualified domain name for given hostnamr

    :param str hostname: hostname
    :return: fqdn
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    if _localDebug:
        logger.debug('Script: Host Name / IP: %s', hostname)
    
    try:
        data = str(socket.getfqdn(hostname))
        fqdn = data
        if _localDebug:
            logger.debug('Script: Host FQDN: %s', fqdn)
        return fqdn
    except Exception as exp:
        logger.error('Script: Get Host FQDN Socket Error: %s', exp)
        return False

def getHostDomain(hostname):
    '''
    Extract domain name for given hostname

    :param str hostname: hostname
    :return: domain
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    fqdn = getHostFqdn(hostname)
    domain  = ".".join(fqdn.split('.')[1:])
    return domain

def getHostFromFQDN(fqdn):
    '''
    Extract hostname name for given full qualified hostname

    :param str hostname: full qualified hostname
    :return: hostname
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      
    hostname = fqdn.split('.')[0]
    return hostname    

def getHostByIP(hostIP):
    '''
    Get hostname name for given ip address

    :param str hostname: full qualified hostname
    :return: ip address
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    if _localDebug:
        logger.debug('Script: Host IP: %s', hostIP)
    try:
        data = socket.gethostbyaddr(hostIP)[0]
        hostName = data
        if _localDebug:
            logger.debug('Script: Host Name: %s', hostName)
        return hostName
    except Exception as exp:
        logger.error('Script: Socket Error: %s', exp)
        return False

def getHostAddressInfo(hostname,port):
    '''
    Extract hostname name for given full qualified hostname

    :param str hostname: The host parameter takes either an ip address or a host name.
    :param int port: The port number of the service. If zero, information is returned for all supported socket types
    :return: full qualified hostname
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    if _localDebug:
        logger.debug('Script: Host Name: %s Port: %s', hostname ,port)
    
    try:
        data = str(socket.getaddrinfo(hostname, port))
        fqdn = data
        if _localDebug:
            logger.debug('Script: Host Info: %s', fqdn)
        return fqdn
    except Exception as exp:
        logger.error('Script: Socket Error: %s', exp)
        return False        

def getCryptoKeyFile():
    '''
    Get fully qualified file name to support encryption / decryption functions

    :return: file name
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    sCryptoKeyFileName = checkCustomCryptoFile(folder=pFolder)
    return sCryptoKeyFileName
    
def encrypt(data, sKeyFileName=""):
    '''
    Symmetrically encrypt data 

    :param str data: The data to symmetrically encrypt
    :param str sKeyFileName: file that contains the encryption key, if empty: use default base of 'sCryptoKeyFileName'
    :return: encrypted data 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''    

    sPwd = data    
    if len(sKeyFileName) < 1:
        sCryptoKeyFile = getCryptoKeyFile()
    else:
        sCryptoKeyFile = sKeyFileName

    key = getCryptoKey(sCryptoKeyFile)
    # cipher = AES.new(key.encode(), AES.MODE_CBC)
    cipher = AES.new(key, AES.MODE_CBC)
    value = b64encode(cipher.iv).decode('utf-8') + b64encode(cipher.encrypt(pad(sPwd.encode(), AES.block_size))).decode('utf-8') + str(len(b64encode(cipher.iv).decode('utf-8')))
    sPwd = "ENC[" + value + "]"
    
    return sPwd

def decrypt(data, sKeyFileName=""):
    '''
    Symmetrically decrypt data 

    :param str data: The data to symmetrically decrypt
    :param str sKeyFileName: file that contains the encryption key, if empty: use default base of 'sCryptoKeyFileName'
    :return: decrypted data 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      


    if "ENC[" in data:
         start = data.find('ENC[') + 4
         end   = data.find(']', start)
         sPwd  = data[start:end]
    else:
        sPwd = data

    if len(sKeyFileName) < 1:
        sCryptoKeyFile = getCryptoKeyFile()
    else:
        sCryptoKeyFile = sKeyFileName

    key = getCryptoKey(sCryptoKeyFile)
    cipher = AES.new(key, AES.MODE_CBC, b64decode(sPwd[0:int(sPwd[-2:]):1]))
    value = unpad(cipher.decrypt(b64decode(sPwd[int(sPwd[-2:]) :len(sPwd):1])), AES.block_size).decode('utf-8')

    return value

def getCryptoKey(sKeyFileName):
    '''
    Get symmetric crypto key 

    :param str sKeyFileName: file that contains the encryption key, if the file does not exist, create one.
    :return: decrypted data 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''        
    if len(sKeyFileName) < 1:
        sCryptoKeyFile = sCryptoKeyFileName
    else:
        sCryptoKeyFile = sKeyFileName

    try:
        with open(sCryptoKeyFile, "rb" ) as keyfile:
            keySecret = keyfile.read()
    except FileNotFoundError as err:
        logger.error('Script: Crypto File Error: %s', err)
        keySecret = os.urandom(16)
        with open(sCryptoKeyFile, "wb") as keyfile:
            keyfile.write(keySecret)

    # value = key_data["AESCrypto"]
    value = keySecret
    if _localDebug:
        logger.debug('Script: Crypto File: "%s"', sCryptoKeyFile)
        logger.debug('Script: Crypto Secret: %s', keySecret)
    return value

def encryptPwd(data,sKeyFileName=""):
    '''
    Symmetrically encrypt password 

    :param str data: The password to symmetrically encrypt
    :return: encrypted password 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    value = encrypt(data=data,sKeyFileName=sKeyFileName)
    if _localDebug:
        logger.debug('Script: Encrypt Data: %s', value)
    return value

def decryptPwd(data,sKeyFileName=""):
    '''
    Symmetrically decrypt password 

    :param str data: The password to symmetrically decrypt
    :return: decrypted password 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    value = decrypt(data=data,sKeyFileName=sKeyFileName)
    if _localDebug:
        logger.debug('Script: Encrypt Data: %s', value)
    return value    

def convertCsv2Json(data,keepDuplicate=False,replaceEmpty=False):
    '''
    Convert panda with csv data to json 

    :param str data: panda with csv data
    :param str keepDuplicate: panda method of handling duplicate records
    :param boolean replaceEmpty: replace empty call with default value
    :return: data
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    df = convertCsv2Panda(data=data,keepDuplicate=keepDuplicate)
    if replaceEmpty:
        df.fillna("Not Defined",inplace=True)
    json_data = df.to_json(orient='records')
    return json_data

def convertCsv2Panda(data,keepDuplicate=False):
    '''
    Convert csv data to panda dataframe

    :param str data: data in csv format
    :return: data
    :rtype: panda dataframe
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''        
    df = pd.read_csv(StringIO(data))
    df = df.drop_duplicates(keep=keepDuplicate)
    return df

def convertJson2Panda(data,keepDuplicate=False):
    '''
    Convert JSON data to panda dataframe

    :param str data: data in JSON format
    :return: data
    :rtype: panda dataframe
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''        
    df = pd.read_json(StringIO(data),orient='records')
    df = df.drop_duplicates(keep=keepDuplicate)
    return df    

def convertJson2Csv(data):
    df = convertJson2Panda(data=data)
    csvData = df.to_csv(index=False)
    return csvData
    
def copyFile(srcFile,dstFile,override=False):
    '''
    Copy file from src to dst

    :param str src: a given source file name, fully qualified
    :param str dst: a given target file name, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''     
    srcFile = str(srcFile)
    dstFile = str(dstFile)
    sFileStatusSource = getFileStatus(srcFile)    
    sFileStatusDest = getFileStatus(dstFile)    

    if sFileStatusDest:
        if override:        
            try:
                if sFileStatusSource:
                    shutil.copy(srcFile, dstFile)
            except OSError as err:
                logger.error('Script: File Copy Error: %s', err)              
        else:
            logger.error('Script: File Exists: %s', dstFile)
    else:
        try:
            if sFileStatusSource:
                shutil.copy(srcFile, dstFile)        
        except OSError as err:
            logger.error('Script: File Copy Error: %s', err)

  
# Check Custom Config File
def checkCustomConfigFile(folder):
    jCfgFName =  sHostname + ".json"
    cfgFolder = os.path.join( folder,"configs")

    # Create Config folder if not exists
    if not getFolderStatus(cfgFolder):
        createFolder(cfgFolder) 

    jCfgFile  = os.path.join( cfgFolder,jCfgFName)    
    jCfgFileStatus = getFileStatus(jCfgFile)

    if not jCfgFileStatus:
        jCfgSampleFName = "integrations.json"
        jCfgSampleFile  = os.path.join( getCurrentFolder(),"samples",jCfgSampleFName)
        copyFile(srcFile=jCfgSampleFile,dstFile=jCfgFile)
    return jCfgFile

# Check Custom Crypto File
def checkCustomCryptoFile(folder):
    jCfgFName =  sHostname + ".bin"
    jCfgFile  = os.path.join( folder,"configs",jCfgFName)
    jCfgFileStatus = getFileStatus(jCfgFile)

    if not jCfgFileStatus:
        keySecret = os.urandom(16)
        with open(jCfgFile, "wb") as keyfile:
            keyfile.write(keySecret)
    
    return jCfgFile  


# Project Core Folder
def getProjectFolder():
    '''
    Get current project folder

    :param: 
    :return: path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''  

    if platform.system() == "Windows":
        projectFolder = getCurrentFolder()
    else:
        home = expanduser("~")
        projectFolder = concatPath(home,".w3rkstatt")
            # Create Config folder if not exists
        if not getFolderStatus(projectFolder):
            createFolder(projectFolder) 

    return projectFolder


# Security functions
def secureCredentials(folder,file,data):
    '''
    Encrypt clear text passwords in config json file and update file

    :param str folder: project folder
    :param str file: configuration file name
    :param json data: configuration data in json
    :return: data
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''  
    # Crypto Support
    sCryptoKeyFileName = checkCustomCryptoFile(folder=folder)
    sCfgData = encryptPwds(file=file,data=data,sKeyFileName=sCryptoKeyFileName)
    return sCfgData


def encryptPwds(file,data,sKeyFileName=""):
    '''
    Encrypt clear text passwords in config json file and update file

    :param str file: config file name
    :param json data: config data in json format
    :param str sKeyFileName: crypto key file name
    :return: data
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''  
    pItemList = data.keys()
    sCfgData  = data
    sCfgFile  = file
    for pItem in pItemList:
        logger.info('Crypto Process Credentials for: %s', pItem)
        securePwd = ""
        jSecPwd = ""

        # unSecPwd = werkstatt.jsonExtractValues(jCfgData,pItem)[0]
        vPath = "$." + pItem + ".pwd"
        jPath = "$." + pItem + ".jks_pwd"

        unSecPwd = getJsonValue(path=vPath,data=sCfgData)
        ujSecPwd = getJsonValue(path=jPath,data=sCfgData)

        if len(unSecPwd) > 0: 
                if "ENC[" in unSecPwd:
                    start = unSecPwd.find('ENC[') + 4
                    end   = unSecPwd.find(']', start)
                    sPwd  = unSecPwd[start:end]

                else:
                    sPwd = unSecPwd
                    securePwd = encryptPwd(data=sPwd,sKeyFileName=sKeyFileName)  
                    logger.info('Crypto Encrypt Password for: "%s"', pItem)

                    if _localDebug: 
                        print (f"Encrypted user password for {pItem}: {securePwd}")  

                    sCfgData[pItem]["pwd"]= securePwd

        # Java Keystore passwords
        if len(ujSecPwd) > 0:
                if "ENC[" in unSecPwd:
                    start = unSecPwd.find('ENC[') + 4
                    end   = unSecPwd.find(']', start)
                    sPwd  = unSecPwd[start:end]

                else:
                    sPwd = unSecPwd
                    securePwd = encryptPwd(data=sPwd,sKeyFileName=sKeyFileName)  
                    logger.info('Crypto Encrypt JKS Password for: "%s"', pItem)
                    if _localDebug: 
                        print (f"Encrypted user JKS password for {pItem}: {securePwd}")  

                    sCfgData[pItem]["pwd_secure"] = securePwd
                    sCfgData[pItem]["pwd"]= securePwd


        if _localDebug:
            logger.debug('Core: Security Function: "%s" ', "Encrypt")
            logger.debug('Core: Security Solution: "%s" ', pItem)
            logger.debug('Core: unSecure Pwd: "%s" ', unSecPwd)
            logger.debug('Core: Secure Pwd: "%s"\n', securePwd)
    
    # update config json file
    logger.info('Crypto Update config file: "%s"', sCfgFile)
    writeJsonFile(file=sCfgFile,content=sCfgData)
    return sCfgData


def decryptPwds(data):
    '''
    Derypt passwords in config json file print 

    :param json data: config data in json format
    :return: path
    :rtype: 
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''  
    pItemList = data.keys()
    sCfgData  = data
    for pItem in pItemList:
        unSecPwd = ""

        # unSecPwd = werkstatt.jsonExtractValues(jCfgData,pItem)[0]
        vPath = "$." + pItem + ".pwd"
        sPwd = getJsonValue(path=vPath,data=sCfgData)
        if len(sPwd) > 0:
            unSecPwd = decryptPwd(data=sPwd)            
            print (f"Decrypted password for {pItem}: {unSecPwd}")
        if _localDebug:
            logger.debug('Core: Security Function: "%s" ', "Decrypt")
            logger.debug('Core: Security Solution: "%s" ', pItem)
            logger.debug('Core: unSecure Pwd: "%s" ', unSecPwd)
            logger.debug('Core: Secure Pwd: "%s"\n', sPwd)


# Create a custom logger
pFolder   = getProjectFolder()
sHostname = str(getHostName()).lower()
sPlatform = platform.system()
sUuid     = str(uuid.uuid4())

jCfgFile  = checkCustomConfigFile(folder=pFolder)
jCfgData  = getFileJson(jCfgFile)
logFolder = getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
loglevel  = getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
datFolder = getJsonValue(path="$.DEFAULT.data_folder",data=jCfgData)

# Central logging facility
if not getFolderStatus(logFolder):
    projectFolder = getProjectFolder()
    logFolder     = os.path.join(projectFolder,"logs")
    createFolder(logFolder)
    jCfgData["DEFAULT"]["log_folder"]=logFolder

# Central data folder
if not getFolderStatus(datFolder):
    projectFolder = getProjectFolder()
    datFolder     = os.path.join(projectFolder,"data")
    createFolder(datFolder)
    jCfgData["DEFAULT"]["data_folder"]=datFolder

logger  = logging.getLogger(__name__)
logFile = os.path.join(logFolder,"integrations.log")

if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='a', level=logging.DEBUG, format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('Werkstatt Python Core Script "Start"')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: "%s" ', sPlatform)   
    logger.info('System Name: "%s" ', sHostname)  
    logger.info('System Config JSON File: "%s" ', jCfgFile)  
    logger.info('Project Folder: "%s" ', pFolder) 
    logger.info('Log Folder: "%s" ', logFolder) 
    logger.info('Data Folder: "%s" ', datFolder) 
    logger.info('Config File: "%s" ', jCfgFile) 
    logger.info('Crypto Key File: "%s" ', getCryptoKeyFile()) 

    sCfgData = secureCredentials(folder=pFolder,file=jCfgFile,data=jCfgData)
    if _SecureDebug:
        decryptPwds(data=sCfgData)

    logger.info('Werkstatt Python Core Script "End"')
    logging.shutdown()
    print (f"Version: {_modVer}")
    print (f"Log File: {logFile}")



