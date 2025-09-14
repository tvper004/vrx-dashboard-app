import argparse
from tqdm import tqdm
import time
import pandas as pd
import MitigationTime as mt
import cleanData as cd

import VickyState as state
import EndpointsEventTask as tasks
import EndpointVulnerabilities as vuln
import Endpoint as assets
import PatchsByAssets as patchs
import EndpointPublisherProductVersions as products
import IncidentsEvents as incidents
import EndpointGroups as groups
from datetime import datetime
import os
import sys


sys.setrecursionlimit(5000)

DEFAULT_QUERY_LIMIT_PER_MINUTE = 55

# Track the last time a query was made
last_query_time = 0

def control_rate(query_limit=None):
    global last_query_time

        # Use the default rate limit if none is provided
    if query_limit is None:
        query_limit = DEFAULT_QUERY_LIMIT_PER_MINUTE

    # Calculate the time since the last query
    elapsed_time = time.time() - last_query_time

    # If less than a minute has passed since the last query, wait
    if elapsed_time < 60:
        # Calculate the time to sleep based on the desired rate
        sleep_time = max(0, (60 / query_limit) - elapsed_time)
        time.sleep(sleep_time)

    # Update the last query time
    last_query_time = time.time()

parser = argparse.ArgumentParser(description='Args for VikyTopiaReport')
parser.add_argument('-k', '--api-key', dest='apiKey', action='store', required=True, help='Topia API key')
parser.add_argument('-d', '--dashboard', dest='dashboard', action='store', required=True, help='Url dashboard ex. https://xxxx.vicarius.cloud')
parser.add_argument('--allreports', dest='allreports', action='store_true', help='All Reports')
parser.add_argument('-a', '--assetsreport', dest='assetsreport', action='store_true', help='Assets Reports')
parser.add_argument('-t', '--taskreport', dest='tasksreport', action='store_true', help='Task Reports')
parser.add_argument('-v', '--vulnerabilitiesreport', dest='vulnreport', action='store_true', help='Vulnerabilities Reports')
parser.add_argument('-p', '--patchsreport', dest='patchsreport', action='store_true', help='Patchs Versions Reports')
parser.add_argument('-i', '--incidentvulnerability', dest='incidentvulreport', action='store_true', help='Vulnerabilities Reports')
parser.add_argument('-r', '--resetstate', dest='resetstate', action='store_true', help='Reset State')
parser.add_argument('-mt', '--mitigationtime', dest='mitigationtime', action='store_true', help='mitigation time')
parser.add_argument('-cd', '--cleandata', dest='cleandata', action='store_true', help='cleandata')
parser.add_argument('-u', '--updatestate', dest='updatestate', action='store_true', help='updatestate')



parser.add_argument('--version', action='version', version='1.0')

args = parser.parse_args()

# Get the Credentials
apikey = args.apiKey
urldashboard = args.dashboard

#Get the Stats and Reports Names
dictState = state.getState()
if dictState is None:
    print("state.json not found. Creating default state.")
    dictState = {
        "lastEndpointsEventTask": 0,
        "minDateIncidentEventVulnerabilities": 0,
        "reportNameEventsTasks": "reports/EndpointsEventTask.csv",
        "reportAssets": "reports/Endpoints.csv",
        "reportAssetsGroup": "reports/EndpointsGroup.csv",
        "reportEndpointGroups": "reports/EndpointsGroup.csv",
        "reportAssetsAttrributes": "reports/EndpointAttributes.csv",
        "reportAssetsExploitabilityRiskFactors": "reports/EndpointExploitabilityRiskFactors.csv",
        "reportAssetsScoresImpactRiskFactors": "reports/EndpointScoresImpactRiskFactors.csv",
        "reporIncidentEventVulnerabilities": "reports/EndpointIncidentesVulnerabilities.csv",
        "reportNameProducts": "reports/Products.csv",
        "reportNameVulnerabilities": "reports/Vulnerabilities.csv",
        "reportCountEndpointPatchs": "reports/EndpointCountPatchs.csv",
        "reportNameEndpointPatchs": "reports/EndpointPatchs.csv"
    }


