"""
问题意图推理
支持多跳推理、因果推理、路径可视化

"""
import re
from typing import List, Dict, Tuple, Optional, Any
from utils.logger import get_logger
from py2neo import Graph

logger = get_logger(__name__)


class KnowledgeReasoner:
    
    def __init__(self):
        try:
            self.graph = Graph("bolt://localhost:7687", auth=("neo4j", "2512macf"))
            self.connected = True
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            self.graph = None
            self.connected = False
        
        # 多跳查询定义模板
        self.multi_hop_patterns = [
            # 并发症链推理：疾病 → 并发症 → 并发症的症状
            {
                'pattern': r'(.+?)(?:的|这些|此|其|该)?(?:并发症|伴随病).*?(?:有什么症状|症状|表现)',
                'type': 'disease_complication_symptom',
                'hops': ['disease→complication', 'complication→symptom'],
                'description': '疾病→并发症→症状'
            },
            # 并发症治疗推理：疾病 → 并发症 → 治疗
            {
                'pattern': r'(?:针对|对于|治疗)?(.+?)(?:的|这些|此|其|该)?(?:并发症|伴随病).*?(?:怎么治|如何治疗|用什么药|吃什么药|怎么办)',
                'type': 'disease_complication_treatment',
                'hops': ['disease→complication', 'complication→treatment'],
                'description': '疾病→并发症→治疗'
            },
            # 症状链推理：症状 → 疾病 → 检查
            {
                'pattern': r'(.+?)(?:可能是什么病|是什么病).*?(?:做什么检查|怎么检查|查什么)',
                'type': 'symptom_disease_check',
                'hops': ['symptom→disease', 'disease→check'],
                'description': '症状→疾病→检查'
            },
            # 症状链推理：症状 → 疾病 → 科室
            {
                'pattern': r'(.+?)(?:是什么病|怎么回事).*?(?:挂什么科|看什么科|去哪个科)',
                'type': 'symptom_disease_department',
                'hops': ['symptom→disease', 'disease→department'],
                'description': '症状→疾病→科室'
            },
            # 复合查询：疾病 → 药物 + 科室
            {
                'pattern': r'(.+?)(?:吃什么药|用什么药).*?(?:挂什么科|看什么科)',
                'type': 'disease_drug_department',
                'hops': ['disease→drug', 'disease→department'],
                'description': '疾病→药物+科室'
            },
            {
                'pattern': r'(.+?)(?:挂什么科|看什么科).*?(?:吃什么药|用什么药)',
                'type': 'disease_drug_department',
                'hops': ['disease→department', 'disease→drug'],
                'description': '疾病→科室+药物'
            },
            # 并发症饮食推理：疾病 → 并发症 → 饮食
            {
                'pattern': r'(.+?)(?:的并发症|并发症).*?(?:吃什么|饮食|忌口|能吃|不能吃)',
                'type': 'disease_complication_food',
                'hops': ['disease→complication', 'complication→food'],
                'description': '疾病→并发症→饮食'
            },
            # 并发症预防推理：疾病 → 并发症 → 预防
            {
                'pattern': r'(.+?)(?:的?并发症|伴随病).*?(?:怎么预防|如何预防|预防措施|预防)',
                'type': 'disease_complication_prevention',
                'hops': ['disease→complication', 'complication→prevention'],
                'description': '疾病→并发症→预防'
            },
            # 单纯并发症查询：疾病 → 并发症
            {
                'pattern': r'(.+?)(?:的并发症|并发症|会引起什么病|引起哪些病|有哪些并发症)',
                'type': 'disease_complication',
                'hops': ['disease→complication'],
                'description': '疾病→并发症'
            },
        ]
        
        # 编译正则
        self.compiled_patterns = [
            {**p, 'regex': re.compile(p['pattern'])} 
            for p in self.multi_hop_patterns
        ]
    
    def _find_disease_by_name(self, disease_name: str) -> Optional[str]:
        """
        匹配疾病名称
        """
        if not self.connected:
            return None
        
        # 先尝试精确匹配
        exact_query = """
        MATCH (d:Disease)
        WHERE d.name = $disease
        RETURN d.name as name
        LIMIT 1
        """
        exact_result = self.graph.run(exact_query, disease=disease_name).data()
        if exact_result:
            return exact_result[0]['name']
        
        # 如果精确匹配失败，尝试 CONTAINS 匹配，但优先匹配长度最接近的
        contains_query = """
        MATCH (d:Disease)
        WHERE d.name CONTAINS $disease
        RETURN d.name as name
        ORDER BY 
            CASE WHEN d.name = $disease THEN 0 ELSE 1 END,
            ABS(LENGTH(d.name) - LENGTH($disease)),
            d.name
        LIMIT 5
        """
        contains_results = self.graph.run(contains_query, disease=disease_name).data()
        
        if contains_results:
            # 优先返回长度最接近的，且如果输入是完整词，优先返回完全匹配的
            best_match = contains_results[0]['name']
            # 如果匹配到的名称包含输入名称且长度差小于等于3，认为是合理匹配
            # 但如果输入是完整词，而匹配到的是包含它的长词则跳过
            if len(best_match) - len(disease_name) <= 3:
                return best_match
            # 如果长度差太大，尝试找更短的匹配
            for result in contains_results:
                if abs(len(result['name']) - len(disease_name)) <= 2:
                    return result['name']
            # 如果都太长，返回第一个
            return best_match
        
        return None
    
    def detect_multi_hop(self, question: str) -> Optional[Dict]:
        """检测是否有多个意图，即是否为多跳查询"""
        for pattern_info in self.compiled_patterns:
            match = pattern_info['regex'].search(question)
            if match:
                entity = match.group(1).strip()
                # 清理实体中的多余字符
                entity = re.sub(r'[，。？！,.\?!]', '', entity)
                return {
                    'type': pattern_info['type'],
                    'entity': entity,
                    'hops': pattern_info['hops'],
                    'description': pattern_info['description']
                }
        return None
    
    def execute_reasoning(self, question: str) -> Optional[Dict]:
        """推理查询"""
        if not self.connected:
            return None
        
        # 检测多跳查询
        hop_info = self.detect_multi_hop(question)
        if not hop_info:
            return None
        
        reasoning_type = hop_info['type']
        entity = hop_info['entity']
        
        # 新定义多段的查询类型
        if reasoning_type == 'disease_complication_symptom':
            return self._reason_disease_complication_symptom(entity, hop_info)
        elif reasoning_type == 'disease_complication_treatment':
            return self._reason_disease_complication_treatment(entity, hop_info)
        elif reasoning_type == 'symptom_disease_check':
            return self._reason_symptom_disease_check(entity, hop_info)
        elif reasoning_type == 'symptom_disease_department':
            return self._reason_symptom_disease_department(entity, hop_info)
        elif reasoning_type == 'disease_drug_department':
            return self._reason_disease_drug_department(entity, hop_info)
        elif reasoning_type == 'disease_complication_food':
            return self._reason_disease_complication_food(entity, hop_info)
        elif reasoning_type == 'disease_complication_prevention':
            return self._reason_disease_complication_prevention(entity, hop_info)
        elif reasoning_type == 'disease_complication':
            return self._reason_disease_complication(entity, hop_info)
        
        return None
    
    def _reason_disease_complication_symptom(self, disease: str, hop_info: Dict) -> Dict:
        """
        疾病 → 并发症 → 并发症的症状
        """
        reasoning_steps = []
        
        actual_disease = self._find_disease_by_name(disease)
        if not actual_disease:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{disease}」的相关信息",
                'reasoning_path': []
            }
        
        # 查询并发症
        comp_query = """
        MATCH (d:Disease)-[r:acompany_with]->(comp:Disease)
        WHERE d.name = $disease
        RETURN d.name as disease, comp.name as complication
        LIMIT 10
        """
        comp_results = self.graph.run(comp_query, disease=actual_disease).data()
        
        if not comp_results:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{actual_disease}」的并发症信息",
                'reasoning_path': []
            }
        
        complications = list(set([r['complication'] for r in comp_results]))
        
        reasoning_steps.append({
            'step': 1,
            'action': f"查询「{actual_disease}」的并发症",
            'query': '疾病 → 并发症',
            'result': complications[:5],
            'relation': 'acompany_with'
        })
        
        # 查询并发症的症状
        comp_symptoms = {}
        for comp in complications[:5]:
            symp_query = """
            MATCH (d:Disease)-[:has_symptom]->(s:Symptom)
            WHERE d.name = $comp
            RETURN s.name as symptom
            LIMIT 5
            """
            symp_results = self.graph.run(symp_query, comp=comp).data()
            if symp_results:
                comp_symptoms[comp] = [r['symptom'] for r in symp_results]
        
        reasoning_steps.append({
            'step': 2,
            'action': '查询各并发症的典型症状',
            'query': '并发症 → 症状',
            'result': f"分析了 {len(comp_symptoms)} 种并发症的症状",
            'relation': 'has_symptom'
        })
        
        # 构建回答
        answer_parts = [f"🔗 {actual_disease}并发症推理链\n"]
        answer_parts.append(f"\n第一步：{actual_disease} → 可能的并发症\n")
        answer_parts.append("常见并发症：" + "、".join(complications[:6]) + "\n")
        
        answer_parts.append(f"\n第二步：并发症 → 相关症状\n")
        for comp, symptoms in list(comp_symptoms.items())[:4]:
            answer_parts.append(f"\n{comp} 的症状：")
            answer_parts.append("、".join(symptoms[:5]))
        
        answer_parts.append("\n\n⚠️ 提示：如出现上述症状，请及时就医检查。")
        
        return {
            'success': True,
            'entity': disease,
            'actual_entity': actual_disease,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def _reason_disease_complication_treatment(self, disease: str, hop_info: Dict) -> Dict:
        """
        疾病 → 并发症 → 并发症的治疗方法
        """
        reasoning_steps = []
        
        actual_disease = self._find_disease_by_name(disease)
        if not actual_disease:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{disease}」的相关信息",
                'reasoning_path': []
            }
        
        # 查询并发症
        comp_query = """
        MATCH (d:Disease)-[r:acompany_with]->(comp:Disease)
        WHERE d.name = $disease
        RETURN d.name as disease, comp.name as complication
        LIMIT 8
        """
        comp_results = self.graph.run(comp_query, disease=actual_disease).data()
        
        if not comp_results:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{actual_disease}」的并发症信息",
                'reasoning_path': []
            }
        
        complications = list(set([r['complication'] for r in comp_results]))
        
        reasoning_steps.append({
            'step': 1,
            'action': f"查询「{actual_disease}」的并发症",
            'query': '疾病 → 并发症',
            'result': complications[:5],
            'relation': 'acompany_with'
        })
        
        # 查询并发症的治疗药物
        comp_treatments = {}
        for comp in complications[:5]:
            treat_query = """
            MATCH (d:Disease)-[:common_drug|recommand_drug]->(drug:Drug)
            WHERE d.name = $comp
            RETURN drug.name as drug
            LIMIT 5
            """
            treat_results = self.graph.run(treat_query, comp=comp).data()
            if treat_results:
                comp_treatments[comp] = [r['drug'] for r in treat_results]
        
        reasoning_steps.append({
            'step': 2,
            'action': '查询各并发症的治疗药物',
            'query': '并发症 → 药物',
            'result': f"找到 {len(comp_treatments)} 种并发症的药物",
            'relation': 'common_drug / recommand_drug'
        })
        
        # 构建回答
        answer_parts = [f"💊 {actual_disease}并发症治疗推理\n"]
        answer_parts.append(f"\n第一步：{actual_disease} → 并发症\n")
        answer_parts.append("需警惕的并发症：" + "、".join(complications[:6]) + "\n")
        
        answer_parts.append(f"\n第二步：并发症 → 治疗药物\n")
        for comp, drugs in list(comp_treatments.items())[:4]:
            answer_parts.append(f"\n{comp} 的常用药：")
            answer_parts.append("、".join(drugs[:4]))
        
        answer_parts.append("\n\n⚠️ 重要提示：用药需遵医嘱，切勿自行用药！")
        
        return {
            'success': True,
            'entity': disease,
            'actual_entity': actual_disease,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def _reason_disease_complication_food(self, disease: str, hop_info: Dict) -> Dict:
        """
        疾病 → 并发症 → 并发症的饮食
        """
        reasoning_steps = []
        
        # 使用智能匹配找到准确的疾病名称
        actual_disease = self._find_disease_by_name(disease)
        if not actual_disease:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{disease}」的相关信息",
                'reasoning_path': []
            }
        
        # 查询并发症
        comp_query = """
        MATCH (d:Disease)-[r:acompany_with]->(comp:Disease)
        WHERE d.name = $disease
        RETURN d.name as disease, comp.name as complication
        LIMIT 8
        """
        comp_results = self.graph.run(comp_query, disease=actual_disease).data()
        
        if not comp_results:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{actual_disease}」的并发症信息",
                'reasoning_path': []
            }
        
        complications = list(set([r['complication'] for r in comp_results]))
        
        reasoning_steps.append({
            'step': 1,
            'action': f"查询「{actual_disease}」的并发症",
            'query': '疾病 → 并发症',
            'result': complications[:5],
            'relation': 'acompany_with'
        })
        
        # 查询并发症的饮食建议
        comp_foods = {}
        for comp in complications[:5]:
            # 查询宜吃食物
            food_good_query = """
            MATCH (d:Disease)-[:do_eat|recommand_eat]->(f:Food)
            WHERE d.name = $comp
            RETURN f.name as food
            LIMIT 5
            """
            food_good_results = self.graph.run(food_good_query, comp=comp).data()
            good_foods = [r['food'] for r in food_good_results] if food_good_results else []
            
            # 查询忌吃食物
            food_bad_query = """
            MATCH (d:Disease)-[:no_eat]->(f:Food)
            WHERE d.name = $comp
            RETURN f.name as food
            LIMIT 5
            """
            food_bad_results = self.graph.run(food_bad_query, comp=comp).data()
            bad_foods = [r['food'] for r in food_bad_results] if food_bad_results else []
            
            if good_foods or bad_foods:
                comp_foods[comp] = {
                    'good': good_foods,
                    'bad': bad_foods
                }
        
        reasoning_steps.append({
            'step': 2,
            'action': '查询各并发症的饮食建议',
            'query': '并发症 → 饮食',
            'result': f"找到 {len(comp_foods)} 种并发症的饮食信息",
            'relation': 'do_eat / recommand_eat / no_eat'
        })
        
        # 构建回答
        answer_parts = [f"🍽️ {actual_disease}并发症饮食推理\n"]
        answer_parts.append(f"\n第一步：{actual_disease} → 并发症\n")
        answer_parts.append("需关注的并发症：" + "、".join(complications[:6]) + "\n")
        
        answer_parts.append(f"\n第二步：并发症 → 饮食建议\n")
        if comp_foods:
            for comp, foods in list(comp_foods.items())[:4]:
                answer_parts.append(f"\n{comp} 的饮食建议：\n")
                if foods['good']:
                    answer_parts.append(f"✅ 宜吃：{', '.join(foods['good'][:5])}\n")
                if foods['bad']:
                    answer_parts.append(f"❌ 忌吃：{', '.join(foods['bad'][:5])}\n")
        else:
            answer_parts.append("⚠️ 未找到详细的饮食信息，建议咨询专业医生或营养师。\n")
        
        answer_parts.append("\n💡 提示：饮食调理需结合个人情况，建议在医生指导下进行。")
        
        return {
            'success': True,
            'entity': disease,
            'actual_entity': actual_disease,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def _reason_disease_complication_prevention(self, disease: str, hop_info: Dict) -> Dict:
        """
        疾病 → 并发症 → 并发症的预防
        """
        reasoning_steps = []
        
        actual_disease = self._find_disease_by_name(disease)
        if not actual_disease:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{disease}」的相关信息",
                'reasoning_path': []
            }
        
        # 查询并发症
        comp_query = """
        MATCH (d:Disease)-[r:acompany_with]->(comp:Disease)
        WHERE d.name = $disease
        RETURN d.name as disease, comp.name as complication
        LIMIT 8
        """
        comp_results = self.graph.run(comp_query, disease=actual_disease).data()
        
        if not comp_results:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{actual_disease}」的并发症信息",
                'reasoning_path': []
            }
        
        complications = list(set([r['complication'] for r in comp_results]))
        
        reasoning_steps.append({
            'step': 1,
            'action': f"查询「{actual_disease}」的并发症",
            'query': '疾病 → 并发症',
            'result': complications[:5],
            'relation': 'acompany_with'
        })
        
        # 查询并发症的预防信息
        comp_preventions = {}
        for comp in complications[:5]:
            prevention_query = """
            MATCH (d:Disease)
            WHERE d.name = $comp
            RETURN d.prevent as prevention
            LIMIT 1
            """
            prevention_results = self.graph.run(prevention_query, comp=comp).data()
            if prevention_results and prevention_results[0].get('prevention'):
                prevention_text = prevention_results[0]['prevention']
                if prevention_text and prevention_text.strip():
                    comp_preventions[comp] = prevention_text.strip()
        
        reasoning_steps.append({
            'step': 2,
            'action': '查询各并发症的预防方法',
            'query': '并发症 → 预防',
            'result': f"找到 {len(comp_preventions)} 种并发症的预防信息",
            'relation': 'prevent (属性)'
        })
        
        # 构建回答
        answer_parts = [f"🛡️ {actual_disease}并发症预防推理\n"]
        answer_parts.append(f"\n第一步：{actual_disease} → 并发症\n")
        answer_parts.append("需预防的并发症：" + "、".join(complications[:6]) + "\n")
        
        answer_parts.append(f"\n第二步：并发症 → 预防方法\n")
        if comp_preventions:
            for comp, prevention in list(comp_preventions.items())[:4]:
                answer_parts.append(f"\n{comp} 的预防：\n")
                prevention_display = prevention[:200] + "..." if len(prevention) > 200 else prevention
                answer_parts.append(f"{prevention_display}\n")
        else:
            answer_parts.append("⚠️ 未找到详细的预防信息。\n")
            answer_parts.append("一般预防建议：\n")
            answer_parts.append("1. 定期体检，监测相关指标\n")
            answer_parts.append("2. 控制原发病，遵医嘱用药\n")
            answer_parts.append("3. 保持健康的生活方式\n")
            answer_parts.append("4. 如有异常症状，及时就医\n")
        
        answer_parts.append("\n💡 重要提示：预防措施需结合个人情况，建议咨询专业医生制定个性化预防方案。")
        
        return {
            'success': True,
            'entity': disease,
            'actual_entity': actual_disease,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def _reason_disease_complication(self, disease: str, hop_info: Dict) -> Dict:
        """
        疾病 → 并发症
        """
        reasoning_steps = []
        
        actual_disease = self._find_disease_by_name(disease)
        if not actual_disease:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{disease}」的相关信息",
                'reasoning_path': []
            }
        
        comp_query = """
        MATCH (d:Disease)-[:acompany_with]->(c:Disease)
        WHERE d.name = $disease
        RETURN d.name as disease, c.name as complication
        LIMIT 20
        """
        comp_results = self.graph.run(comp_query, disease=actual_disease).data()
        
        if not comp_results:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{actual_disease}」的并发症信息",
                'reasoning_path': []
            }
        
        complications = list(set([r['complication'] for r in comp_results]))
        
        reasoning_steps.append({
            'step': 1,
            'action': f"查询「{actual_disease}」的并发症",
            'query': '疾病 → 并发症',
            'result': complications[:10],
            'relation': 'acompany_with'
        })
        
        # 构建回答
        answer_parts = [f"🔗 {actual_disease}的并发症\n"]
        answer_parts.append(f"\n常见并发症：\n")
        
        # 按列表格式展示并发症
        for i, comp in enumerate(complications[:15], 1):
            answer_parts.append(f"{i}. {comp}\n")
        
        if len(complications) > 15:
            answer_parts.append(f"\n（共找到 {len(complications)} 种并发症，以上显示前15种）\n")
        
        answer_parts.append("\n⚠️ 提示：并发症需要及时预防和治疗，如有相关症状请及时就医。")
        
        return {
            'success': True,
            'entity': disease,
            'actual_entity': actual_disease,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def _reason_symptom_disease_check(self, symptom: str, hop_info: Dict) -> Dict:
        """
        症状 → 可能疾病 → 建议检查
        """
        reasoning_steps = []
        
        # 症状 → 疾病
        disease_query = """
        MATCH (d:Disease)-[:has_symptom]->(s:Symptom)
        WHERE s.name CONTAINS $symptom
        RETURN d.name as disease, s.name as symptom
        LIMIT 8
        """
        disease_results = self.graph.run(disease_query, symptom=symptom).data()
        
        if not disease_results:
            return {
                'success': False,
                'entity': symptom,
                'message': f"未找到「{symptom}」相关的疾病信息",
                'reasoning_path': []
            }
        
        diseases = list(set([r['disease'] for r in disease_results]))
        actual_symptom = disease_results[0]['symptom']
        
        reasoning_steps.append({
            'step': 1,
            'action': f"根据「{actual_symptom}」推断可能疾病",
            'query': '症状 → 疾病',
            'result': diseases[:5],
            'relation': 'has_symptom (反向)'
        })
        
        # 疾病 → 检查
        disease_checks = {}
        for disease in diseases[:5]:
            check_query = """
            MATCH (d:Disease)-[:need_check]->(c:Check)
            WHERE d.name = $disease
            RETURN c.name as check_item
            LIMIT 5
            """
            check_results = self.graph.run(check_query, disease=disease).data()
            if check_results:
                disease_checks[disease] = [r['check_item'] for r in check_results]
        
        reasoning_steps.append({
            'step': 2,
            'action': '查询各疾病所需检查',
            'query': '疾病 → 检查项目',
            'result': f"找到 {len(disease_checks)} 种疾病的检查建议",
            'relation': 'need_check'
        })
        
        # 构建回答
        answer_parts = [f"🔬 {actual_symptom}诊断推理\n"]
        answer_parts.append(f"\n第一步：{actual_symptom} → 可能疾病\n")
        answer_parts.append("可能相关的疾病：" + "、".join(diseases[:6]) + "\n")
        
        answer_parts.append(f"\n第二步：疾病 → 建议检查\n")
        for disease, checks in list(disease_checks.items())[:4]:
            answer_parts.append(f"\n{disease} 建议检查：")
            answer_parts.append("、".join(checks[:4]))
        
        answer_parts.append("\n\n💡 建议：如症状持续，请尽早就医进行专业诊断。")
        
        return {
            'success': True,
            'entity': symptom,
            'actual_entity': actual_symptom,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    # 这里有点问题
    def _reason_symptom_disease_department(self, symptom: str, hop_info: Dict) -> Dict:
        """
        症状 → 可能疾病 → 科室
        """
        reasoning_steps = []
        
        # 症状 → 疾病
        disease_query = """
        MATCH (d:Disease)-[:has_symptom]->(s:Symptom)
        WHERE s.name CONTAINS $symptom
        RETURN d.name as disease, s.name as symptom
        LIMIT 8
        """
        disease_results = self.graph.run(disease_query, symptom=symptom).data()
        
        if not disease_results:
            return {
                'success': False,
                'entity': symptom,
                'message': f"未找到「{symptom}」相关的疾病信息",
                'reasoning_path': []
            }
        
        diseases = list(set([r['disease'] for r in disease_results]))
        actual_symptom = disease_results[0]['symptom']
        
        reasoning_steps.append({
            'step': 1,
            'action': f"根据「{actual_symptom}」推断可能疾病",
            'query': '症状 → 疾病',
            'result': diseases[:5],
            'relation': 'has_symptom (反向)'
        })
        
        # 疾病 → 科室
        disease_depts = {}
        for disease in diseases[:5]:
            dept_query = """
            MATCH (d:Disease)-[:belongs_to]->(dept:Department)
            WHERE d.name = $disease
            RETURN dept.name as department
            LIMIT 3
            """
            dept_results = self.graph.run(dept_query, disease=disease).data()
            if dept_results:
                disease_depts[disease] = [r['department'] for r in dept_results]
        
        reasoning_steps.append({
            'step': 2,
            'action': '查询各疾病所属科室',
            'query': '疾病 → 科室',
            'result': f"找到 {len(disease_depts)} 种疾病的科室归属",
            'relation': 'belongs_to'
        })
        
        # 统计科室频率
        dept_count = {}
        for depts in disease_depts.values():
            for dept in depts:
                dept_count[dept] = dept_count.get(dept, 0) + 1
        
        # 按频率排序
        sorted_depts = sorted(dept_count.items(), key=lambda x: x[1], reverse=True)
        
        # 构建回答
        answer_parts = [f"🏥 {actual_symptom}就诊推理\n"]
        answer_parts.append(f"\n第一步：{actual_symptom} → 可能疾病\n")
        answer_parts.append("可能相关的疾病：" + "、".join(diseases[:6]) + "\n")
        
        answer_parts.append(f"\n第二步：疾病 → 推荐科室\n")
        if sorted_depts:
            top_dept = sorted_depts[0][0]
            answer_parts.append(f"首推科室：🎯 {top_dept}\n")
            if len(sorted_depts) > 1:
                other_depts = [d[0] for d in sorted_depts[1:4]]
                answer_parts.append(f"也可考虑：{', '.join(other_depts)}\n")
        
        answer_parts.append("\n详细分析：")
        for disease, depts in list(disease_depts.items())[:3]:
            answer_parts.append(f"\n- {disease} → {', '.join(depts)}")
        
        return {
            'success': True,
            'entity': symptom,
            'actual_entity': actual_symptom,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def _reason_disease_drug_department(self, disease: str, hop_info: Dict) -> Dict:
        """
        复合查询：疾病 → 药物 + 科室 (同时回答)
        """
        reasoning_steps = []
        
        # 使用智能匹配找到准确的疾病名称
        actual_disease = self._find_disease_by_name(disease)
        if not actual_disease:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{disease}」的相关信息",
                'reasoning_path': []
            }
        
        # 查询药物
        drug_query = """
        MATCH (d:Disease)-[:common_drug|recommand_drug]->(drug:Drug)
        WHERE d.name = $disease
        RETURN d.name as disease, drug.name as drug
        LIMIT 10
        """
        drug_results = self.graph.run(drug_query, disease=actual_disease).data()
        
        # 查询科室
        dept_query = """
        MATCH (d:Disease)-[:belongs_to]->(dept:Department)
        WHERE d.name = $disease
        RETURN d.name as disease, dept.name as department
        LIMIT 5
        """
        dept_results = self.graph.run(dept_query, disease=actual_disease).data()
        
        if not drug_results and not dept_results:
            return {
                'success': False,
                'entity': disease,
                'message': f"未找到「{actual_disease}」的相关信息",
                'reasoning_path': []
            }
        
        drugs = list(set([r['drug'] for r in drug_results])) if drug_results else []
        depts = list(set([r['department'] for r in dept_results])) if dept_results else []
        
        reasoning_steps.append({
            'step': 1,
            'action': f"查询「{actual_disease}」的用药和科室",
            'query': '疾病 → 药物 + 科室',
            'result': {'drugs': len(drugs), 'departments': len(depts)},
            'relation': 'common_drug + belongs_to'
        })
        
        # 构建回答
        answer_parts = [f"📋 {actual_disease}综合查询\n"]
        
        if depts:
            answer_parts.append(f"\n🏥 就诊科室\n")
            answer_parts.append(f"推荐科室：{', '.join(depts)}\n")
        
        if drugs:
            answer_parts.append(f"\n💊 常用药物\n")
            answer_parts.append(f"参考用药：{', '.join(drugs[:8])}")
            if len(drugs) > 8:
                answer_parts.append(f"（等共 {len(drugs)} 种）")
        
        answer_parts.append("\n\n⚠️ 提示：具体用药请遵医嘱！")
        
        return {
            'success': True,
            'entity': disease,
            'actual_entity': actual_disease,
            'answer': '\n'.join(answer_parts),
            'reasoning_path': reasoning_steps,
            'hop_info': hop_info
        }
    
    def get_comprehensive_analysis(self, disease: str) -> Dict:
        """
        综合分析：获取疾病的全景信息
        用于展示知识图谱的完整推理能力
        """
        if not self.connected:
            return {'success': False, 'message': '数据库未连接'}
        
        # 验证疾病存在
        verify_query = """
        MATCH (d:Disease) WHERE d.name CONTAINS $disease
        RETURN d.name LIMIT 1
        """
        verify_result = self.graph.run(verify_query, disease=disease).data()
        if not verify_result:
            return {'success': False, 'message': f'未找到「{disease}」相关信息'}
        
        actual_disease = verify_result[0]['name']
        
        # 收集全景信息
        analysis = {
            'disease': actual_disease,
            'symptoms': [],
            'drugs': [],
            'foods_good': [],
            'foods_bad': [],
            'checks': [],
            'departments': [],
            'complications': [],
            'prevention': '',
            'cause': '',
        }
        
        # 症状
        symp_query = """
        MATCH (d:Disease)-[:has_symptom]->(s:Symptom) 
        WHERE d.name = $disease RETURN s.name as name LIMIT 10
        """
        analysis['symptoms'] = [r['name'] for r in self.graph.run(symp_query, disease=actual_disease).data()]
        
        # 药物
        drug_query = """
        MATCH (d:Disease)-[:common_drug|recommand_drug]->(dr:Drug) 
        WHERE d.name = $disease RETURN dr.name as name LIMIT 10
        """
        analysis['drugs'] = [r['name'] for r in self.graph.run(drug_query, disease=actual_disease).data()]
        
        # 饮食建议
        food_good_query = """
        MATCH (d:Disease)-[:do_eat|recommand_eat]->(f:Food) 
        WHERE d.name = $disease RETURN f.name as name LIMIT 8
        """
        analysis['foods_good'] = [r['name'] for r in self.graph.run(food_good_query, disease=actual_disease).data()]
        
        food_bad_query = """
        MATCH (d:Disease)-[:no_eat]->(f:Food) 
        WHERE d.name = $disease RETURN f.name as name LIMIT 8
        """
        analysis['foods_bad'] = [r['name'] for r in self.graph.run(food_bad_query, disease=actual_disease).data()]
        
        # 检查
        check_query = """
        MATCH (d:Disease)-[:need_check]->(c:Check) 
        WHERE d.name = $disease RETURN c.name as name LIMIT 8
        """
        analysis['checks'] = [r['name'] for r in self.graph.run(check_query, disease=actual_disease).data()]
        
        # 科室
        dept_query = """
        MATCH (d:Disease)-[:belongs_to]->(dep:Department) 
        WHERE d.name = $disease RETURN dep.name as name LIMIT 5
        """
        analysis['departments'] = [r['name'] for r in self.graph.run(dept_query, disease=actual_disease).data()]
        
        # 并发症
        comp_query = """
        MATCH (d:Disease)-[:acompany_with]->(c:Disease) 
        WHERE d.name = $disease RETURN c.name as name LIMIT 8
        """
        analysis['complications'] = [r['name'] for r in self.graph.run(comp_query, disease=actual_disease).data()]
        
        # 属性信息
        prop_query = """
        MATCH (d:Disease) WHERE d.name = $disease 
        RETURN d.prevent as prevent, d.cause as cause
        """
        prop_result = self.graph.run(prop_query, disease=actual_disease).data()
        if prop_result:
            analysis['prevention'] = prop_result[0].get('prevent', '') or ''
            analysis['cause'] = prop_result[0].get('cause', '') or ''
        
        analysis['success'] = True
        return analysis


if __name__ == '__main__':
    reasoner = KnowledgeReasoner()
    