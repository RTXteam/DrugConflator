import sqlite3
import json
import biothings_client
import requests


class DrugConflator:
    def __init__(self, node_synonymizer_path = "data/node_synonymizer_v1.1_KG2.8.0.1.sqlite", rxnav_url = "https://rxnav.nlm.nih.gov/REST", normalizer_url = 'https://nodenormalization-sri.renci.org/1.3'):
        self.my_chem_fields = ['unii']
        self.node_synonymizer_path = node_synonymizer_path
        self.normalizer_url = normalizer_url
        self.rxnav_url = rxnav_url
        self.mc = biothings_client.get_client("chem")

    def _get_all_equivalent_info_from_node_normalizer(self, curie):
        """
        This function calls the node normalizer and returns the equivalent identifiers and their names
        """

        body = {
                'curies': [
                    curie
                ],
                'conflate': "true"
                }
        headers = {'Content-Type':'application/json'}
        identifiers = []
        labels = []
        response = requests.post(url=f"{self.normalizer_url}/get_normalized_nodes", headers=headers, json=body)
        if response.status_code == 200:
            json_response = response.json()
            if json_response[curie]:
                for item in json_response[curie]['equivalent_identifiers']:
                    if 'identifier' in item and item['identifier'] and item['identifier'] != '':
                        identifiers.append(item['identifier'])
                    if 'label' in item and item['label'] and item['label'] != '':
                        labels.append(item['label'].lower())
                        
                return [list(set(identifiers)), list(set(labels))]
            else:
                return []
        else:
            return []

    def _get_all_equivalent_info_from_synonymizer(self, curie):
        """
        This function calls the node synnoymizer and returns the equivalent identifiers and their names
        """
        ns_con = sqlite3.connect(self.node_synonymizer_path)

        identifiers = []
        labels = []
        ns_cur = ns_con.cursor()                                 
        sql_query_template = f"""
                    SELECT N.id, N.cluster_id, N.name, N.category, C.name
                    FROM nodes as N
                    INNER JOIN clusters as C on C.cluster_id == N.cluster_id
                    WHERE N.id in ('{curie}')"""
        culster_ids = [x[1] for x in ns_cur.execute(sql_query_template).fetchall()]
        if len(culster_ids) > 0:
            if len(culster_ids) == 1:
                sql_query_template = f"""
                            SELECT N.id, N.cluster_id, N.name, N.category, C.name
                            FROM nodes as N
                            INNER JOIN clusters as C on C.cluster_id == N.cluster_id
                            WHERE N.cluster_id in ('{culster_ids[0]}')"""
            else:
                sql_query_template = f"""
                            SELECT N.id, N.cluster_id, N.name, N.category, C.name
                            FROM nodes as N
                            INNER JOIN clusters as C on C.cluster_id == N.cluster_id
                            WHERE N.cluster_id in {tuple(culster_ids)}"""
            res = ns_cur.execute(sql_query_template).fetchall()
            for item in res:
                identifiers.append(item[0])
                if item[2] and item[2] != '':
                    labels.append(item[2].lower())
                elif item[4] and item[4] != '':
                    labels.append(item[4].lower())
                else:
                    pass

            return [list(set(identifiers)), list(set(labels))]
        else:
            return []

    @staticmethod
    def _parse_rxcui_json(json_response):
        """
        Parse JSON response from rxnav API
        """
        selected_types = ['IN', 'MIN', 'PIN', 'BN', 'SCDC', 'SBDC', 'SCD', 'GPCK', 'SBD', 'BPCK', 'SCDG', 'SBDG']
        return list(set([y['rxcui'] for x in json_response['allRelatedGroup']['conceptGroup'] if x['tty'] in selected_types and 'conceptProperties' in x  for y in x['conceptProperties']]))


    def get_rxnorm_from_rxnav(self, curie_list = None, name_list = None):
        """
        This function queries the rxnorm APIs to get the related rxcui ids for a given curie list and a given string name.
        It accepts a list of curies and a list of names as input and returns a list of rxcuis.
        Specifically, it queries the following APIs:
        For curie ids:
            API: https://rxnav.nlm.nih.gov/REST/rxcui.json?idtype=yourIdtype&id=yourId
            For idtype, we only consider the following: ATC, Drugbank, GCN_SEQNO(NDDF), HIC_SEQN(NDDF), MESH, UNII_CODE(UNII), VUID(VANDF)
        For names:
            API: https://rxnav.nlm.nih.gov/REST/approximateTerm?term=value&maxEntries=4
            The 'value' is the name of given drug
        By using these two kinds of APIs, the function will get some rxcui ids. With these key rxcui ids, another API:
            https://rxnav.nlm.nih.gov/REST/rxcui/id/allrelated.json will be called to get more related rxcui ids.
        """
        
        rxcui_list = []
        selected_prefixes = ['ATC', 'MESH', 'DRUGBANK', 'NDDF', 'RXNORM', 'UNII', 'VANDF']
        prefix_mapping = {'ATC': 'ATC', 'MESH': 'MESH', 'DRUGBANK': 'Drugbank', 'NDDF': 'GCN_SEQNO|HIC_SEQN', 'UNII': 'UNII_CODE', 'VANDF': 'VUID'}
        if curie_list and len(curie_list) > 0:
            ## filter unrelated curies
            curie_list = [curie for curie in curie_list if curie.split(':')[0] in selected_prefixes]
            if len(curie_list) > 0:
                for curie in curie_list:
                    prefix = curie.split(':')[0]
                    value = curie.split(':')[1]
                    if prefix == 'RXNORM':
                        rxcui_list += [value]
                    else:
                        prefix_list = prefix_mapping[prefix].split('|')
                        for prefix in prefix_list:
                            url = f"{self.rxnav_url}/rxcui.json?idtype={prefix}&id={value}"
                            response = requests.get(url)
                            if response.status_code == 200:
                                try:
                                    rxcui_list += response.json()['idGroup']['rxnormId']
                                except KeyError:
                                    pass
            else:
                pass
            
        if name_list and len(name_list) > 0:
            for name in name_list:
                url = f"{self.rxnav_url}/approximateTerm.json?term={name}&maxEntries=1"
                response = requests.get(url)
                if response.status_code == 200:
                    try:
                        rxcui_list += list(set([x['rxcui'] for x in response.json()['approximateGroup']['candidate']]))
                    except KeyError:
                        pass
        
        if len(rxcui_list) > 0:
            final_result = []
            for rxcui in rxcui_list:
                url = f"{self.rxnav_url}/rxcui/{rxcui}/allrelated.json"
                response = requests.get(url)
                if response.status_code == 200:
                    final_result += self._parse_rxcui_json(response.json())
            return list(set(final_result))
        else:
            return []

    def get_rxnorm_from_mychem(self ,curie_list = None):
        """
        This function calls mychem.info API and queries the unii.rxcui field for a given curie list.
        """

        rxcui_list = []
        
        # filter unrelated curies
        selected_prefixes = ['CHEMBL.COMPOUND', 'UMLS', 'KEGG.DRUG', 'DRUGBANK', 'NCIT', 'CHEBI', 'VANDF', 'HMDB', 'DrugCentral', 'UNII']
        query_template_dict = {
            'CHEMBL.COMPOUND': "chembl.molecule_chembl_id:{value} AND _exists_:unii.rxcui",
            'UMLS': "umls.cui:{value} AND _exists_:unii.rxcui",
            'KEGG.DRUG': "_exists_:unii.rxcui and drugcentral.xrefs.kegg_drug:{value}",
            'DRUGBANK': "_exists_:unii.rxcui and drugbank.id:{value}",
            'NCIT': "unii.ncit:{value} AND _exists_:unii.rxcui",
            'CHEBI': "chebi.id:{key}\\:{value} AND _exists_:unii.rxcui",
            'VANDF': "drugcentral.xrefs.vandf:{value} AND _exists_:unii.rxcui",
            'HMDB': "unichem.hmdb:{value} AND _exists_:unii.rxcui",
            'DrugCentral': "drugcentral.xrefs.drugcentral:{value} AND _exists_:unii.rxcui",
            'UNII': "unii.unii:{value} AND _exists_:unii.rxcui"
        }
        
        if curie_list and len(curie_list) > 0:
            curie_list = [curie for curie in curie_list if curie.split(':')[0] in selected_prefixes]
            for curie in curie_list:
                query = query_template_dict[curie.split(':')[0]].format(key=curie.split(':')[0], value=curie.split(':')[1])
                res = self.mc.query(query, fields=", ".join(self.my_chem_fields), size=0)
                if res["total"] > 0:
                    # fetch_all=True option returns all hits as an iterator
                    res = self.mc.query(query, fields=", ".join(self.my_chem_fields), size=1, fetch_all=True)
                    for item in res:
                        if isinstance(item['unii'], list):
                            rxcui_list += [uni['rxcui'] for uni in item['unii'] if 'rxcui' in uni]
                        else:
                            try:
                                rxcui_list.append(item['unii']['rxcui'])
                            except KeyError:
                                pass
                            
            return list(set(rxcui_list))
        else:
            return []
        
    def get_equivalent_curies_and_name(self, curie):
        """
        This function is used to call the node normalizer and node synonymizer to get the equivalent curies and english name based on a given curie
        """
        
        identifiers = []
        labels = []
        
        # get equivalent curies and english name from node normalizer
        res_node_normalizer = self._get_all_equivalent_info_from_node_normalizer(curie)
        if len(res_node_normalizer) > 0:
            identifiers += res_node_normalizer[0]
            labels += res_node_normalizer[1]
            
        # get equivalent curies and english name from node synonymizer
        res_synonymizer = self._get_all_equivalent_info_from_synonymizer(curie)
        if len(res_synonymizer) > 0:
            identifiers += res_synonymizer[0]
            labels += res_synonymizer[1]
        
        return [list(set(identifiers)), list(set(labels))]

    def get_rxcui_results(self, curie, use_curie_id = True, use_curie_name = True, use_rxnav = True, use_mychem = True):
        """
        This function calls the 'get_equivalent_curies_and_name' function to get the equivalent curies and names of the given drug
        Following which we query the RxNav database with the identifer and the english name for the rxcui value
        Following which we query mychem.info for the rxcui value
        """
        
        result = []
        ## Get equivalent curies and names
        equivalent_info = self.get_equivalent_curies_and_name(curie)
        
        ## Get rxcui from RxNav
        if use_curie_id:
            curie_list = equivalent_info[0]
        else:
            curie_list = None
        if use_curie_name:
            name_list = equivalent_info[1]
        else:
            name_list = None
            
        if use_rxnav:
            result += self.get_rxnorm_from_rxnav(curie_list = curie_list, name_list = name_list)
        
        if use_mychem:
            result += self.get_rxnorm_from_mychem(curie_list = curie_list)

        return list(set(result))

if __name__ == "__main__":
    ## Test Examples
    test_curies = ["CHEBI:15365", "RXNORM:1156278"]
    ## Set up drug conflator class
    dc = DrugConflator()
    
    result = [[curie, dc.get_rxcui_results(curie)] for curie in test_curies]
    for item in result:
        print(f"query_curie: {item[0]}, rxcui: {item[1]}", flush=True)