def getAllEndpoitsTasks(fr0m,siz3,maxDate,minDate):
    print("minDate->"+str(minDate))
    print("maxDate->"+str(maxDate))
    """if lastdate == '0':
        head = "Taskid,AutomationId,AutomationName,Asset,TaskType,PublisherName,PathOrProduct,PathOrProductDesc,ActionStatus,MessageStatus,Username,CreateAt,UpdateAt\n"
        writeReport(dictState['reportNameEventsTasks'],head)"""
    
    strTasks, lastdate = "", 0  # Inicializar variables antes del try
    control_rate (50)

    try:
        strTasks, lastdate = tasks.getTasksEndopintsEvents(apikey,urldashboard,fr0m,siz3,maxDate,minDate)
    except Exception as e:
        # Las variables ya tienen un valor seguro, solo registramos el error
        print (f"An exception occurred: {e}")

    
    if len(strTasks) > 0:

        writeReport(dictState['reportNameEventsTasks'],strTasks)
        
        maxDate = str(lastdate)

        #dictState.update({'lastEndpointsEventTask': lastdate})
        
        #state.setState(dictState)

        getAllEndpoitsTasks(fr0m,siz3,maxDate,minDate)
        
    else:
        print("No event")
      


def getAllEndpoits(fr0m,siz3,count,pbar):
    control_rate(20)
    if fr0m == 0:
        head = "ID,HOSTNAME,HASH,SO,VERSION,endpointUpdatedAt\n"
        writeReport(dictState['reportAssets'],head)
    control_rate()
    strEndpoints = assets.getEndpoints(apikey,urldashboard,fr0m,siz3)
    writeReport(dictState['reportAssets'],strEndpoints)
    
    pbar.update(siz3)
    #time.sleep(0.25)

    fr0m += siz3

    if fr0m < count:
        dictState.update({'lastEndpoints': fr0m})
        state.setState(dictState)
        control_rate(20)
        getAllEndpoits(fr0m,siz3,count,pbar)

    else:
        pbar.update(siz3)
        time.sleep(0.25)
        
        dictState.update({'lastEndpoints': count})
        state.setState(dictState)     
        pbar.close()
        print("Done!")

def getAllEndpointsGroup(fr0m,siz3,count,pbar,endpointsGroups,groupName,searchQuery):
    control_rate(20)
    strEndpointGroups = groups.getAssetsbySearchQuery(apikey,urldashboard,searchQuery,fr0m,siz3)
    endpointsGroups += strEndpointGroups 
    
    pbar.update(siz3)
    

    fr0m += siz3

    if fr0m < count:
        control_rate(50)
        getAllEndpointsGroup(fr0m,siz3,count,pbar,endpointsGroups,groupName,searchQuery)

    else:
        writeReport(dictState['reportAssetsGroup'],groupName + "," + endpointsGroups + "\n")
        
        pbar.update(siz3)
        #time.sleep(0.25)
        pbar.close()
 
    
def getAllGroupsSearchs(fr0m,siz3,count,pbar,endpointsGroups):
    control_rate(50)
    strEndpointGroups = groups.getEndpointGroups(apikey,urldashboard,fr0m,siz3)
    endpointsGroups += strEndpointGroups
    #writeReport(dictState['reportAssetsGroup'],strEndpointGroups)
    
    pbar.update(siz3)
    time.sleep(0.25)

    fr0m += siz3

    if fr0m < count:
        control_rate(50)
        getAllGroupsSearchs(fr0m,siz3,count,pbar,endpointsGroups)

    else:
        pbar.update(siz3)
        time.sleep(0.25)
        pbar.close()
        print("Done!")
    
        # Obtain Asssets From GroupSearch
        head = "groupname,assets\n"
        writeReport(dictState['reportAssetsGroup'],head)

        lstGps = endpointsGroups.split("\n")

        for gp in lstGps:
            
            lstGp = gp.split("||")
            
            if len(lstGp) > 1:
                groupName = lstGp[0]
                searchQuery = lstGp[1]
                control_rate(20)
                groupscount = groups.getAssetsbySearchQueryCount(apikey,urldashboard,searchQuery)
                print(groupscount)

                fr0m = 0       
                
                if fr0m < groupscount:
                    endpointsGp = ""
                    with tqdm(total=groupscount,desc=groupName) as pbar:
                        control_rate()            
                        getAllEndpointsGroup(fr0m,siz3,groupscount,pbar,endpointsGp,groupName,searchQuery)
                else:
                    print("Done!")

