"""
RAG检索

- 从Neo4j知识图谱中检索与问题相关的信息
- 支持多种检索策略（实体匹配、语义搜索等）
- 构建检索增强的上下文

"""

from typing import List, Dict, Optional
from utils.logger import get_logger
from py2neo import Graph

logger = get_logger(__name__)


class RAGRetriever:
    
    def __init__(self, graph: Optional[Graph] = None):
        """
        初始化
        """
        if graph:
            self.g = graph
        else:
            try:
                import os
                neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                neo4j_password = os.getenv("NEO4J_PASSWORD", "2512macf")
                self.g = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))
            except Exception as e:
                logger.error(f"Neo4j连接失败: {e}")
                self.g = None
    
    def retrieve(self, question: str, entities: Optional[Dict] = None, max_results: int = 5) -> str:
        """
        从知识图谱检索相关信息

        question: 用户问题
        entities: 已识别的实体字典，格式为 {实体名: [类型列表]}
        max_results: 最大检索结果数
        
        """
        if not self.g:
            return ""
        
        retrieved_info = []
        
        # 如果没有提供实体，尝试从问题中提取
        if not entities:
            entities = self._extract_entities_from_question(question)
        
        # 基于实体的检索
        if entities:
            for entity, types in entities.items():
                if 'disease' in types:
                    info = self._retrieve_disease_info(entity, max_results)
                    if info:
                        retrieved_info.append(info)
                elif 'symptom' in types:
                    info = self._retrieve_symptom_info(entity, max_results)
                    if info:
                        retrieved_info.append(info)
                elif 'drug' in types:
                    info = self._retrieve_drug_info(entity, max_results)
                    if info:
                        retrieved_info.append(info)
        
        # 通用检索仅在信息不足时回退：优先用已识别实体名作为关键词
        if len(retrieved_info) < 2:
            generic_info = ""
            if entities:
                for ent in entities.keys():
                    generic_info = self._retrieve_generic_info(ent, max_results)
                    if generic_info:
                        break
            else:
                generic_info = self._retrieve_generic_info(question, max_results)
            if generic_info:
                retrieved_info.append(generic_info)
        
        # 合并检索结果
        if retrieved_info:
            return "\n\n".join(retrieved_info)
        return ""
    
    def _extract_entities_from_question(self, question: str) -> Dict:
        # 使用已有的 question_classifier 来提取实体
        try:
            from nlp.question_classifier import QuestionClassifier
            qc = QuestionClassifier()
            res = qc.classify(question)
            if res and isinstance(res, dict):
                return res.get('args', {}) or {}
        except Exception as e:
            logger.warning(f"实体抽取失败，fallback为空：{e}")

        # 若无法执行分类器或无结果，返回空字典
        return {}
    
    def _retrieve_disease_info(self, disease_name: str, max_results: int = 5) -> str:
        """检索疾病相关信息"""
        try:
            query = """
            MATCH (d:Disease {name: $name})
            OPTIONAL MATCH (d)-[:has_symptom]->(s:Symptom)
            OPTIONAL MATCH (d)-[:common_drug]->(drug:Drug)
            OPTIONAL MATCH (d)-[:do_eat]->(f:Food)
            OPTIONAL MATCH (d)-[:need_check]->(c:Check)
            OPTIONAL MATCH (d)-[:belongs_to]->(dept:Department)
            WITH d, 
                 collect(DISTINCT s.name)[0..10] as symptoms,
                 collect(DISTINCT drug.name)[0..10] as drugs,
                 collect(DISTINCT f.name)[0..10] as foods,
                 collect(DISTINCT c.name)[0..10] as checks,
                 collect(DISTINCT dept.name)[0..5] as departments
            RETURN d.name as name,
                   d.desc as desc,
                   d.cause as cause,
                   d.prevent as prevent,
                   d.cure_way as cure_way,
                   symptoms, drugs, foods, checks, departments
            LIMIT 1
            """
            result = self.g.run(query, name=disease_name).data()
            logger.debug("Executing disease Cypher: %s | params: %s", query.strip(), {'name': disease_name})
            logger.debug("Raw disease query result: %s", result)
            
            if result:
                r = result[0]
                info_parts = []
                
                if r.get('name'):
                    info_parts.append(f"疾病名称: {r['name']}")
                if r.get('desc'):
                    info_parts.append(f"疾病描述: {r['desc']}")
                if r.get('cause'):
                    info_parts.append(f"病因: {r['cause']}")
                if r.get('prevent'):
                    info_parts.append(f"预防措施: {r['prevent']}")
                if r.get('cure_way'):
                    cure_ways = r['cure_way'] if isinstance(r['cure_way'], list) else [r['cure_way']]
                    info_parts.append(f"治疗方法: {', '.join(cure_ways)}")
                if r.get('symptoms'):
                    info_parts.append(f"常见症状: {', '.join(r['symptoms'])}")
                if r.get('drugs'):
                    info_parts.append(f"常用药品: {', '.join(r['drugs'])}")
                if r.get('foods'):
                    info_parts.append(f"推荐食物: {', '.join(r['foods'])}")
                if r.get('checks'):
                    info_parts.append(f"检查项目: {', '.join(r['checks'])}")
                if r.get('departments'):
                    info_parts.append(f"所属科室: {', '.join(r['departments'])}")
                
                    logger.debug("Formatted disease info for '%s': %s", disease_name, info_parts)
                    return "\n".join(info_parts)
        except Exception as e:
            logger.error(f"检索疾病信息失败: {e}")
        
        return ""
    
    def _retrieve_symptom_info(self, symptom_name: str, max_results: int = 5) -> str:
        """检索症状相关信息"""
        try:
            query = """
            MATCH (d:Disease)-[:has_symptom]->(s:Symptom {name: $name})
            RETURN d.name as disease, s.name as symptom
            LIMIT $max_results
            """
            result = self.g.run(query, name=symptom_name, max_results=max_results).data()
            
            if result:
                diseases = [r['disease'] for r in result]
                return f"症状「{symptom_name}」可能相关的疾病: {', '.join(diseases)}"
        except Exception as e:
            logger.error(f"检索症状信息失败: {e}")
        
        return ""
    
    def _retrieve_drug_info(self, drug_name: str, max_results: int = 5) -> str:
        """检索药品相关信息"""
        try:
            query = """
            MATCH (d:Disease)-[:common_drug]->(drug:Drug {name: $name})
            RETURN d.name as disease, drug.name as drug
            LIMIT $max_results
            """
            result = self.g.run(query, name=drug_name, max_results=max_results).data()
            
            if result:
                diseases = [r['disease'] for r in result]
                return f"药品「{drug_name}」可用于治疗: {', '.join(diseases)}"
        except Exception as e:
            logger.error(f"检索药品信息失败: {e}")
        
        return ""
    
    def _retrieve_generic_info(self, question: str, max_results: int = 5) -> str:
        # 一个简单的实现，对 Disease/Drug/Symptom 的名称和描述做包含匹配
        try:
            kw = (question or '').strip()
            if not kw:
                return ""

            kw_lower = kw.lower()
            retrieved_parts = []

            # 疾病匹配：匹配 name 或 desc
            try:
                dq = """
                MATCH (d:Disease)
                WHERE toLower(d.name) CONTAINS $kw OR toLower(d.desc) CONTAINS $kw
                RETURN d.name as name, d.desc as desc
                LIMIT $limit
                """
                logger.debug("Executing generic disease query: %s | params: %s", dq.strip(), {'kw': kw_lower, 'limit': max_results})
                diseases = self.g.run(dq, kw=kw_lower, limit=max_results).data()
                logger.debug("Generic disease query result: %s", diseases)
                if diseases:
                    names = [r.get('name') for r in diseases if r.get('name')]
                    if names:
                        retrieved_parts.append(f"相关疾病: {', '.join(names)}")
            except Exception as e:
                logger.debug(f"通用检索-疾病查询失败: {e}")

            # 药品匹配：匹配 name 或 desc
            try:
                dq = """
                MATCH (n:Drug)
                WHERE toLower(n.name) CONTAINS $kw OR toLower(n.desc) CONTAINS $kw
                RETURN n.name as name, n.desc as desc
                LIMIT $limit
                """
                logger.debug("Executing generic drug query: %s | params: %s", dq.strip(), {'kw': kw_lower, 'limit': max_results})
                drugs = self.g.run(dq, kw=kw_lower, limit=max_results).data()
                logger.debug("Generic drug query result: %s", drugs)
                if drugs:
                    names = [r.get('name') for r in drugs if r.get('name')]
                    if names:
                        retrieved_parts.append(f"相关药品: {', '.join(names)}")
            except Exception as e:
                logger.debug(f"通用检索-药品查询失败: {e}")

            # 症状匹配：匹配 name
            try:
                dq = """
                MATCH (s:Symptom)
                WHERE toLower(s.name) CONTAINS $kw
                RETURN s.name as name
                LIMIT $limit
                """
                logger.debug("Executing generic symptom query: %s | params: %s", dq.strip(), {'kw': kw_lower, 'limit': max_results})
                syms = self.g.run(dq, kw=kw_lower, limit=max_results).data()
                logger.debug("Generic symptom query result: %s", syms)
                if syms:
                    names = [r.get('name') for r in syms if r.get('name')]
                    if names:
                        retrieved_parts.append(f"相关症状: {', '.join(names)}")
            except Exception as e:
                logger.debug(f"通用检索-症状查询失败: {e}")

            if retrieved_parts:
                return "\n".join(retrieved_parts)

        except Exception as e:
            logger.error(f"通用检索失败: {e}")

        return ""

