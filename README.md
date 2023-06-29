# DrugConflator

## Description
The goal of this repository is to develop a tool to identify the "essentially the same" drugs based on the drug properties (e.g., ingredients, brand name, drug components, clinical groups) provided by [RxNav](https://mor.nlm.nih.gov/RxNav/) Service. For any given drug curie, this tool can return all RXCUI identifiers related to this curie. When drugs have certian amount of overlapping RXCUI identifiers, they are considered as "essentially the same".

The process to find the RXCUI identifiers for a curie is as follows
 1. Find all equivalent curies and names of a given curie using both [node normalizer](https://github.com/TranslatorSRI/NodeNormalization) and [node synnoymizer](https://github.com/RTXteam/RTX/tree/master/code/ARAX/NodeSynonymizer).
 2. If the equivalent curies include the identifiers from ATC, Drugbank, GCN_SEQNO(NDDF), HIC_SEQN(NDDF), MESH, UNII_CODE(UNII), VUID(VANDF), we call [findRxcuiById](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiById.html) API to get the corresponding RXCUI identifiers. For each returned RXCUI ID, we collect all related RXCUI IDs from [RxNav](https://mor.nlm.nih.gov/RxNav/) Service according to ingredient, precise ingredient, brand name, clinical drug component, branded drug component, clinical drug or pack, branded drug or pack, clinical dose form group, and branded dose form group
 3. If the equivalent curies include the identifers from CHEMBL, UMLS, KEGG.DRUG, DRUGBANK, NCIT, CHEBI, VANDF, HMDB, DrugCentral, UNII, we call [mychem.info](https://mychem.info/) API to get the corresponding RXCUI identifiers.
 4. For each equivalent name, we leverage the [getApproximateMatch](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getApproximateMatch.html) API with `rank==1` to get the corresponding RXCUI identifiers.
     

# How to use this tool
To use this tool, you need to download the node synonymizer database `node_synonymizer_v1.1_KG2.8.0.1.sqlite` from [here](https://pennstateoffice365-my.sharepoint.com/:u:/g/personal/cqm5886_psu_edu/EbVzSgyiIeRCumXtAeCnSPkBTr5_g9lQ8mukWo9y3JDBzQ?e=yAXxsg), and then put it under a folder named `data`.


Here, we provide an example python code to use this tool below:
```python
from drugconflator_new import DrugConflator

## Test Examples
test_curies = ["CHEBI:15365", "RXNORM:1156278"]
## Set up drug conflator class
dc = DrugConflator()

## Extract the corresponding RXCUI ids for each test drug curies
result = [[curie, dc.get_rxcui_results(curie)] for curie in test_curies]
for item in result:
    print(f"query_curie: {item[0]}, rxcui: {item[1]}", flush=True)
```