def getAllEndpoitsExternalAttributes(fr0m,siz3,count,pbar):
    if fr0m == 0:
        head = "id,asset,attribute,value\n"
        writeReport(dictState['reportAssetsAttrributes'],head)
    
    control_rate()
    strEndpointsAttributes = assets.getEndpoitsExternalAttributes(apikey,urldashboard,fr0m,siz3)
    writeReport(dictState['reportAssetsAttrributes'],strEndpointsAttributes)
    
    pbar.update(siz3)
    #time.sleep(0.25)

    fr0m += siz3

    if fr0m < count:
        #dictState.update({'lastEndpoints': fr0m})
        #state.setState(dictState)
        control_rate()
        getAllEndpoitsExternalAttributes(fr0m,siz3,count,pbar)

    else:
        pbar.update(siz3)
        time.sleep(0.25)
        
        pbar.close()
        print("Done!")

def getAllEndpoitsExploitabilityRiskFactors(fr0m,siz3,count,pbar):
    if fr0m == 0:
        head = "id,asset,riskfactorterm,riskfactordescription\n"
        writeReport(dictState['reportAssetsExploitabilityRiskFactors'],head)

    strEndpointsAttributes = assets.getEndpointScoresExploitabilityRiskFactors(apikey,urldashboard,fr0m,siz3)
    writeReport(dictState['reportAssetsExploitabilityRiskFactors'],strEndpointsAttributes)
    
    pbar.update(siz3)
    time.sleep(0.25)

    fr0m += siz3

    if fr0m < count:
        getAllEndpoitsExploitabilityRiskFactors(fr0m,siz3,count,pbar)

    else:
        pbar.update(siz3)
        time.sleep(0.25)
        
        pbar.close()
        print("Done!")

def getAllEndpoitsScoresImpactRiskFactors(fr0m,siz3,count,pbar):
    if fr0m == 0:
        head = "id,asset,riskfactorterm,riskfactorscore\n"
        writeReport(dictState['reportAssetsScoresImpactRiskFactors'],head)

    strEndpointsAttributes = assets.getEndpointScoresImpactRiskFactors(apikey,urldashboard,fr0m,siz3)
    writeReport(dictState['reportAssetsScoresImpactRiskFactors'],strEndpointsAttributes)
    
    pbar.update(siz3)
    time.sleep(0.25)

    fr0m += siz3

    if fr0m < count:
        getAllEndpoitsScoresImpactRiskFactors(fr0m,siz3,count,pbar)

    else:
        pbar.update(siz3)
        time.sleep(0.25)
        
        pbar.close()
        print("Done!")

