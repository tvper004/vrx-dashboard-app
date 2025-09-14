#Author: Joaldir Rani

import requests
import json
import utils

def getCountEvents(apikey,urldashboard,lastdate):
    headers = {
        'Accept': 'application/json',
        'Vicarius-Token': apikey,
    }

    params = {
        'from': 0,
        'size': 1,
        'sort' : '-analyticsEventCreatedAt',
        'q':'analyticsEventCreatedAt>' + str(lastdate),
    }

    response = requests.get(urldashboard + '/vicarius-external-data-api/taskEndpointsEvent/count', params=params, headers=headers)
    jsonresponse = json.loads(response.text)
    responsecount = jsonresponse['serverResponseCount']

    return responsecount
    
def getTasksEndopintsEvents(apikey,urldashboard,fr0m,siz3,maxdate,mindate):
    headers = {
        'Accept': 'application/json',
        'Vicarius-Token': apikey,
    }

    params = {
        #'includeFields': 'taskEndpointsEventOrganizationEndpointPatchPatchPackages;taskEndpointsEventEndpoint.endpointName;taskEndpointsEventTask;analyticsEventCreatedAt;analyticsEventUpdatedAt',
        'from': fr0m,
        'size': siz3,
        'sort' : '-analyticsEventCreatedAt',
        'q':'analyticsEventCreatedAt>' + mindate + ';analyticsEventCreatedAt<' + maxdate,
    }
    
    response = requests.get(urldashboard + '/vicarius-external-data-api/taskEndpointsEvent/filter', params=params, headers=headers)
    parsed = json.loads(response.text)

    strTasks = ""
    lastdate = 0

    if 'serverResponseObject' in parsed and parsed['serverResponseObject']:
        for i in parsed['serverResponseObject']:
            try:
                try:
                    automationName = i['taskEndpointsEventTask']['taskAutomation']['automationName']
                    automationId = i['taskEndpointsEventTask']['taskAutomation']['automationId']
                except:
                    automationName = ""
                    automationId = ""

                
                taskid = i['taskEndpointsEventTask']['taskId']
                asset = i['taskEndpointsEventEndpoint']['endpointName']
                
                try:
                    username = i['taskEndpointsEventTask']['taskUser']['userFirstName']
                    username = username + " " + i['taskEndpointsEventTask']['taskUser']['userLastName']
                except:
                    username=""
                
                try:
                    taskType = i['taskEndpointsEventTask']['taskTaskType']['taskTypeName']
                except:
                    taskType = ""

                try:
                    publisherName = i['taskEndpointsEventTask']['taskPublisher']['publisherName']
                except:
                    publisherName = ""

                pathproduct = ""
                pathproductdesc = ""

                if 'taskPatch' in i['taskEndpointsEventTask']:
                    if 'patchName' in i['taskEndpointsEventTask']['taskPatch']:            
                        pathproduct = i['taskEndpointsEventTask']['taskPatch']['patchName']
                        try:
                            pathproductdesc = i['taskEndpointsEventTask']['taskPatch']['patchDescription']
                        except KeyError:
                            pathproductdesc = ""
                else:
                    pathproduct = ""
                    pathproductdesc = ""


                if 'taskProduct' in i['taskEndpointsEventTask']:
                    if 'productName' in i['taskEndpointsEventTask']['taskProduct']:
                        try:
                            pathproduct = i['taskEndpointsEventTask']['taskProduct']['productName']
                        except KeyError:
                            pathproduct = ""
                else:
                    pathproduct = ""


                if 'ApplyPublisherOperatingSystemVersionsPatchs' in taskType:
                    pathproduct = i['taskEndpointsEventTask']['taskOperatingSystem']['operatingSystemName']
                
                if 'ActivateTopia' in (i['taskEndpointsEventTask']['taskTaskType']['taskTypeName']):
                    actionStatus = taskType
                    messageStatus = ""
                

                else:
                    try:
                        actionStatus = i['taskEndpointsEventOrganizationEndpointPatchPatchPackages']['organizationEndpointPatchPatchPackagesActionStatus']['actionStatusName']
                        messageStatus = i['taskEndpointsEventOrganizationEndpointPatchPatchPackages']['organizationEndpointPatchPatchPackagesStatusMessage']
                    except:
                        actionStatus = ""
                        messageStatus = ""
                
                if 'RunScript' in (i['taskEndpointsEventTask']['taskTaskType']['taskTypeName']):
                    # set actionstatus to taskTaskStatus taskStatusName
                    try:
                        messageStatus = i['taskEndpointsEventOrganizationEndpointTaskScriptTemplateCommandAbs']['organizationEndpointTaskOrganizationScriptTemplatesOutput'] 
                    except:
                        messageStatus = ''
                    actionStatus = i['taskEndpointsEventTask']['taskTaskStatus']['taskStatusName']
                    try:
                        pathproductdesc = i['taskEndpointsEventTask']['taskScriptTemplate']['organizationScriptTemplateName']
                    except:
                        pathproductdesc = ''
                    
                    
                createAt = i['analyticsEventCreatedAt']
                updateAt = i['analyticsEventUpdatedAt']

                pathproductdesc = pathproductdesc.replace("\r","").replace("\n",">>")
                pathproductdesc = pathproductdesc.replace('"',"").strip('\n')

                messageStatus = messageStatus.replace("\r","").replace("\n",">>")
                messageStatus = messageStatus.replace('"',"").strip('\n')
                
                strTasks += (str(taskid) + "," + str(automationId) + "," + automationName + "," + asset + "," + taskType + "," + publisherName + "," + pathproduct + ",\"" + pathproductdesc + "\"," + actionStatus + ",\"" + messageStatus + "\"," + username + "," + str(createAt) + "," + str(updateAt) + "\n")
                lastdate = i['analyticsEventCreatedAt']
            except Exception as e:
                print(f"Could not parse task event record. Error: {e}. Record: {i}")
                continue

    return strTasks,lastdate