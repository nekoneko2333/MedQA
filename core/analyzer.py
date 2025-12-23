"""
知识图谱数据分析

- 知识图谱整体统计（节点数、关系数等）
- 数据覆盖率分析
- 疾病关联分析（相似疾病、共用药品等）
- 热门疾病和症状排行
- 科室分布统计

"""

from py2neo import Graph
from utils.logger import get_logger

logger = get_logger(__name__)

class KnowledgeGraphAnalyzer:
    """
    节点统计、关系统计、覆盖率分析、疾病关联
    """
    
    def __init__(self):
        try:
            self.g = Graph("bolt://localhost:7687", auth=("neo4j", "2512macf"))
            self.connected = True
        except Exception:
            self.g = None
            self.connected = False
    
    def get_overview_stats(self):
        """获取图谱整体统计信息"""
        if not self.g:
            return None
        
        stats = {}
        try:
            # 各类节点数量
            stats['disease_count'] = self.g.run("MATCH (n:Disease) RETURN count(n) as cnt").data()[0]['cnt']
            stats['symptom_count'] = self.g.run("MATCH (n:Symptom) RETURN count(n) as cnt").data()[0]['cnt']
            stats['drug_count'] = self.g.run("MATCH (n:Drug) RETURN count(n) as cnt").data()[0]['cnt']
            stats['food_count'] = self.g.run("MATCH (n:Food) RETURN count(n) as cnt").data()[0]['cnt']
            stats['check_count'] = self.g.run("MATCH (n:Check) RETURN count(n) as cnt").data()[0]['cnt']
            stats['department_count'] = self.g.run("MATCH (n:Department) RETURN count(n) as cnt").data()[0]['cnt']
            
            # 总关系数
            stats['total_relations'] = self.g.run("MATCH ()-[r]->() RETURN count(r) as cnt").data()[0]['cnt']
            
            # 各类关系数量
            stats['rel_symptom'] = self.g.run("MATCH ()-[r:has_symptom]->() RETURN count(r) as cnt").data()[0]['cnt']
            stats['rel_drug'] = self.g.run("MATCH ()-[r:common_drug]->() RETURN count(r) as cnt").data()[0]['cnt']
            stats['rel_food'] = self.g.run("MATCH ()-[r:do_eat]->() RETURN count(r) as cnt").data()[0]['cnt']
            stats['rel_check'] = self.g.run("MATCH ()-[r:need_check]->() RETURN count(r) as cnt").data()[0]['cnt']
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def get_coverage_stats(self):
        """获取数据覆盖率统计"""
        if not self.g:
            return None
        
        coverage = {}
        try:
            total_diseases = self.g.run("MATCH (n:Disease) RETURN count(n) as cnt").data()[0]['cnt']
            
            # 各属性覆盖率
            has_symptom = self.g.run("MATCH (d:Disease)-[:has_symptom]->() RETURN count(DISTINCT d) as cnt").data()[0]['cnt']
            has_drug = self.g.run("MATCH (d:Disease)-[:common_drug]->() RETURN count(DISTINCT d) as cnt").data()[0]['cnt']
            has_food = self.g.run("MATCH (d:Disease)-[:do_eat]->() RETURN count(DISTINCT d) as cnt").data()[0]['cnt']
            has_check = self.g.run("MATCH (d:Disease)-[:need_check]->() RETURN count(DISTINCT d) as cnt").data()[0]['cnt']
            has_dept = self.g.run("MATCH (d:Disease)-[:belongs_to]->() RETURN count(DISTINCT d) as cnt").data()[0]['cnt']
            
            coverage['total'] = total_diseases
            coverage['symptom'] = {'count': has_symptom, 'rate': round(has_symptom/total_diseases*100, 1) if total_diseases > 0 else 0}
            coverage['drug'] = {'count': has_drug, 'rate': round(has_drug/total_diseases*100, 1) if total_diseases > 0 else 0}
            coverage['food'] = {'count': has_food, 'rate': round(has_food/total_diseases*100, 1) if total_diseases > 0 else 0}
            coverage['check'] = {'count': has_check, 'rate': round(has_check/total_diseases*100, 1) if total_diseases > 0 else 0}
            coverage['department'] = {'count': has_dept, 'rate': round(has_dept/total_diseases*100, 1) if total_diseases > 0 else 0}
            
        except Exception as e:
            coverage['error'] = str(e)
        
        return coverage
    
    def get_top_diseases(self, limit=10):
        """获取关联最多的热门疾病"""
        if not self.g:
            return []
        try:
            query = """
            MATCH (d:Disease)-[r]->()
            RETURN d.name as name, count(r) as relation_count
            ORDER BY relation_count DESC
            LIMIT $limit
            """
            return self.g.run(query, limit=limit).data()
        except:
            return []
    
    def get_top_symptoms(self, limit=10):
        """获取最常见的症状"""
        if not self.g:
            return []
        try:
            query = """
            MATCH (d:Disease)-[:has_symptom]->(s:Symptom)
            RETURN s.name as name, count(d) as disease_count
            ORDER BY disease_count DESC
            LIMIT $limit
            """
            return self.g.run(query, limit=limit).data()
        except:
            return []
    
    def find_similar_diseases(self, disease_name, limit=5):
        """查找与指定疾病有相似症状的疾病"""
        if not self.g:
            return []
        try:
            query = """
            MATCH (d1:Disease {name: $name})-[:has_symptom]->(s:Symptom)<-[:has_symptom]-(d2:Disease)
            WHERE d1 <> d2
            RETURN d2.name as disease, count(DISTINCT s) as common_symptoms, 
                   collect(DISTINCT s.name)[0..5] as symptoms
            ORDER BY common_symptoms DESC
            LIMIT $limit
            """
            return self.g.run(query, name=disease_name, limit=limit).data()
        except:
            return []
    
    def find_common_drugs(self, disease_name):
        """查找与指定疾病共用药品的其他疾病"""
        if not self.g:
            return []
        try:
            query = """
            MATCH (d1:Disease {name: $name})-[:common_drug]->(drug:Drug)<-[:common_drug]-(d2:Disease)
            WHERE d1 <> d2
            RETURN d2.name as disease, count(DISTINCT drug) as common_drugs,
                   collect(DISTINCT drug.name)[0..3] as drugs
            ORDER BY common_drugs DESC
            LIMIT 5
            """
            return self.g.run(query, name=disease_name).data()
        except:
            return []
    
    def get_department_distribution(self):
        """获取疾病的科室分布"""
        if not self.g:
            return []
        try:
            query = """
            MATCH (d:Disease)-[:belongs_to]->(dept:Department)
            RETURN dept.name as department, count(d) as disease_count
            ORDER BY disease_count DESC
            LIMIT 10
            """
            result = self.g.run(query).data()
            
            if not result:
                alt_query = """
                MATCH (d:Disease)-[r]->(dept:Department)
                RETURN dept.name as department, count(d) as disease_count
                ORDER BY disease_count DESC
                LIMIT 10
                """
                result = self.g.run(alt_query).data()
                if result:
                    logger.warning(f"使用备用查询获取科室分布，找到 {len(result)} 条记录")
            
            if not result:
                dept_check = self.g.run("MATCH (dept:Department) RETURN count(dept) as cnt").data()
                dept_count = dept_check[0]['cnt'] if dept_check else 0
                if dept_count > 0:
                    logger.warning(f"数据库中有 {dept_count} 个科室节点，但没有找到 Disease 到 Department 的关系")
                else:
                    logger.warning(f"数据库中没有 Department 节点")
            
            return result if result else []
        except Exception as e:
            logger.error(f"科室分布查询失败: {e}")
            import traceback
            traceback.print_exc()
            return []