def getAllIncidentEventVulnerabilities(fr0m,siz3,incidenttype,minDate,maxDate):
    header = "assetid,asset,cve,severity,eventType,publisher,apporso,threatLevelId,vulV3exploitlevel,vulv3basescore,patchId,vulsummary,eventcreatedat,eventupdatedat,MitigatedEventDetectionDate\n"
    create_or_update_file(dictState['reporIncidentEventVulnerabilities'],header)

    print("minDate->"+minDate)
    print("maxDate->"+maxDate)

    time.sleep(3)
    jresponse = incidents.getIncidentEventsbyType(apikey,urldashboard,fr0m,siz3,incidenttype,minDate,maxDate) 

    if jresponse is None:
        print("jresponse is None, retrying in 10 seconds...")
        time.sleep(10)
        getAllIncidentEventVulnerabilities(fr0m,siz3,incidenttype,minDate,maxDate)
    
    # Check if the expected key exists and if it contains data
    elif 'serverResponseObject' in jresponse and len(jresponse['serverResponseObject']) > 0:
        strEventsVuln,minDate = incidents.parseIncidentEventsbyType(jresponse)
        minDate = str(minDate)
        dictState.update({'minDateIncidentEventVulnerabilities': int(minDate)})
        state.setState(dictState)
        writeReport(dictState['reporIncidentEventVulnerabilities'],strEventsVuln)
        print("Processing ->" + str(len(jresponse['serverResponseObject'])))
        getAllIncidentEventVulnerabilities(fr0m,siz3,incidenttype,minDate,maxDate)
        
    else:
        # This block now handles both the end of pagination and unexpected API responses
        if 'serverResponseObject' not in jresponse:
            print(f"Warning: Unexpected API response received. Halting incident report. Response: {jresponse}")
        else:
            print("No more incident events to process.")
    
def getAllEndpointsProductsVersions(fr0m,siz3,count,pbar):
    if fr0m == 0:
        head = "asset,productName,productRawEntryName,productVersion,publisherName,operatingSystemFamilyName,endpointId,productId\n"
        writeReport(dictState['reportNameProducts'],head)

    strProductsVersions = products.getEndpointPublisherProductVersions(apikey,urldashboard,fr0m,siz3)
    writeReport(dictState['reportNameProducts'],strProductsVersions)
    
    pbar.update(siz3)
    time.sleep(0.25)

    fr0m += siz3

    if fr0m < count:
        getAllEndpointsProductsVersions(fr0m,siz3,count,pbar)

    else:
        pbar.update(siz3)
        time.sleep(0.25)
 
        pbar.close()
        print("Done!")

def writeReport(reportName,strText):
    try:
        with open(reportName, 'a', encoding='UTF8') as report:
            report.write(strText)
        report.close()
    except:
        print("Somthing wrong with file")

def ReportTaskEvents():
    header = "Taskid,AutomationId,AutomationName,Asset,TaskType,PublisherName,PathOrProduct,PathOrProductDesc,ActionStatus,MessageStatus,Username,CreateAt,UpdateAt\n"
    create_or_update_file(dictState['reportNameEventsTasks'], header)
  
    time.sleep(3)
    dateNow = datetime.now()
    maxDate = str(int(float(dateNow.timestamp())*1000))
    minDate = str(dictState['lastEndpointsEventTask'])
    
    dictState.update({'lastEndpointsEventTask': int(maxDate)})
    state.setState(dictState)

    fr0m = 0
    siz3 = 100

    #set these variables for specific event time interval

    #maxDate = str(1709208000000)
    #minDate = str(1706788800000)

    getAllEndpoitsTasks(fr0m,siz3,maxDate,minDate)

def ReportProdctsVersions():
    productscount = products.getCountEndpointPublisherProductVersions(apikey,urldashboard)
    print("Products -> " + str(productscount))
    fr0m = 0       
    
    if fr0m < productscount:
        deltacount = productscount - fr0m
        with tqdm(total=deltacount,desc="ProductsVersions") as pbar:
            
            getAllEndpointsProductsVersions(fr0m,500,productscount,pbar)
    else:
        print("Done!")

def ReportEndpoints():
    control_rate(20)
    endpointcount = assets.getCountEndpoints(apikey,urldashboard)
    print("Endpoints -> " + str(endpointcount))
    fr0m = 0
    
    if fr0m < endpointcount:
        deltacount = endpointcount - fr0m
        with tqdm(total=deltacount,desc="Endpoints") as pbar:

            control_rate(20)
            getAllEndpoits(fr0m,500,endpointcount,pbar)
    else:
        print("Done!")

