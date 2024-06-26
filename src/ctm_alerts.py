#!/usr/bin/env python3
# Filename: ctm_alerts.py
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
20210527      Volker Scheithauer    Tranfer Development from other projects
20220715      Volker Scheithauer    BMC Helix Operation Management Integration
20240503      Volker Scheithauer    Fix CTM Alert conversion to json

"""

import time
import logging
import sys
import getopt
import platform
import argparse
import os
import json
from collections import OrderedDict
import collections
from xml.sax.handler import ContentHandler
from xml.sax import make_parser

# handle dev environment vs. production
try:
    import w3rkstatt as w3rkstatt
    import core_ctm as ctm
    import core_bhom as bhom
except:
    # fix import issues for modules
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstatt
    from src import core_ctm as ctm
    from src import core_bhom as bhom

# Get configuration from bmcs_core.json
jCfgData = w3rkstatt.getProjectConfig()
cfgFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",
                                   data=jCfgData)
logFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder", data=jCfgData)
tmpFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",
                                   data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",
                                    data=jCfgData)

data_folder = logFolder
ctm_host = w3rkstatt.getJsonValue(path="$.CTM.host", data=jCfgData)
ctm_port = w3rkstatt.getJsonValue(path="$.CTM.port", data=jCfgData)

integration_bhom_enabled = w3rkstatt.getJsonValue(path="$.CTM.bhom.enabled",
                                                  data=jCfgData)

# Extract CTM job log & details
# Level: full, mini
ctm_job_log_level = w3rkstatt.getJsonValue(path="$.CTM.jobs.log_level",
                                           data=jCfgData)
ctm_job_detail_level = w3rkstatt.getJsonValue(path="$.CTM.jobs.detail_level",
                                              data=jCfgData)

ctmCoreData = None
ctmJobData = None
ctmAlertFileName = ""

# Assign module defaults
_localDebug = jCfgData["DEFAULT"]["debug"]["api"]
_localDebugFunctions = jCfgData["DEFAULT"]["debug"]["functions"]
_localDebugData = jCfgData["DEFAULT"]["debug"]["data"]
_localDebugAdvanced = jCfgData["DEFAULT"]["debug"]["advanced"]
_localQA = jCfgData["DEFAULT"]["debug"]["qa"]
_localDebugBHOM = jCfgData["BHOM"]["debug"]

_FutureUse = False

_localInfo = False
_modVer = "3.1"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_ctmActiveApi = False

logger = w3rkstatt.logging.getLogger(__name__)
logFile = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file", data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)
hostFqdn = w3rkstatt.getHostFqdn(hostName)
domain = w3rkstatt.getHostDomain(hostFqdn)
parser = argparse.ArgumentParser(prefix_chars=':')
sUuid = w3rkstatt.sUuid


def ctmAlert2Dict(list, start, end):
    """    Converts list to dicts
    Added start and end to function parms to allow for 0 or 1 start and custom end.
    first parm is key, second value, and so on.
    :type lst: list
    :type start: int
    :type end: int
    """

    # Linux arguments
    # '/opt/ctmexpert/ctm-austin/bmcs_crust_ctm_alert.py', 'call_type:', 'I', 'alert_id:', '208905', 'data_center:', 'psctm', 'memname:', 'order_id:', '00000', 'severity:', 'R', 'status:', 'Not_Noticed', 'send_time:', '20210413165844', 'last_user:', 'last_time:', 'message:', 'STATUS', 'OF', 'AGENT', 'PLATFORM', 'vl-aus-ctm-ap01.ctm.bmc.com', 'CHANGED', 'TO', 'AVAILABLE', 'run_as:', 'sub_application:', 'application:', 'job_name:', 'host_id:', 'alert_type:', 'R', 'closed_from_em:', 'ticket_number:', 'run_counter:', '00000000000', 'notes:'
    res_dct = {}
    param = None
    value = None
    sAlert = str(list).replace("',", "").replace("'", "")
    sCustom = ""

    try:
        if w3rkstatt.sPlatform == "Linux":
            if _localDebugFunctions or _localDebugData:
                logger.debug('Function = "%s" ', "ctmAlert2Dict")
                # logger.debug('Script Arguments for Linux ')
                # logger.debug('Script Arguments #     = %s ', len(list))
                # logger.debug('Script Arguments Start = %s ', start)
                # logger.debug('Script Arguments End   = %s ', end)
                # logger.debug('Script Arguments List  = %s ', str(list))
                logger.debug('Script Arguments Str   = %s ', str(sAlert))

            for counter in range(start, end):
                entry = str(list[counter])

                if entry[-1] == ":":
                    param = list[counter].replace(":", "")
                    sCustom = str(sCustom) + "," + param + ":"
                else:
                    value = str(list[counter]).strip().replace(",", " ")
                    sCustom = str(sCustom) + str(value) + " "

                # res_dct[param] = value

            sCustom = str(sCustom)  # + "'"
            sCustom = sCustom[1:]

            res_dct = dict(item.split(":") for item in sCustom.split(","))

            for (key, value) in res_dct.items():

                if len(value) < 1:
                    value = None
                else:
                    value = value.replace('"', '').strip()
                    if len(value) < 1:
                        value = None

                res_dct[key] = value
                if _localDebugFunctions or _localDebugData:
                    logger.debug('Arguments %s=%s ', key, value)

        else:

            for counter in range(start, end, 2):
                list[counter] = list[counter].replace(":", "")
                value = str(list[counter + 1]).strip()
                param = list[counter]

                if len(value) < 1:
                    value = None
                if _localDebugFunctions or _localDebugData:
                    logger.debug('%s="%s" ', param, value)

                res_dct[param] = value
    except:
        pass

    return res_dct


def getCtmJobInfo(ctmApiClient, data):
    # Get Job Info via CTM API
    ctmData = data
    ctmDataCenter = w3rkstatt.getJsonValue(path="$.data_center", data=ctmData)
    ctmOrderId = w3rkstatt.getJsonValue(path="$.order_id", data=ctmData)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobInfo")
        logger.info('CTM Get Job Info: "%s:%s"', ctmDataCenter, ctmOrderId)
    jData = ctm.getCtmJobInfo(ctmApiClient=ctmApiClient,
                              ctmServer=ctmDataCenter,
                              ctmOrderID=ctmOrderId)

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "jData")
    return jData


def getCtmJobRunLog(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter", data=data)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobRunLog")
        logger.info('CTM Get Job Run Log: "%s # %s"', ctmJobID,
                    ctmJobRunCounter)

    sLogData = ctm.getCtmJobLog(ctmApiClient=ctmApiClient, ctmJobID=ctmJobID)
    if _localDebugFunctions:
        logger.info('CMT QA Get Job Run Log: %s', sLogData)

    # Based on config, extract level of details
    if ctm_job_log_level == "full":
        jCtmJobLog = ctm.transformCtmJobLog(data=sLogData)
    else:
        jCtmJobLog = ctm.transformCtmJobLogMini(data=sLogData,
                                                runCounter=ctmJobRunCounter)

    if _localDebugFunctions or _localDebugData:
        logger.debug('CMT Job Run Log Raw: %s', jCtmJobLog)

    sCtmJobLog = str(jCtmJobLog)

    return sCtmJobLog


def getCtmJobLog(ctmApiClient, data):
    # Get CTM job log after 30 sec - wait for archive server to have log
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobLog")
        logger.debug('CMT Job Log: First attempt to retrieve data')
    time.sleep(2)
    sCtmJobLog = getCtmJobRunLog(ctmApiClient, data)

    if _localDebugFunctions or _localDebugData:
        logger.debug('CMT Job Log Raw: %s', sCtmJobLog)

    jCtmJobLog = json.loads(sCtmJobLog)
    ctmStatus = w3rkstatt.getJsonValue(path="$.status", data=jCtmJobLog)

    if ctmStatus != True:
        if _localDebugFunctions:
            logger.debug('CMT Job Log: Second attempt to retrieve data')
        time.sleep(2)
        jCtmJobLog = getCtmJobRunLog(ctmApiClient, data)
        sCtmJobLog = w3rkstatt.dTranslate4Json(data=jCtmJobLog)

    return sCtmJobLog


def getCtmJobConfig(ctmApiClient, data):
    jCtmJobInfo = data
    ctmFolderInfo = getCtmFolder(ctmApiClient=ctmApiClient, data=jCtmJobInfo)
    jCtmFolderInfo = json.loads(ctmFolderInfo)
    iCtmFolderInfo = w3rkstatt.getJsonValue(path="$.count",
                                            data=jCtmFolderInfo)
    sStatus = w3rkstatt.getJsonValue(path="$.status", data=jCtmFolderInfo)

    if ctm_job_detail_level == "full" or iCtmFolderInfo == 1:
        jCtmJobDetail = ctmFolderInfo
        sCtmJobDetail = w3rkstatt.dTranslate4Json(data=jCtmJobDetail)
    else:
        if _localDebugData:
            logger.debug('Function = "%s" ', "getCtmJobConfig")
            logger.debug('CMT Job Config: "%s"', jCtmJobInfo)
        if sStatus:
            jCtmJobName = w3rkstatt.getJsonValue(path="$.name",
                                                 data=jCtmJobInfo)
            jCtmFolderName = w3rkstatt.getJsonValue(path="$.folder",
                                                    data=jCtmJobInfo)
            jQl = "$." + str(jCtmFolderName) + "." + str(jCtmJobName)
            jData = json.loads(ctmFolderInfo)
            jCtmJobDetail = w3rkstatt.getJsonValue(path=jQl, data=jData)
            sCtmJobDetail = w3rkstatt.dTranslate4Json(data=jCtmJobDetail)
        else:
            sCtmJobDetail = ctmFolderInfo

    return sCtmJobDetail


def getCtmArchiveJobLog(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                              data=ctmData)
    value = ctm.getCtmArchiveJobLog(ctmApiClient=ctmApiClient,
                                    ctmJobID=ctmJobID,
                                    ctmJobRunCounter=ctmJobRunCounter)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmArchiveJobLog")
        logger.debug('CMT Job Log Raw: %s', value)
    return value


def getCtmJobRunOutput(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                              data=ctmData)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobRunOutput")
        logger.info('CTM Get Job Run Output: "%s # %s"', ctmJobID,
                    ctmJobRunCounter)

    value = ctm.getCtmJobOutput(ctmApiClient=ctmApiClient,
                                ctmJobID=ctmJobID,
                                ctmJobRunId=ctmJobRunCounter)
    if _localDebugFunctions:
        logger.debug('CMT Job Output Raw: %s', value)

    ctmJobOutput = ctm.transformCtmJobOutput(data=value)

    if _localDebugFunctions or _localDebugData:
        logger.debug('CMT Job Run Output: %s', ctmJobOutput)
    return ctmJobOutput


def getCtmArchiveJobRunOutput(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                              data=ctmData)
    value = ctm.getCtmArchiveJobOutput(ctmApiClient=ctmApiClient,
                                       ctmJobID=ctmJobID,
                                       ctmJobRunId=ctmJobRunCounter)
    ctmJobOutput = ctm.transformCtmJobOutput(data=value)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmArchiveJobRunOutput")
        logger.debug('CMT Job Output Raw: %s', ctmJobOutput)
    return ctmJobOutput

def getCtmJobOutput(ctmApiClient, data):
    # Get CTM job log after 30 sec - wait for archive server to have log
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobOutput")
        logger.debug('CMT Job Output: First attempt to retrieve data')
    time.sleep(2)
    jCtmJobOutput = getCtmJobRunOutput(ctmApiClient, data)
    ctmStatus = w3rkstatt.getJsonValue(path="$.status", data=jCtmJobOutput)

    if ctmStatus != True:
        if _localDebugFunctions:
            logger.debug('CMT Job Output: Second attempt to retrieve data')
        time.sleep(2)
        jCtmJobOutput = getCtmJobRunOutput(ctmApiClient, data)

    # transform to JSON string
    sCtmJobOutput = w3rkstatt.dTranslate4Json(data=jCtmJobOutput)

    return sCtmJobOutput

def getCtmFolder(ctmApiClient, data):
    ctmData = data
    ctmFolderID = ctmData["entries"][0]["folder_id"]
    ctmFolder = ctmData["entries"][0]["folder"]
    ctmServer = ctmData["entries"][0]["ctm"]
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmFolder")
        logger.info('CTM Get Job Folder: "%s @ %s"', ctmFolder, ctmServer)
    value = ctm.getCtmDeployedFolder(ctmApiClient=ctmApiClient,
                                     ctmServer=ctmServer,
                                     ctmFolder=ctmFolder)

    # adjust new ctm aapi result
    sCtmDeployedFolderTmp = w3rkstatt.dTranslate4Json(str(value))
    jCtmDeployedFolderTmp = json.loads(sCtmDeployedFolderTmp)
    jCtmDeployedFolder = jCtmDeployedFolderTmp

    # adjust if CTM API access failed
    sJobLogStatus = True
    # Failed to get
    if "Failed to get" in str(sCtmDeployedFolderTmp):
        sJobLogStatus = False
        sEntry = ""
        i = 0
    else:
        sEntry = sCtmDeployedFolderTmp[1:-1]
        i = 1

    # Check future use?
    # if "." in value:
    #     xTemp = value.split(".")
    #     for xLine in xTemp:
    #         zValue = xLine.strip()
    #         # construct json string
    #         if i == 0:
    #             sEntry = '"entry-' + str(i).zfill(4) + '":"' + zValue + '"'
    #         else:
    #             sEntry = sEntry + ',"entry-' + \
    #                 str(i).zfill(4) + '":"' + zValue + '"'
    #         i += 1
    # else:
    #     sEntry = '"entry-0000": "' + value + '"'

    jData = '{"count":' + str(i) + ',"status":' + \
        str(sJobLogStatus) + ',"entries":[{' + str(sEntry) + '}]}'
    sData = w3rkstatt.dTranslate4Json(data=jData)

    return sData


def analyzeAlert4Job(ctmApiClient, raw, data):
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "analyzeAlert4Job")
        logger.info('CTM: Analyze Alert for Jobs - Start')

    jCtmAlert = data
    ctmOrderId = w3rkstatt.getJsonValue(path="$.order_id", data=jCtmAlert)
    ctmJobData = None
    jCtmAlertData = json.dumps(jCtmAlert)
    sCtmAlertData = str(jCtmAlertData)
    jCtmAlertRaw = raw

    sCtmJobInfo = '{"count": 0,"status": "unknown"}'
    sCtmJobOutput = '{"count": 0,"status": "unknown"}'
    sCtmJobLog = '{"count": 0,"status": "unknown"}'
    sCtmJobConfig = '{"count": 0,"status": "unknown"}'

    if not ctmOrderId == "00000" and ctmOrderId is not None:

        if "New" in ctmAlertCallType:
            # Get CTM Job Info
            ctmJobId = w3rkstatt.getJsonValue(path="$.job_id", data=jCtmAlert)
            ctmJobName = w3rkstatt.getJsonValue(path="$.job_name",
                                                data=jCtmAlert)

            if _ctmActiveApi:
                # Get job information
                sCtmJobInfo = getCtmJobInfo(ctmApiClient=ctmApiClient,
                                            data=jCtmAlert)

                if _FutureUse:
                    # Get job output
                    sCtmJobOutput = getCtmJobOutput(ctmApiClient=ctmApiClient,
                                                    data=jCtmAlert)

                    jCtmJobOutput = json.loads(sCtmJobOutput)
                    sCtmJobOutputStatus = jCtmJobOutput["status"]

                    # Get job log
                    # if sCtmJobOutputStatus:
                    #     sCtmJobLog = getCtmJobLog(
                    #         ctmApiClient=ctmApiClient, data=jCtmAlert)
                    # else:
                    #    sCtmJobLog = '{"collection":"no accessible"}'
                    sCtmJobLog = getCtmJobLog(ctmApiClient=ctmApiClient,
                                              data=jCtmAlert)
                    jCtmJobLog = json.loads(sCtmJobLog)
                else:
                    sCtmJobLog = '{"count": 0,"status": "experimental"}'

                # Create JSON object
                jCtmJobInfo = json.loads(sCtmJobInfo)

                # Folder / Job Details
                ctmJobInfoCount = w3rkstatt.getJsonValue(path="$.count",
                                                         data=jCtmJobInfo)

                if ctmJobInfoCount >= 1:
                    sCtmJobConfig = getCtmJobConfig(ctmApiClient=ctmApiClient,
                                                    data=jCtmJobInfo)
                else:
                    xData = '{"count":0,"status":' + \
                        str(None) + ',"entries":[]}'
                    sCtmJobConfig = w3rkstatt.dTranslate4Json(data=xData)

            # Prep for str concat
            sCtmAlertRaw = str(jCtmAlertRaw)
            ctmJobData = '{"uuid":"' + sUuid + '","raw":[' + sCtmAlertRaw + '],"jobAlert":[' + sCtmAlertData + '],"jobInfo":[' + \
                sCtmJobInfo + '],"jobConfig":[' + sCtmJobConfig + '],"jobLog":[' + \
                sCtmJobLog + '],"jobOutput":[' + sCtmJobOutput + ']}'
            ctmJobData = w3rkstatt.dTranslate4Json(data=ctmJobData)

        # Convert event data to the JSON format required by the API.
    else:
        sCtmAlertRaw = str(jCtmAlertRaw)
        sjCtmAlert = w3rkstatt.dTranslate4Json(data=jCtmAlert)
        # defaults
        sCtmJobInfo = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) +
                                                ',"status":' + str(None) +
                                                ',"entries":[]}')
        sCtmJobOutput = w3rkstatt.dTranslate4Json(data='{"count":' +
                                                  str(None) + ',"status":' +
                                                  str(None) + ',"entries":[]}')
        sCtmJobLog = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) +
                                               ',"status":' + str(None) +
                                               ',"entries":[]}')
        sCtmJobConfig = w3rkstatt.dTranslate4Json(data='{"count":' +
                                                  str(None) + ',"status":' +
                                                  str(None) + ',"entries":[]}')
        ctmJobData = '{"uuid":"' + sUuid + '","raw":[' + sCtmAlertRaw + '],"jobAlert":[' + sCtmAlertData + '],"jobInfo":[' + \
            sCtmJobInfo + '],"jobConfig":[' + sCtmJobConfig + '],"jobLog":[' + \
            sCtmJobLog + '],"jobOutput":[' + sCtmJobOutput + ']}'

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "ctmJobData")
        logger.info('CTM: Analyze Alert for Jobs - End')
    return ctmJobData


def analyzeAlert4Core(raw, data):
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "analyzeAlert4Core")
        logger.info('CTM: Analyze Alert for Core - Start')

    jCtmAlert = data
    ctmCoreData = None
    jCtmAlertData = json.dumps(jCtmAlert)
    jCtmAlertRaw = raw

    # Prep for str concat
    sCtmAlertRaw = str(jCtmAlertRaw)
    sCtmAlertData = str(jCtmAlertData)

    ctmCoreData = '{"uuid":"' + sUuid + \
        '","raw":[' + sCtmAlertRaw + '],"coreAlert":[' + sCtmAlertData + ']}'
    ctmCoreData = w3rkstatt.jsonTranslateValues(ctmCoreData)
    ctmCoreData = w3rkstatt.jsonTranslateValuesAdv(ctmCoreData)

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "ctmCoreData")
        logger.info('CTM: Analyze Alert for Core - End')
    return ctmCoreData


def analyzeAlert4Infra(raw, data):
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "analyzeAlert4Infra")
        logger.info('CTM: Analyze Alert for Infra - Start')

    jCtmAlert = data
    ctmCoreData = None
    jCtmAlertData = json.dumps(jCtmAlert)
    jCtmAlertRaw = raw

    # Prep for str concat
    sCtmAlertRaw = str(jCtmAlertRaw)
    sCtmAlertData = str(jCtmAlertData)

    ctmCoreData = '{"uuid":"' + sUuid + \
        '","raw":[' + sCtmAlertRaw + '],"infraAlert":[' + sCtmAlertData + ']}'
    ctmCoreData = w3rkstatt.jsonTranslateValues(ctmCoreData)
    ctmCoreData = w3rkstatt.jsonTranslateValuesAdv(ctmCoreData)

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "ctmCoreData")
        logger.info('CTM: Analyze Alert for Infra - End')
    return ctmCoreData


def writeAlertFile(data, alert, type="job"):
    fileStatus = False
    fileName = None
    ctmJobData = data
    if _ctmActiveApi:
        fileType = "ctm-enriched-" + type + "-"
    else:
        fileType = "ctm-basic-" + type + "-"

    fileContent = json.loads(ctmJobData)
    fileJsonStatus = w3rkstatt.jsonValidator(data=ctmJobData)

    if fileJsonStatus:
        fileName = fileType + \
            alert.zfill(8) + "-" + str(epoch).replace(".", "") + ".json"
        filePath = w3rkstatt.concatPath(path=data_folder, folder=fileName)
        fileRsp = w3rkstatt.writeJsonFile(file=filePath, content=fileContent)
        fileStatus = w3rkstatt.getFileStatus(path=filePath)

        if _localDebugFunctions:
            logger.info('Function = "%s" ', "writeAlertFile")
            logger.info('CTM QA Alert File: "%s" ', filePath)

    return fileStatus, fileName


if __name__ == "__main__":
    logging.basicConfig(filename=logFile,
                        filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')

    sSysOutMsg = ""

    if _localInfo:
        logger.info('CTM: start event management - %s', w3rkstatt.sUuid)
        logger.info('Version: %s ', _modVer)
        logger.info('System Platform: %s ', w3rkstatt.sPlatform)
        logger.info('Log Level: %s', loglevel)
        logger.info('Epoch: %s', epoch)
        logger.info('Host Name: %s', w3rkstatt.sHostname)
        logger.info('UUID: %s', w3rkstatt.sUuid)

    # Extract script arguments
    sCtmArguments = sys.argv[1:]
    sCtmArgDict = ctmAlert2Dict(list=sCtmArguments,
                                start=0,
                                end=len(sCtmArguments))
    jCtmArgs = json.dumps(sCtmArgDict)
    jCtmAlert = json.loads(jCtmArgs)
    ctmAlertId = str(w3rkstatt.getJsonValue(path="$.alert_id",
                                            data=jCtmAlert)).strip()
    ctmRunCounter = None

    # Test integration with sample data
    if not len(ctmAlertId) > 0:
        if _localQA:
            jCtmAlert = {
                "call_type": "I",
                "alert_id": "279",
                "data_center": "ctm-srv.trybmc.com",
                "memname": None,
                "order_id": "0000q",
                "severity": "V",
                "status": "Not_Noticed",
                "send_time": "20220729163544",
                "last_user": None,
                "last_time": None,
                "message": "Ended not OK",
                "run_as": "dbus",
                "sub_application": "Integration",
                "application": "ADE",
                "job_name": "Agent Health",
                "host_id": "ctm-net.trybmc.com",
                "alert_type": "R",
                "closed_from_em": None,
                "ticket_number": None,
                "run_counter": "00014",
                "notes": None
            }

            jCtmAlert = {
                "call_type": "I",
                "alert_id": "1981",
                "data_center": "ctm-srv.shytwr.net",
                "memname": None,
                "order_id": None,
                "severity": "V",
                "status": "Not_Noticed",
                "send_time": "20240412112921",
                "last_user": None,
                "last_time": None,
                "message": "SERVER ctm-srv.shytwr.net WAS DISCONNECTED",
                "run_as": "Gateway",
                "sub_application": None,
                "application": None,
                "job_name": None,
                "host_id": None,
                "alert_type": "R",
                "closed_from_em": None,
                "ticket_number": None,
                "run_counter": None,
                "notes": None
            }

    if len(jCtmAlert) > 0:

        if _localDebugData:
            logger.debug('Function = "%s" ', "__main__")
            logger.debug('CTM Initial Alert JSON: %s', jCtmAlert)

        # Transform CTM Alert
        jCtmAlertRaw = json.dumps(jCtmAlert)
        sCtmAlert = ctm.trasnformtCtmAlert(data=jCtmAlert)
        jCtmAlert = json.loads(sCtmAlert)
        ctmEventType = ctm.extractCtmAlertType(jCtmAlert)
        ctmAlertId = str(w3rkstatt.getJsonValue(path="$.alert_id", data=jCtmAlert))
        ctmAlertCallType = w3rkstatt.getJsonValue(path="$.call_type",data=jCtmAlert)
        ctmDataCenter = w3rkstatt.getJsonValue(path="$.data_center", data=jCtmAlert)

        ctmOrderId = w3rkstatt.getJsonValue(path="$.order_id", data=jCtmAlert)
        ctmRunCounter = w3rkstatt.getJsonValue(path="$.run_counter", data=jCtmAlert)
        ctmAlertCat = w3rkstatt.getJsonValue(path="$.system_category", data=jCtmAlert)
        ctmAlertSev = w3rkstatt.getJsonValue(path="$.severity", data=jCtmAlert)
        sCtmJobCyclic = w3rkstatt.getJsonValue(path="$.jobInfo.[0].cyclic", data=jCtmAlert)
        ctmAlertNotes = w3rkstatt.getJsonValue(path="$.notes", data=jCtmAlert)

        # clean up data
        if ctmAlertId and not ctmAlertId.startswith("None"):
            ctmAlertId = ctmAlertId.strip()

        if ctmAlertCallType and not ctmAlertCallType.startswith("None"):
            ctmAlertCallType = ctmAlertCallType.strip()

        if ctmDataCenter and not ctmDataCenter.startswith("None"):
            ctmDataCenter = ctmDataCenter.strip()

        if ctmOrderId and not ctmOrderId.startswith("None"):
            ctmOrderId = ctmOrderId.strip()

        if ctmRunCounter and not ctmRunCounter.startswith("None"):
            ctmRunCounter = ctmRunCounter.strip()

        if ctmAlertCat and not ctmAlertCat.startswith("None"):
            ctmAlertCat = ctmAlertCat.strip()

        if ctmAlertSev and not ctmAlertSev.startswith("None"):
            ctmAlertSev = ctmAlertSev.strip()

        if sCtmJobCyclic and not sCtmJobCyclic.startswith("None"):
            sCtmJobCyclic = sCtmJobCyclic.strip()

        if _localDebugData:
            logger.info('CTM Extract Alert Category: %s', ctmAlertCat)
            logger.info('CTM Extract Alert ID: %s', ctmAlertId)
            logger.info('CTM Extract Alert Type: "%s"', ctmEventType)
            logger.info('CTM Extract Alert Category: "%s"', ctmAlertCat)
            logger.info('CTM Extract Job Datacenter: %s', ctmDataCenter)
            logger.info('CTM Extract Job ID: %s', ctmOrderId)
            logger.info('CTM Extract Run Counter: %s', ctmRunCounter)
            logger.info('CTM Extract Alert Call: "%s"', ctmAlertCallType)

            

        # Process only 'new' alerts
        if "New" in ctmAlertCallType:
            logger.info('')
            logger.info('CMT New Alert Processing: %s', jCtmAlertRaw)
            logger.info('CMT New Alert Category: "%s"', ctmAlertCat)


            if ctmAlertCat == "infrastructure":
                pass
            else:
                if ctmRunCounter == None:
                    ctmRunCounter = 0
                elif len(ctmRunCounter) < 1:
                    ctmRunCounter = 0
                else:
                    ctmRunCounter = int(ctmRunCounter)

            # logger.debug('CMT Alert JSON Raw: %s', jCtmAlertRaw)
            # logger.debug('CMT Alert JSON Formatted: %s', jCtmAlert)

            if _localDebugData:
                # sCtmAlert = w3rkstatt.jsonTranslateValues(data=jCtmAlert)
                sCtmAlert = json.dumps(jCtmAlert)
                logger.info('CMT QA Alert JSON Raw: %s', jCtmAlertRaw)
                logger.info('')
                logger.info('CMT QA Alert JSON Format 01: %s', jCtmAlert)
                logger.info('')
                logger.info('CMT QA Alert JSON Format 02: %s', sCtmAlert)
                logger.info('')
                logger.info('CTM QA Alert ID: %s', ctmAlertId)
                logger.info('CTM QA Alert Type: "%s"', ctmEventType)
                logger.info('CTM QA Alert Category: "%s"', ctmAlertCat)
                logger.info('CTM QA Job Datacenter: %s', ctmDataCenter)
                logger.info('CTM QA Job ID: %s', ctmOrderId)
                logger.info('CTM QA Run Counter: %s', ctmRunCounter)
                logger.info('CTM QA Alert Call: "%s"', ctmAlertCallType)

                logger.info('')
                jCtmAlertRawTemp = jCtmAlertRaw.replace('null', 'None')
                logger.info('CMT QA Alert JSON Format 03: %s', jCtmAlertRawTemp)
                logger.info('')

            # xAlert ID
            if not ctmAlertId:
                ctmAlertId = str(
                    w3rkstatt.getJsonValue(path="$.Serial", data=jCtmAlert)).strip()

            # CTM Login
            try:
                ctmApiObj = ctm.getCtmConnection()
                ctmApiClient = ctmApiObj.api_client
                _ctmActiveApi = True
            except:
                _ctmActiveApi = False
                ctmApiClient = None
                logger.error('CTM Login Status: %s', _ctmActiveApi)

            # Analyze alert
            ctmAlertDataFinal = {}
            if ctmAlertCat == "infrastructure":
                ctmAlertDataFinal = analyzeAlert4Infra(raw=jCtmAlertRaw, data=jCtmAlert)
                fileStatus, ctmAlertFileName = writeAlertFile(data=ctmAlertDataFinal, alert=ctmAlertId, type="infra")

                # Update CTM Alert staus if file is written
                if _ctmActiveApi and fileStatus:
                    sAlertNotes = "Alert File: '" + ctmAlertFileName + "'"
                    ctmAlertSev = "Normal"
                    ctmAlertsStatus = ctm.updateCtmAlertCore(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertComment=sAlertNotes,
                        ctmAlertUrgency=ctmAlertSev)   

                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")                    

                    if _localDebug:
                        logger.debug('CTM Alert Update Status: "%s"', ctmAlertsStatus)

            elif ctmAlertCat == "job":
                ctmAlertDataFinal = analyzeAlert4Job(ctmApiClient=ctmApiClient, raw=jCtmAlertRaw, data=jCtmAlert)
                fileStatus, ctmAlertFileName = writeAlertFile(data=ctmAlertDataFinal, alert=ctmAlertId, type="job")

                if ctmOrderId == "00000" and ctmRunCounter == 0:
                    # do not create file
                    fileStatus = True
                    if _ctmActiveApi:
                        sAlertNotes = "Alert File: '" + ctmAlertFileName + "'"
                        ctmAlertSev = "Normal"
                        ctmAlertsStatus = ctm.updateCtmAlertCore(
                            ctmApiClient=ctmApiClient,
                            ctmAlertIDs=ctmAlertId,
                            ctmAlertComment=sAlertNotes,
                            ctmAlertUrgency=ctmAlertSev)                        

                        ctmAlertsStatus = ctm.updateCtmAlertStatus(
                            ctmApiClient=ctmApiClient,
                            ctmAlertIDs=ctmAlertId,
                            ctmAlertStatus="Reviewed")

                        if _localDebug:                            
                            logger.debug('CTM Alert Update Status: "%s"', ctmAlertsStatus)
                else:
                    # Update CTM Alert staus if file is written
                    fileStatus, ctmAlertFileName = writeAlertFile(data=ctmAlertDataFinal, alert=ctmAlertId, type="job")

                if _ctmActiveApi and fileStatus:                   
                    sAlertNotes = "Alert File: '" + ctmAlertFileName + "'"
                    ctmAlertSev = "Normal"
                    ctmAlertsStatus = ctm.updateCtmAlertCore(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertComment=sAlertNotes,
                        ctmAlertUrgency=ctmAlertSev)

                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")

                    if _localDebug:
                        logger.debug('CTM Alert Update Status: "%s"',ctmAlertsStatus)

            else:

                ctmAlertDataFinal = analyzeAlert4Core(raw=jCtmAlertRaw, data=jCtmAlert)
                fileStatus, ctmAlertFileName = writeAlertFile(data=ctmAlertDataFinal, alert=ctmAlertId, type="core")

                # Update CTM Alert staus if file is written
                if _ctmActiveApi and fileStatus:
                    sAlertNotes = "Alert File: '" + ctmAlertFileName + "'"
                    ctmAlertSev = "Normal"
                    ctmAlertsStatus = ctm.updateCtmAlertCore(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertComment=sAlertNotes,
                        ctmAlertUrgency=ctmAlertSev)                 

                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")

                    if _localDebug:
                        logger.debug('CTM Alert Update Status: "%s"', ctmAlertsStatus)

            bhom_event_id = "BHOM-0000"
            if integration_bhom_enabled:
                # translate ctm alert to BHOM format
                # ctmAlertDataFinal = json.dumps(ctmAlertDataFinal)
                jBhomEvent = ctm.transformCtmBHOM(data=ctmAlertDataFinal,
                                                  category=ctmAlertCat)

                # future enhancements -> keep token for 24 hours
                authToken = bhom.authenticate()
                if authToken != None:
                    bhom_event_id = bhom.createEvent(token=authToken,
                                                     event_data=jBhomEvent)
                    time.sleep(10)
                    bhom_assigned_user = w3rkstatt.getJsonValue(
                        path="$.BHOM.user", data=jCfgData)
                    bhom.assignEvent(
                        token=authToken,
                        event_id=bhom_event_id,
                        assigned_user=bhom_assigned_user,
                        event_note="Control-M Alert Integration via: " +
                        hostFqdn)

                    time.sleep(10)
                    bhom_event_note = ctmAlertDataFinal
                    bhom.addNoteEvent(token=authToken,
                                      event_id=bhom_event_id,
                                      event_note=bhom_event_note)

                if _localDebugBHOM:
                    logger.debug('CTM BHOM: Event      : %s', jBhomEvent)
                    logger.debug('CTM BHOM: Event Note : "%s"',
                                 bhom_event_note)
                    logger.debug('CTM BHOM: Event ID   : %s', bhom_event_id)
                    logger.debug('CTM BHOM: Auth Token : %s', authToken)

                # update CTM Alert
                if _ctmActiveApi:
                    sAlertNotes = "Event: #" + bhom_event_id + "#" + ctmAlertFileName + "#"
                    ctmAlertSev = "Normal"
                    ctmAlertsStatus = ctm.updateCtmAlertCore(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertComment=sAlertNotes,
                        ctmAlertUrgency=ctmAlertSev)

                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")                        

            # Close cTM AAPI connection
            if _ctmActiveApi:
                ctm.delCtmConnection(ctmApiObj)
            if _localDebugData:
                logger.debug('CTM New Alert Processing: %s', "Done")
 
            sSysOutMsg = "Event: #" + str(ctmAlertId) + "#" + bhom_event_id + "#, Alert File: '" + ctmAlertFileName + "'"
            logger.info(sSysOutMsg)

        # Process only 'update' alerts
        if "Update" in ctmAlertCallType:
            if _localDebugData:
                logger.debug('- CTM Alert Update: "%s"', "Start")
                logger.debug('- CTM Alert Notes : "%s"', "ctmAlertNotes")
                logger.debug('- CTM Update Alert Processing: "%s"', "Nothing To do")

            sSysOutMsg = "Processed Update Alert: " + str(ctmAlertId)

    if _localInfo:
        logger.info('CTM: end event management - %s', w3rkstatt.sUuid)

    logging.shutdown()

    print(f"Message: {sSysOutMsg}")
