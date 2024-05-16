#!/usr/bin/env python3
# Filename: core_excel.py
"""
(c) 2022 Volker Scheithauer
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

w3rkstatt Python BMC Helix Operation Manager [BHOM] Integration


Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20230600      Volker Scheithauer    Initial Development


See also: 
"""

import os
import json
import logging
import requests
import urllib3
import time
import datetime
import sys
import getopt
import openpyxl
import subprocess
import pandas as pd



# handle dev environment vs. production
try:
    import w3rkstatt as w3rkstatt
except:
    # fix import issues for modules
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstat
    
# Define global variables from w3rkstatt.ini file
# Get configuration from bmcs_core.json
jCfgData = w3rkstatt.getProjectConfig()
cfgFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",
                                   data=jCfgData)
logFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder", data=jCfgData)
tmpFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",
                                   data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",
                                    data=jCfgData)

# Assign module defaults
_modVer = "20.23.06.00"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
# _localDebug = jCfgData["EXCEL"]["debug"]
_localInfo = True
logger = w3rkstatt.logging.getLogger(__name__)
logFile = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file", data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)
domain = w3rkstatt.getHostDomain(w3rkstatt.getHostFqdn(hostName))    

def getFilenameFromArguments(arguments):
    filename = None
    for index, arg in enumerate(arguments):
        if arg == "--file" and index + 1 < len(sys.argv):
            filename = arguments[index + 1]
            break

    return filename


def procssessExcel(filename, worksheet):
    try:
        # Read the Excel spreadsheet
        df = pd.read_excel(filename, sheet_name=worksheet)

        # Iterate over each row in the dataframe
        for index, row in df.iterrows():
            # Extract the values from the row
            id = row['ID']
            company = row['Company']
            title = row['Title']
            first_name = row['First Name']
            last_name = row['Last Name']
            email = row['E-Mail']
            phone = row['Phone']
            specialty = row['Specialty']
            status = row['Status']

            # Execute a command per entry (example command)
            command = f"echo 'ID: {id}, Company: {company}, Title: {title}, First Name: {first_name}, Last Name: {last_name}, E-Mail: {email}, Phone: {phone}, Specialty: {specialty}, Status: {status}'"
            # Replace the above command with your desired command

            # Execute the command
            import subprocess
            subprocess.run(command, shell=True)

        print("Execution completed.")

    except FileNotFoundError:
        print("File not found.")

    except pd.errors.SheetNameError:
        print("Sheet 'Customers' not found in the Excel file.")
        

if __name__ == "__main__":
    logging.basicConfig(filename=logFile,
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')

    # Extract script arguments
    sArguments = sys.argv[1:]
    
    if len(sArguments) >= 2:
        sFilename = getFilenameFromArguments(arguments=sArguments)
        sFileStatus = w3rkstatt.getFileStatus(path=sFilename)
        
    if _localInfo:
        logger.info('CTM: start event management - %s', w3rkstatt.sUuid)
        logger.info('Version: %s ', _modVer)
        logger.info('System Platform: %s ', w3rkstatt.sPlatform)
        logger.info('Log Level: %s', loglevel)
        logger.info('Epoch: %s', epoch)
        logger.info('Host Name: %s', w3rkstatt.sHostname)
        logger.info('File Name: %s', sFilename)
        logger.info('File Status: %s', sFileStatus)
        logger.info('UUID: %s', w3rkstatt.sUuid)

   
    procssessExcel(filename=sFilename, worksheet="Customers")
  


logging.shutdown()
print(f"Version: {_modVer}")