def ReportEndpointsAttributes():
    endpointattribcount = assets.getEndpoitsExternalAttributesCount(apikey,urldashboard)
    #print("EndpointsAttribs -> " + str(endpointattribcount))
    fr0m = 0       
    
    if fr0m < endpointattribcount:
        deltacount = endpointattribcount - fr0m
        with tqdm(total=deltacount,desc="Endpoints") as pbar:

            control_rate(20) 
            getAllEndpoitsExternalAttributes(fr0m,500,endpointattribcount,pbar)
    else:
        print("Done!")

def ReportEndpointScores():
    endpointcount = assets.getCountEndpoints(apikey,urldashboard)
    print("Endpoints -> " + str(endpointcount))
    fr0m = 0       
    
    if fr0m < endpointcount:
        deltacount = endpointcount - fr0m
        with tqdm(total=deltacount,desc="Endpoints") as pbar:            
            getAllEndpoitsScoresImpactRiskFactors(fr0m,500,endpointcount,pbar)
    else:
        print("Done!")

    if fr0m < endpointcount:
        deltacount = endpointcount - fr0m
        with tqdm(total=deltacount,desc="Endpoints") as pbar:            
            getAllEndpoitsExploitabilityRiskFactors(fr0m,500,endpointcount,pbar)
    else:
        print("Done!")    

def ReportIncident():

    dateNow = datetime.now()
    maxDate = str(int(float(dateNow.timestamp())*1000000000))
    minDate = str(dictState['minDateIncidentEventVulnerabilities'])
    incidenttype = "MitigatedVulnerability,DetectedVulnerability"



    fr0m = 0
    siz3 = 500

    #set these variables for specific event time interval

    #maxDate = str(1709251199000000000)
    #minDate = str(1706745600000000000)

    getAllIncidentEventVulnerabilities(fr0m,siz3,incidenttype,minDate,maxDate)

def SearchGroupsbyEndpoint(endpoint,dfg):
    # filter the dataframe to only include rows where the "assetname" column contains a certain string
    assetname_filter = dfg['assets'].str.contains(endpoint+'|',regex=False)
    df_filtered = dfg[assetname_filter]

    # extract the "groupname" column from the filtered dataframe
    groupname_series = df_filtered['groupname']

    # convert the groupname series to a list
    groupname_list = groupname_series.tolist()

    # create a string with groups
    my_string = "AllAssets|" + '|'.join(groupname_list)
    
    return my_string

def getAllEndpointsVulnerabilities(fr0m,siz3,minDate,maxDate,endpointName,endpointHash,endpointGroups):
   #time.sleep(1)  # Ensure rate limit is not exceeded
    try:
        control_rate()
        jresponse = vuln.getEndpointVulnerabilities(apikey, urldashboard, fr0m, siz3, minDate, maxDate, endpointName, endpointHash)
        
        # Check for valid response and if there is data to process
        if jresponse and 'serverResponseCount' in jresponse and jresponse['serverResponseCount'] > 0:
            control_rate()  # Control rate before making another query
            # The maxDate is not used for pagination here, so we can ignore it.
            strVulnerabilities, _ = vuln.parseEndpointVulnerabilities(jresponse, endpointGroups)
            writeReport(dictState['reportNameVulnerabilities'], strVulnerabilities)

            # If the number of results equals the page size, there might be more pages.
            if jresponse['serverResponseCount'] >= siz3:
                # Recursive call to get the next page of results.
                # BUG FIX: Increment 'fr0m' for pagination to avoid infinite recursion.
                getAllEndpointsVulnerabilities(fr0m + siz3, siz3, minDate, maxDate, endpointName, endpointHash, endpointGroups)
        elif jresponse and 'serverResponseCount' not in jresponse:
            # Handle unexpected API response structure
            print(f"Warning: Unexpected API response for endpoint {endpointName}. Response: {jresponse}")

    except Exception as e:
        # Handle errors/log here
        print (e)

