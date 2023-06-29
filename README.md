# DrugConflator
The goal of this repository is to develop a tool to identify the "essentially the same" drugs based on the drug properties (e.g., ingredients, brand name, drug components, clinical groups) provided by [RxNav](https://mor.nlm.nih.gov/RxNav/) Service. For any given drug curie, this tool can return all RXCUI identifiers related to this curie. When drugs have certian amount of overlapping RXCUI identifiers, they are considered as "essentially the same".

The process to find the RXCUI identifiers for a curie is as follows
 1. Find all equivalent curies and names of a given curie using both [node normalizer](https://github.com/TranslatorSRI/NodeNormalization) and [node synnoymizer](https://github.com/RTXteam/RTX/tree/master/code/ARAX/NodeSynonymizer).
 2. If the equivalent curies include the identifiers from ATC, Drugbank, GCN_SEQNO(NDDF), HIC_SEQN(NDDF), MESH, UNII_CODE(UNII), VUID(VANDF), we call [findRxcuiById](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiById.html) API to get the corresponding RXCUI identifiers. For each returned RXCUI ID, we collect all related RXCUI IDs from [RxNav](https://mor.nlm.nih.gov/RxNav/) Service according to ingredient, precise ingredient, brand name, clinical drug component, brand component
 3. If the equivalent curies include the identifers from CHEMBL, UMLS, KEGG.DRUG, DRUGBANK, NCIT, CHEBI, VANDF, HMDB, DrugCentral, UNII, we call [mychem.info](https://mychem.info/) API to get the corresponding RXCUI identifiers.
 4. For each equivalent name, we leverage the [getApproximateMatch](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getApproximateMatch.html) API with `rank==1` to get the corresponding RXCUI identifiers.
     
1) Query the RXNORM SQLITE Database for RXCUI ID by querying the database with the curie
2) If RXCUI ID is not obtained by Step 1, MyChem.info API by querying the database with the curie
3) If RXCUI ID is not obtained by Step 2, using the node synonymizer, we get the english name and query the RXNORM Database with the english name
4) If RXCUI ID is not obtained by Step 3, Use the node normalizer and obtain alternate identifiers and repeat steps 1-3

#class DrugConflator contains the below methods
  - # create_drugmap_table:
    This is a classmethod which is used to create the drugmap table which will store the mappings between curies and rxcui
  - # insert_drugmap_table
    This is the insert method which is used to insert records into the drugmap table
  - # get_rxnorm_from_rxnav
    This method queries the RXNORM database located in the data/ folder with the curie. 
    Only certain types of curies can be directly queried on this database and if we are unable to query the database with the query, 
    the control of the program exits this method
    
  - # get_rxnorm_from_mychem
  - get_all_identifiers_from_node_normalizer
    This function queries the node normalizer to get alternate identifiers which we use to query all the above sources to get the RXCUI
  - # get_name_from_synonymizer
     This function gets the english name from the node synonymizer database and returns it.
