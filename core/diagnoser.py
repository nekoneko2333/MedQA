"""
症状组合诊断

- 根据用户输入的症状组合，在知识图谱中查找匹配的疾病
- 计算症状匹配度
- 提供常见症状列表

"""

from py2neo import Graph
from utils.logger import get_logger

logger = get_logger(__name__)

class SymptomDiagnoser:
    """
    症状组合诊断器
    根据用户输入的症状组合，在Neo4j知识图谱中查找匹配的疾病，
    并计算匹配度：匹配的症状数 / 总症状数

    """
    
    def __init__(self):
        try:
            self.g = Graph("bolt://localhost:7687", auth=("neo4j", "2512macf"))
            self.connected = True
        except:
            self.g = None
            self.connected = False
        
        try:
            from nlp.question_classifier import QuestionClassifier
            self.classifier = QuestionClassifier()
        except Exception as e:
            logger.warning(f"分类器初始化失败: {e}")
            self.classifier = None
    
    def diagnose(self, symptoms):
        """
        根据症状列表诊断可能的疾病

        """
        if not self.g or not symptoms:
            return []
        
        results = {}
        for symptom in symptoms:
            try:
                query = """
                MATCH (d:Disease)-[:has_symptom]->(s:Symptom)
                WHERE s.name CONTAINS $symptom
                RETURN d.name as disease, s.name as symptom
                """
                data = self.g.run(query, symptom=symptom).data()
                for item in data:
                    disease = item['disease']
                    if disease not in results:
                        results[disease] = {'matched_user_symptoms': set(), 'all_symptoms': []}
                    # 记录匹配到的用户输入症状，用于计算匹配度
                    results[disease]['matched_user_symptoms'].add(symptom)
                    # 记录所有相关症状
                    if item['symptom'] not in results[disease]['all_symptoms']:
                        results[disease]['all_symptoms'].append(item['symptom'])
            except:
                continue
        
        total_symptoms = len(symptoms)
        diagnosis_results = []
        
        # 按匹配的用户症状数量排序
        sorted_results = sorted(
            [(d, info) for d, info in results.items()],
            key=lambda x: len(x[1]['matched_user_symptoms']),
            reverse=True
        )[:10]
        
        for disease, info in sorted_results:
            # 匹配度 = 匹配到的用户症状数 / 用户输入的总症状数 * 100
            # 确保不超过100%
            matched_count = len(info['matched_user_symptoms'])
            match_rate = min(int((matched_count / total_symptoms) * 100), 100)
            
            diagnosis_results.append({
                'disease': disease,
                'match_rate': match_rate,
                'matched_symptoms': list(info['matched_user_symptoms']),
                'all_symptoms': info['all_symptoms'][:5]  # 只显示前5个相关症状
            })
        return diagnosis_results
    
    def get_common_symptoms(self, limit=20):
        """
        获取最常见的症状列表
        """
        try:
            query = "MATCH (d:Disease)-[:has_symptom]->(s:Symptom) RETURN s.name as symptom, count(d) as cnt ORDER BY cnt DESC LIMIT $limit"
            data = self.g.run(query, limit=limit).data()
            # 过滤掉无效的症状
            invalid_symptoms = ["驻站医", "驻站医师"] 
            symptoms = [item['symptom'] for item in data if item['symptom'] not in invalid_symptoms]
            return symptoms
        except:
            return []