def ReportVunerabilities():
    try:
        df = pd.read_csv(dictState['reportAssets'])
        if df.empty:
            print("Asset report is empty. Skipping vulnerabilities report.")
            return
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print(f"Warning: Asset report '{dictState['reportAssets']}' not found or is empty. Skipping vulnerabilities report.")
        return

    try:
        dfg = pd.read_csv(dictState['reportEndpointGroups'])
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print(f"Warning: Endpoint groups report '{dictState['reportEndpointGroups']}' not found or is empty. Group information will be missing.")
        # Create an empty dataframe with the expected column to avoid crashing SearchGroupsbyEndpoint
        dfg = pd.DataFrame(columns=['groupname', 'assets'])

    print(f"Total assets to process for vulnerabilities: {len(df.index)}")
    df = df.sort_values(by='endpointUpdatedAt', ascending=False)
    df = df.drop_duplicates(subset=['HOSTNAME'], keep='first')
    print(f"Unique assets to process: {len(df.index)}")

    fr0m = 0
    siz3 = 500

    head = "asset,assethash,group,productName,productRawEntryName,sensitivityLevelName,cve,vulnerabilityid,patchid,patchName,patchReleaseDate,createAt,updateAt,link,vulnerabilitySummary,V3BaseScore,V3ExploitabilityLevel\n"
    create_or_update_file(dictState['reportNameVulnerabilities'], head)

    dateNow = datetime.now()
    minDate = 0
    maxDate = str(int(float(dateNow.timestamp())*1000))

    try:
        with tqdm(total=len(df.index), desc="Endpoint Activities Vul") as pbar:
            for ind in df.index:
                endpointName = df['HOSTNAME'][ind]
                endpointHash = df['HASH'][ind]
                control_rate()
                endpointGroups = SearchGroupsbyEndpoint(endpointName, dfg)
                getAllEndpointsVulnerabilities(fr0m, siz3, minDate, maxDate, endpointName, endpointHash, endpointGroups)
                pbar.update(1)
    except Exception as e:
        print(f"An unexpected error occurred during ReportVunerabilities: {e}")

def getAllPatchsEndpoint(fr0m,siz3,endpointName,endpointSO,endpointGroups,totalPatchs):
    control_rate()
    strEndpointPatchs,tmpPatchs = patchs.getEndpointsPatchs(apikey,urldashboard,fr0m,siz3,endpointName,endpointSO,endpointGroups)

    totalPatchs += tmpPatchs

    if len(strEndpointPatchs) > 0:
        writeReport(dictState['reportNameEndpointPatchs'],strEndpointPatchs)        
    
    if tmpPatchs >= siz3:
        fr0m += siz3
        control_rate()
        getAllPatchsEndpoint(fr0m,siz3,endpointName,endpointSO,endpointGroups,totalPatchs)
    
    else:
        strcountendpointpatchs = endpointName + "," + str(totalPatchs) + "\n"
        writeReport(dictState['reportCountEndpointPatchs'],strcountendpointpatchs)


def ReportEndpointPatchs():
    # get the assets
    df = pd.read_csv(dictState['reportAssets'])
    #dduplication hostname
    df = df.drop_duplicates(subset=['HOSTNAME'], keep='first')

    # get Groups
    dfg = pd.read_csv(dictState['reportEndpointGroups'])

    fr0m = 0
    siz3 = 500

    strcountendpointpatchs = "Asset,TotalPactchs\n"
    writeReport(dictState['reportCountEndpointPatchs'],strcountendpointpatchs)

    strEndpointPatchs = "Asset,SO,PatchName,SeverityLevel,SeverityName,Description,PatchID\n"
    writeReport(dictState['reportNameEndpointPatchs'],strEndpointPatchs)

    with tqdm(total=len(df.index),desc="Endpoint Pacths") as pbar:            
        for ind in df.index:
            pbar.update()
            endpointHash = df['HASH'][ind]
            endpointName = df['HOSTNAME'][ind]
            endpointSO = df['SO'][ind]  
            control_rate()          
            endpointGroups = SearchGroupsbyEndpoint(endpointName,dfg)
            # BUG FIX: Reset totalPatchs for each endpoint to count them correctly.
            totalPatchs = 0
            control_rate()
            getAllPatchsEndpoint(fr0m,siz3,endpointName,endpointSO,endpointGroups,totalPatchs)

        pbar.close()

