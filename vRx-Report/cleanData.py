# %%
import pandas as pd

def cleanData():

    chunk_size = 10**6  # Adjust as needed
    try:
        # load Vulnerabilties.csv file to dataframe 
        vulnerabilties_df = pd.read_csv('reports/Vulnerabilities.csv')
        # delete duplicates rows based on assethas and cve
        vulnerabilties_df.drop_duplicates(subset=['assethash', 'cve'], keep='first', inplace=True)
        vulnerabilties_df.to_csv('reports/VulnerabilitiesND.csv', index=False)
        print("Cleaned Vulnerabilities report generated.")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print("Warning: Could not clean Vulnerabilities.csv. File not found or is empty.")
    except Exception as e:
        print(f"An unexpected error occurred while cleaning Vulnerabilities.csv: {e}")

    try:
        # load EndpointIncidentesVulnerabilities.csv file to dataframe
        chunk_size = 10**6  # Adjust as needed
        
        chunks = pd.read_csv('reports/EndpointIncidentesVulnerabilities.csv', iterator=True, chunksize=chunk_size, dtype={'column1': 'int64', 'column2': 'object', 'column3': 'object', 'column4': 'object', 'column5': 'object', 'column6': 'object', 'column7': 'object', 'column8': 'int64', 'column9': 'float64', 'column10': 'float64', 'column11': 'int64', 'column12': 'object', 'column13': 'int64', 'column14': 'int64'})

        events_df = pd.concat(chunks, ignore_index=True)

        if not events_df.empty:
            # assing to events_df the following column names "assetid", "asset", "cve", "severity", "eventType", "publisher", "apporso", "threatLevelId", "vulV3exploitlevel", "vulv3basescore", "patchId", "vulsummary", "eventcreatedat", "eventupdatedat", "MitigatedEventDetectionDate"
            events_df.columns = ["assetid", "asset", "cve", "severity", "eventType", "publisher", "apporso", "threatLevelId", "vulV3exploitlevel", "vulv3basescore", "patchId", "vulsummary", "eventcreatedat", "eventupdatedat", "MitigatedEventDetectionDate"]

            # create a new events_df_nd dataframe and filter rows that have assetid that are contained in endpoints_df ID column
            #events_df_nd = events_df[events_df['assetid'].isin(endpoints_df['ID'])]
            events_df.drop_duplicates(subset=["assetid", "asset", "cve", "eventType", "publisher", "apporso", "eventcreatedat", "eventupdatedat"], keep='first', inplace=True)

            events_df.to_csv('reports/EndpointIncidentesVulnerabilitiesND.csv', index=False)
            print("Cleaned EndpointIncidentesVulnerabilities report generated.")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print("Warning: Could not clean EndpointIncidentesVulnerabilities.csv. File not found or is empty.")
    except Exception as e:
        print(f"An unexpected error occurred while cleaning EndpointIncidentesVulnerabilities.csv: {e}")


def getLastIncidentEventVulnerabilities ():
    try :
        chunk_size = 10**6  # Adjust as needed
        chunks = pd.read_csv('reports/EndpointIncidentesVulnerabilities.csv', iterator=True, chunksize=chunk_size, on_bad_lines='skip')
        events_df = pd.concat(chunks, ignore_index=True)
        # assing to events_df the following column names "assetid", "asset", "cve", "severity", "eventType", "publisher", "apporso", "threatLevelId", "vulV3exploitlevel", "vulv3basescore", "patchId", "vulsummary", "eventcreatedat", "eventupdatedat"
        # events_df.columns = ["assetid", "asset", "cve", "severity", "eventType", "publisher", "apporso", "threatLevelId", "vulV3exploitlevel", "vulv3basescore", "patchId", "vulsummary", "eventcreatedat", "eventupdatedat"]
        return int (events_df['eventcreatedat'].max() * 1000000)
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
        print("Warning: Could not get last incident event date. File not found, is empty, or has no valid dates.")
        return 0
  

def getLastEndpointsEventTask () :
    try :
        chunk_size = 10**6  # Adjust as needed
        chunks = pd.read_csv('reports/EndpointsEventTask.csv', iterator=True, chunksize=chunk_size, on_bad_lines='skip')
        tasks_df = pd.concat(chunks, ignore_index=True)
        return int (tasks_df['CreateAt'].max())
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
        print("Warning: Could not get last task event date. File not found, is empty, or has no valid dates.")
        return 0
