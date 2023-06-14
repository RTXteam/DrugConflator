import sqlite3
import json
import biothings_client

mc = biothings_client.get_client("chem")

class DrugConflator:
    def __init__(self,curie):
        self.curie = curie
        self.common_name = ""
        self.result = []
        self.my_chem_fields = ['unii']

    def get_rxnorm_from_rxnav(self,mode='curie'):
        con = sqlite3.connect("data/rxnorm3.sqlite")
        cur = con.cursor()

        cui_query = f""" Select DISTINCT DM.PRIMARY_RXCUI,RC.TTY,RC.RXCUI,RC2.STR,RC.STR
                        from RXNCONSO as RC left join DRUG_MAP as DM ON RC.RXCUI == DM.RXCUI 
                        left join RXNCONSO as RC2 ON RC2.RXCUI == DM.PRIMARY_RXCUI """
        if 'mesh' in self.curie.lower():
            where_condition = f"where RC.SAB = 'MSH' and RC.CODE = '{self.curie.split(':')[1]}' COLLATE NOCASE"
        elif 'drugbank:' in self.curie.lower():
            where_condition = f"where RC.SAB = 'DRUGBANK' and RC.CODE = '{self.curie.split(':')[1]}' COLLATE NOCASE"
        elif 'vandf:' in self.curie.lower():
            where_condition = f"where RC.SAB = 'VANDF' and RC.CODE = '{self.curie.split(':')[1]}' COLLATE NOCASE"
        elif 'atc:' in self.curie.lower():
            where_condition = f"where RC.SAB = 'ATC' and RC.CODE = '{self.curie.split(':')[1]}' COLLATE NOCASE"
        elif 'rxnorm:' in self.curie.lower():
            where_condition = f"where RC.SAB = 'RXNORM' and RC.CODE = '{self.curie.split(':')[1]}' COLLATE NOCASE"
        elif 'nddf:' in self.curie.lower():
            where_condition = f"where RC.SAB = 'NDDF' and RC.CODE = '{self.curie.split(':')[1]}' COLLATE NOCASE"
        else:
            where_condition = ""
        if mode == 'name':
            where_condition = f"where RC.STR = '{self.common_name}' COLLATE NOCASE"

        if where_condition:
            cui_query = cui_query + where_condition
        else:
            return
        rxcui = None
        cursor = cur.execute(cui_query).fetchall()
        import pdb;pdb.set_trace()
        if cursor:
            common_name = cursor[0][4]
            if cursor[0][0] and cursor[0][1] == "MIN":
                rxcui = cursor[0][0]
                in_min_flag = True
                # result.append({"input":name,"output": cursor[0][3], "type":"mixture"})
            else:
                rxcui = cursor[0][2]
                in_min_flag = False
                self.result.append({"input_name":common_name,"curie":self.curie, "output": rxcui, "type":"ingredient"})

        in_min_query = f""" select DISTINCT RC.STR,RE.RELA,RC.RXCUI,RC.TTY from RXNREL as RE inner join RXNCONSO as RC on RC.RXCUI == RE.RXCUI2 where RE.RXCUI1 = {rxcui} and RE.RELA in ('part_of', 'has_part') COLLATE NOCASE"""
        if rxcui and in_min_flag:
            # print(in_min_query)
            cursor = cur.execute(in_min_query).fetchall()
            if len(cursor) == 0:
                self.result.append({"input_name":common_name,"curie":self.curie, "output": rxcui, "type":"ingredient"})
            import pdb;pdb.set_trace()
            for item in cursor:
                if item[1] == 'part_of':
                    self.result.append({"input_name":item[0],"curie":self.curie, "output": item[2], "type":"ingredient"})
                if item[1] == 'has_part':
                    self.result.append({"input_name":item[0],"curie":self.curie,"output": item[2], "type":"mixture"})
        con.close()

    def get_rxnorm_from_mychem(self):
        query = ""
        if 'chembl' in self.curie.lower():
            query = f"chembl.molecule_chembl_id:{self.curie.split(':')[-1]} AND _exists_:unii.rxcui"
        elif 'umls' in self.curie.lower():
            query = f"umls.cui:{self.curie.split(':')[-1]} AND _exists_:unii.rxcui"
        elif 'kegg.drug' in self.curie.lower():
            query = f"_exists_:unii.rxcui and drugcentral.xrefs.kegg_drug:{self.curie.split(':')[-1]}"
        elif 'drugbank:' in self.curie.lower():
            query = f"_exists_:unii.rxcui and drugbank.id:{self.curie.split(':')[-1]}"
        elif 'ncit:' in self.curie.lower():
            query = f"unii.ncit:{self.curie.split(':')[-1]} AND _exists_:unii.rxcui"
        elif 'chebi' in self.curie.lower():
            query = f"chebi.id:{self.curie.split(':')[0]}\\:{self.curie.split(':')[1]} AND _exists_:unii.rxcui"
        elif 'vandf' in self.curie.lower():
            query = f"drugcentral.xrefs.vandf:{self.curie.split(':')[1]} AND _exists_:unii.rxcui"
        elif 'hmdb' in self.curie.lower():
            query = f"unichem.hmdb:{self.curie.split(':')[1]} AND _exists_:unii.rxcui"
        elif 'drugcentral' in self.curie.lower():
            query = f"chembl.xrefs.drugcentral.id:{self.curie.split(':')[1]} AND _exists_:unii.rxcui"
        elif 'unii' in self.curie.lower():
            query = f"unii.unii:{self.curie.split(':')[1]} AND _exists_:unii.rxcui"
        if not query:
            return
        res = mc.query(query, fields=", ".join(self.my_chem_fields), size=0)
        print(f'Found {res["total"]} hits from MyChem.info API')
        if res["total"] > 0:
            # fetch_all=True option returns all hits as an iterator
            res = mc.query(query, fields=", ".join(self.my_chem_fields), size=5,fetch_all=True)
            for item in res:
                self.result.append({"input":item['unii'].get('preferred_term'),"output": item['unii']['rxcui'], "type":"unknown"})

    def get_name_from_synonymizer(self):
        # # Create a SQL connection to our SQLite database
        ns_con = sqlite3.connect("data/node_synonymizer_v1.0_KG2.8.0.sqlite")

        # cur = con.cursor()
        ns_cur = ns_con.cursor()
        # The result of a "cursor.execute" can be iterated over by row
        counter = 0
        # cursor = cur.execute("SELECT * FROM RXNCONSO where RXCUI in (315249,315250,315253,315255,315256,315259,315261,315262,315263,315264,315266);")
        node_synonymizer_query = f"""
                                SELECT C.curie,C.unique_concept_curie,U.curie,U.name,U.category
                                  FROM curies AS C
                                 INNER JOIN unique_concepts AS U ON C.unique_concept_curie == U.uc_curie
                                 WHERE C.uc_curie  = '{self.curie}'"""
        result = ns_cur.execute(node_synonymizer_query).fetchall()
        self.common_name = result[0][3]
        ns_con.close()
                                # WHERE N.id_simplified in ('{identifier}')"""
        # print(sql_query_template)
        

if __name__ == "__main__":
    curie = "VANDF:4012972"
    dc = DrugConflator(curie=curie)
    dc.get_name_from_synonymizer()
    dc.get_rxnorm_from_rxnav(mode='curie')
    if not dc.result:
        dc.get_rxnorm_from_mychem()
    if not dc.result:
        dc.get_rxnorm_from_rxnav(mode='name')