# DrugConflator

## Description
The goal of this repository is to develop a tool to identify "essentially the same" drugs based on the drug information (e.g., ingredients, brand name, drug components, clinical groups) provided by [RxNav](https://mor.nlm.nih.gov/RxNav/) Service. For any given drug curie, this tool can return all RXCUI identifiers related to this curie. When drugs have certian amount of overlapping RXCUI identifiers, they are considered as "essentially the same". Based on the overlapping RXCUI identifiers, this tool can tell whether two given drug curies should be conflated together or not based on a specific threshold.

The process to find the RXCUI identifiers for a curie is as follows
 1. Find all equivalent curies and names of a given curie using both [node normalizer](https://github.com/TranslatorSRI/NodeNormalization) and [node synnoymizer](https://github.com/RTXteam/RTX/tree/master/code/ARAX/NodeSynonymizer).
 2. If the equivalent curies include the identifiers from ATC, Drugbank, GCN_SEQNO(NDDF), HIC_SEQN(NDDF), MESH, UNII_CODE(UNII), VUID(VANDF), we call [findRxcuiById](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiById.html) API to get the corresponding RXCUI identifiers. For each returned RXCUI ID, we collect all related RXCUI IDs from [RxNav](https://mor.nlm.nih.gov/RxNav/) Service according to ingredient, precise ingredient, brand name, clinical drug component, branded drug component, clinical drug or pack, branded drug or pack, clinical dose form group, and branded dose form group
 3. If the equivalent curies include the identifers from CHEMBL, UMLS, KEGG.DRUG, DRUGBANK, NCIT, CHEBI, VANDF, HMDB, DrugCentral, UNII, we call [mychem.info](https://mychem.info/) API to get the corresponding RXCUI identifiers.
 4. For each equivalent name, we leverage the [getApproximateMatch](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getApproximateMatch.html) API with `rank==1` to get the corresponding RXCUI identifiers (if can be turned off by setting `use_curie_name = False` in get_rxcui_results).

Given the RxCUI lists of two query cureis, we provide two metrics to determine how close they are:

- Jaccard Similarity
    $$
        JS(A, B) = |A ∩ B| / |A ∪ B|
    $$
- Max Containment
    $$
        MC(A, B) = |A ∩ B| / min(|A|, |B|)
    $$
where `A` is the RxCUI list of curie1 and `B` is the RxCUI list of curie2.


## Preparation

### Set up Running Environment
 1. Install conda following its [instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
 2. Build conda environment for this tool by running the following command:
    ```bash
    conda env create -f env.yml
    ```

### Download necessary databases
To use this tool, please download the node synonymizer database [node_synonymizer_v1.1_KG2.8.0.1.sqlite](https://pennstateoffice365-my.sharepoint.com/:u:/g/personal/cqm5886_psu_edu/EbVzSgyiIeRCumXtAeCnSPkBTr5_g9lQ8mukWo9y3JDBzQ?e=yAXxsg), and then put it under a folder named `data`:
```bash
mkdir data
## download node_synonymizer_v1.1_KG2.8.0.1.sqlite
mv node_synonymizer_v1.1_KG2.8.0.1.sqlite ./data
```

## How to run the tool
Here, we provide an example `PUBCHEM.COMPOUND:38072` to illustrate some useful methods:
```python
from drugconflator_new import DrugConflator

## Query drug curie
query_curie = "PUBCHEM.COMPOUND:38072"

## Set up drug conflator class
dc = DrugConflator()

## Get equivalent curies and names for query drug curie
equivalent_curies_and_names = dc.get_equivalent_curies_and_name(query_curie)
## equivalent curies
equivalent_curies_and_names[0]
## equivalent names
equivalent_curies_and_names[1]

## Extract RXCUI IDs from RXNAV database and MyChem database
dc.get_rxcui_results(query_curie) # By default, it queries both curie id and name from both RXNAV and MyChem databases

## use the curie id only for querying
dc.get_rxcui_results(query_curie, use_curie_name = False)
## use the curie name only for querying
dc.get_rxcui_results(query_curie, use_curie_id = False)
## use RXNAV database only for querying
dc.get_rxcui_results(query_curie, use_mychem = False)
## use MyChem database only for querying
dc.get_rxcui_results(query_curie, use_rxnav = False)

## Given two curies, tell if they are "essentailly the same"
dc.are_conflated("CHEMBL.COMPOUND:CHEMBL25", "CHEBI:15365", method = 'js') # Use jaccard similarity
dc.are_conflated("CHEMBL.COMPOUND:CHEMBL25", "CHEBI:15365", method = 'js', threshold = 0.5, return_format='boolean') # Use jaccard similarity and return a boolean value based on threshold 0.5
dc.are_conflated("CHEMBL.COMPOUND:CHEMBL25", "CHEBI:15365", method = 'mc') # Uese max containment
dc.are_conflated("CHEMBL.COMPOUND:CHEMBL25", "CHEBI:15365", method = 'mc', threshold = 0.5, return_format='boolean') # Use max containment and return a boolean value based on threshold 0.5

```