def ReportGroupsSearchs():
    control_rate(20)
    groupscount = groups.getEndpointGroupsCount(apikey,urldashboard)
    print("Endpoints Groups-> " + str(groupscount))
    fr0m = 0       
    
    if fr0m < groupscount:
        #deltacount = endpointcount - fr0m
        endpointsGroups = ""
        with tqdm(total=groupscount,desc="EndpointGroups") as pbar:
            control_rate(20)            
            getAllGroupsSearchs(fr0m,500,groupscount,pbar,endpointsGroups)
    else:
        print("Done!")

def resetState():
    dictState.update({'lastEndpointVulnerabilities': 0})
    dictState.update({'lastEndpoints':0})
    dictState.update({'lastEndpointsEventTask':0})
    dictState.update({'lastProductVersions':0})
    dictState.update({'lastPatchsEndpoint':0})
    dictState.update({'minDateIncidentEventVulnerabilities':0}) #minDateIncidentEventVulnerabilities
    dictState.update({'lastIncidentEventVulnerabilities':0})    
    state.setState(dictState)
    print("Done!")

def updateState():
    lastEndpointsEventTask = cd.getLastEndpointsEventTask ()
    minDateIncidentEventVulnerabilities = cd.getLastIncidentEventVulnerabilities ()
    dictState.update({'lastEndpointVulnerabilities': 0})
    dictState.update({'lastEndpoints':0})
    dictState.update({'lastEndpointsEventTask': lastEndpointsEventTask})
    dictState.update({'lastProductVersions':0})
    dictState.update({'lastPatchsEndpoint':0})
    dictState.update({'minDateIncidentEventVulnerabilities': minDateIncidentEventVulnerabilities}) #minDateIncidentEventVulnerabilities
    dictState.update({'lastIncidentEventVulnerabilities':0})    
    state.setState(dictState)
    print("Done!")

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"{file_path} file deleted ok.")
    else:
        print(f"{file_path} no file found, create a new")

def create_or_update_file(file_path, header):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as textfile:
            textfile.write(header)
        print(f"created {file_path}.")
    else:
        print()

def main():
    args.dashboard    
    if args.allreports:
        delete_file('reports/MitigationTime.csv')
        delete_file('reports/EndpointIncidentesVulnerabilitiesND.csv')
        delete_file('reports/VulnerabilitiesND.csv')
        delete_file('reports/EndpointCountPatchs.csv')
        delete_file('reports/EndpointPatchs.csv')
        delete_file('reports/Vulnerabilities.csv')
        delete_file('reports/EndpointsGroup.csv')
        delete_file('reports/Endpoints.csv')
        
        ReportEndpoints()
        ReportGroupsSearchs()
        ReportTaskEvents()
        ReportVunerabilities()
        ReportEndpointPatchs()
        ReportIncident()
        cd.cleanData()
        mt.get_mitigation_time()
        
    
    elif args.assetsreport:
        ReportEndpoints()
        #ReportEndpointsAttributes()
        #ReportEndpointScores()        
        #ReportGroupsAtrributesTags()
        ReportGroupsSearchs()
    
    elif args.tasksreport:
        ReportTaskEvents()

    elif args.vulnreport:
        ReportVunerabilities()        

    elif args.patchsreport:
        ReportEndpointPatchs()

    elif args.incidentvulreport:
        ReportIncident()
   
    elif args.resetstate:
        resetState()
    elif args.mitigationtime:
        mt.get_mitigation_time()
    
    elif args.cleandata:
        cd.cleanData()
    
    elif args.updatestate:
        updateState ()

    else:
        print("Select one report and try again!!!")

if __name__ == '__main__':
    main()