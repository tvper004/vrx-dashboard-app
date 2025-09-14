# Description: This script calculates the mitigation time for each mitigated vulnerability event, from EndPointIncidentesVulnerabilities.csv report.

import pandas as pd


def get_mitigation_time():
        events_report_path = f'reports\\EndpointIncidentesVulnerabilitiesND.csv'
        mitigation_report_path = f'reports\\MitigationTime.csv'
        df = pd.read_csv(events_report_path, encoding='utf-8')
        df['eventcreatedat'] = pd.to_numeric(df['eventcreatedat'], errors='coerce', downcast='integer')
        df['eventupdatedat'] = pd.to_numeric(df['eventupdatedat'], errors='coerce', downcast='integer')
        df['MitigatedEventDetectionDate'] = pd.to_numeric(df['MitigatedEventDetectionDate'], errors='coerce', downcast='integer')
        #df['vulsummary'] = df['vulsummary'].astype(str).apply(clean_vulsummary)
        df['vulsummary'] = ''

        df.rename(columns={'eventcreatedat': 'mitigation_date'}, inplace=True)
        df.rename(columns={'MitigatedEventDetectionDate': 'detection_date'}, inplace=True)

        mitigated_events = df[df['eventType'] == 'MitigatedVulnerability'].sort_values(by='mitigation_date', ascending=False)
        mitigated_events['mitigation_time'] = mitigated_events.apply(lambda row: (row['mitigation_date'] - row['detection_date']) / (1000 * 3600 * 24) 
                                        if pd.notnull(row['mitigation_date']) and pd.notnull(row['detection_date']) 
                                        else None, axis=1)

        mitigated_events.to_csv(mitigation_report_path, index=False)


