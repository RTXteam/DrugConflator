# DrugConflator
Tool to find the "essential drug" corresponding to any biolink:ChemicalEntity

The process to find the RXCUI for a curie is as follows
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
