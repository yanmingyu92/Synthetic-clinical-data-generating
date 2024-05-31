from xport import Reader
import pandas as pd

def parse_xpt(file_path):
    with open(file_path, 'rb') as file:  # Use context manager to automatically close file
        reader = Reader(file)  
        df = pd.DataFrame(list(reader))  # Create DataFrame from records

    return df.to_dict('records') 

adsl_records = parse_xpt('/workspaces/Synthetic-clinical-data-generating/data/adsl.xpt')
adae_records = parse_xpt('/workspaces/Synthetic-clinical-data-generating/data/adae.xpt')
adlb_records = parse_xpt('/workspaces/Synthetic-clinical-data-generating/data/adlbc.xpt')

import pandas as pd

def transform_records(records):
    df = pd.DataFrame(records)
    return df

adsl_df = transform_records(adsl_records)
adae_df = transform_records(adae_records)
adlb_df = transform_records(adlb_records)

from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "411104"))

def create_subject_nodes(tx, subjects):
    query = """
    UNWIND $subjects AS subject
    MERGE (s:Subject {USUBJID: subject.USUBJID})
    """
    tx.run(query, subjects=subjects)

def create_adsl_nodes(tx, adsl_records):
    query = """
    UNWIND $records AS record
    MATCH (s:Subject {USUBJID: record.USUBJID})
    CREATE (a:ADSLRecord {USUBJID: record.USUBJID, STUDYID: record.STUDYID, AGE: toInteger(record.AGE), RACE: record.RACE, SEX: record.SEX, TRT01P: record.TRT01P})
    CREATE (s)-[:HAS_ADSL]->(a)
    """
    tx.run(query, records=adsl_records)

def create_adae_nodes(tx, adae_records):
    query = """
    UNWIND $records AS record
    MATCH (s:Subject {USUBJID: record.USUBJID})
    CREATE (e:ADAERecord {USUBJID: record.USUBJID, AETERM: record.AETERM, AEDECOD: record.AEDECOD, AESTDTC: record.AESTDTC})
    CREATE (s)-[:HAS_ADAE]->(e)
    """
    tx.run(query, records=adae_records)

def create_adlb_nodes(tx, adlb_records):
    query = """
    UNWIND $records AS record
    MATCH (s:Subject {USUBJID: record.USUBJID})
    CREATE (l:ADLBRecord {USUBJID: record.USUBJID, PARAM: record.PARAM, LBSTRESN: toFloat(record.LBSTRESN), LBSTNRLO: toFloat(record.LBSTNRLO), LBSTNRHI: toFloat(record.LBSTNRHI)})
    CREATE (s)-[:HAS_ADLB]->(l)
    """
    tx.run(query, records=adlb_records)

with driver.session() as session:
    # Create Subject nodes
    unique_subjects = adsl_df[['USUBJID']].drop_duplicates().to_dict('records')
    session.write_transaction(create_subject_nodes, unique_subjects)
    
    # Create ADSL nodes and relationships
    adsl_records = adsl_df.to_dict('records')
    session.write_transaction(create_adsl_nodes, adsl_records)
    
    # Create ADAE nodes and relationships
    adae_records = adae_df.to_dict('records')
    session.write_transaction(create_adae_nodes, adae_records)
    
    # Create ADLB nodes and relationships
    adlb_records = adlb_df.to_dict('records')
    session.write_transaction(create_adlb_nodes, adlb_records)
