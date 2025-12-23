"""
问题解析

- 将分类结果转换为Cypher查询语句
- 根据问题类型生成对应的Neo4j查询

"""


class QuestionPaser:
    def build_entitydict(self, args):
        """创建节点"""
        entity_dict = {}
        for arg, types in args.items():
            for type in types:
                if type not in entity_dict:
                    entity_dict[type] = [arg]
                else:
                    entity_dict[type].append(arg)

        return entity_dict

    def parser_main(self, res_classify):
        args = res_classify['args']
        entity_dict = self.build_entitydict(args)
        question_types = res_classify['question_types']
        sqls = []
        # 处理生产厂家的bug
        if 'drug_producer' in question_types and 'drug_desc' in question_types:
            question_types = [qt for qt in question_types if qt != 'drug_desc']

        for question_type in question_types:
            sql_ = {}
            sql_['question_type'] = question_type
            sql = []
            if question_type == 'disease_symptom':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'symptom_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('symptom'))

            elif question_type == 'disease_cause':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_acompany':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_not_food':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_do_food':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'food_not_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('food'))

            elif question_type == 'food_do_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('food'))

            elif question_type == 'disease_drug':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))
            
            elif question_type == 'symptom_drug':
                sql = self.sql_transfer(question_type, entity_dict.get('symptom'))

            elif question_type == 'drug_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'disease_check':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'check_disease':
                sql = self.sql_transfer(question_type, entity_dict.get('check'))

            elif question_type == 'disease_prevent':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_lasttime':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_cureway':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))
            
            elif question_type == 'symptom_cureway':
                sql = self.sql_transfer(question_type, entity_dict.get('symptom'))

            elif question_type == 'drug_producer':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'drug_desc':
                sql = self.sql_transfer(question_type, entity_dict.get('drug'))

            elif question_type == 'disease_cureprob':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_easyget':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_desc':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            elif question_type == 'disease_department':
                sql = self.sql_transfer(question_type, entity_dict.get('disease'))

            if sql:
                sql_['sql'] = sql

                sqls.append(sql_)

        return sqls

    '''针对不同的问题，分开进行处理'''
    def sql_transfer(self, question_type, entities):
        if not entities:
            return []
        sql = []

        # 查询疾病的原因
        if question_type == 'disease_cause':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.cause".format(i) for i in entities]

        # 查询疾病的预防措施
        elif question_type == 'disease_prevent':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.prevent".format(i) for i in entities]

        # 查询疾病的持续时间
        elif question_type == 'disease_lasttime':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.cure_lasttime".format(i) for i in entities]

        # 查询疾病的治愈概率
        elif question_type == 'disease_cureprob':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.cured_prob".format(i) for i in entities]

        # 查询疾病的治疗方式
        elif question_type == 'disease_cureway':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.cure_way".format(i) for i in entities]
        
        # 查询症状对应的疾病的治疗方式（症状+怎么办）
        elif question_type == 'symptom_cureway':
            symptoms = [e for e in entities if e]
            if symptoms:
                symptom_list = ", ".join(["'{}'".format(s) for s in symptoms])
                sql = [
                    f"""
                    MATCH (m:Disease)-[r:has_symptom]->(n:Symptom)
                    WHERE n.name IN [{symptom_list}]
                    WITH m, count(n) as match_count, collect(n.name) as matched_symptoms
                    MATCH (m)-[:has_symptom]->(allS:Symptom)
                    WITH m, match_count, matched_symptoms, count(allS) AS total_sym_count
                    ORDER BY match_count DESC, total_sym_count ASC
                    LIMIT 8
                    RETURN m.name, m.cure_way, matched_symptoms, match_count
                    """
                ]

        # 查询疾病的易发人群
        elif question_type == 'disease_easyget':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.easy_get".format(i) for i in entities]

        # 查询疾病的相关介绍
        elif question_type == 'disease_desc':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name, m.desc".format(i) for i in entities]

        # 查询疾病有哪些症状
        elif question_type == 'disease_symptom':
            sql = ["MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]

        # 查询症状会导致哪些疾病（多症状组合查询）
        if question_type == 'symptom_disease':
            # 多症状合并到一个SQL
            symptoms = [e for e in entities if e]
            if symptoms:
                symptom_list = ", ".join(["'{}'".format(s) for s in symptoms])
                sql = [
                    f"""
                    MATCH (m:Disease)-[r:has_symptom]->(n:Symptom)
                    WHERE n.name IN [{symptom_list}]
                    WITH m, count(n) as match_count, collect(n.name) as matched_symptoms
                    MATCH (m)-[:has_symptom]->(allS:Symptom)
                    WITH m, match_count, matched_symptoms, count(allS) AS total_sym_count
                    ORDER BY match_count DESC, total_sym_count ASC
                    LIMIT 8
                    RETURN m.name, matched_symptoms, match_count
                    """
                ]
        # 查询疾病的并发症
        elif question_type == 'disease_acompany':
            sql1 = ["MATCH (m:Disease)-[r:acompany_with]->(n:Disease) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:acompany_with]->(n:Disease) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql = sql1 + sql2
        # 查询疾病的忌口
        elif question_type == 'disease_not_food':
            sql = ["MATCH (m:Disease)-[r:no_eat]->(n:Food) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]

        # 查询疾病建议吃的东西
        elif question_type == 'disease_do_food':
            sql1 = ["MATCH (m:Disease)-[r:do_eat]->(n:Food) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_eat]->(n:Food) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql = sql1 + sql2

        # 已知忌口查疾病
        elif question_type == 'food_not_disease':
            sql = ["MATCH (m:Disease)-[r:no_eat]->(n:Food) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]

        # 已知推荐查疾病
        elif question_type == 'food_do_disease':
            sql1 = ["MATCH (m:Disease)-[r:do_eat]->(n:Food) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_eat]->(n:Food) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql = sql1 + sql2

        # 查询疾病常用药品－药品别名记得扩充
        elif question_type == 'disease_drug':
            sql1 = ["MATCH (m:Disease)-[r:common_drug]->(n:Drug) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql = sql1 + sql2

        # 症状对应的疾病的用药（症状+吃什么药）
        elif question_type == 'symptom_drug':
            # 先找到症状对应的疾病，然后返回这些疾病的用药
            sql = ["""
                MATCH (s:Symptom)<-[:has_symptom]-(d:Disease)-[:common_drug]->(drug:Drug)
                WHERE s.name = '{0}'
                WITH d, drug, s, count(DISTINCT s) as symptom_count
                ORDER BY symptom_count DESC
                LIMIT 5
                RETURN d.name as `d.name`, drug.name as `n.name`, s.name as `s.name`
            """.format(i).strip() for i in entities]

        # 已知药品查询能够治疗的疾病
        elif question_type == 'drug_disease':
            sql1 = ["MATCH (m:Disease)-[r:common_drug]->(n:Drug) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]
            sql = sql1 + sql2
        # 查询疾病应该进行的检查
        elif question_type == 'disease_check':
            sql = ["MATCH (m:Disease)-[r:need_check]->(n:Check) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]

        # 已知检查查询疾病
        elif question_type == 'check_disease':
            sql = ["MATCH (m:Disease)-[r:need_check]->(n:Check) where n.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]

        # 查询疾病所属科室
        elif question_type == 'disease_department':
            sql = ["MATCH (m:Disease)-[r:belongs_to]->(n:Department) where m.name = '{0}' return m.name, r.name, n.name".format(i) for i in entities]

        # 查询药品的生产厂家
        elif question_type == 'drug_producer':
            sql = ["MATCH (n:Drug)-[:produced_by]->(m:Producer) WHERE n.name = '{0}' RETURN n.name, m.name".format(i) for i in entities]

        # 查询药品的描述信息
        elif question_type == 'drug_desc':
            sql = ["MATCH (n:Drug) WHERE n.name = '{0}' RETURN n.name, n.desc".format(i) for i in entities]

        return sql



if __name__ == '__main__':
    handler = QuestionPaser()
