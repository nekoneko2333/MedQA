"""
搜索答案

增加了答案模板
更友好的回答模式

"""
from py2neo import Graph
import random
from utils.logger import get_logger

logger = get_logger(__name__)


class AnswerSearcher:
    def __init__(self):
        # 初始化 Neo4j 连接
        from os import getenv
        neo_url = getenv('NEO4J_BOLT_URL', 'bolt://localhost:7687')
        neo_user = getenv('NEO4J_USER', 'neo4j')
        neo_pass = getenv('NEO4J_PASSWORD', '此处填入密码')
        try:
            self.g = Graph(neo_url, auth=(neo_user, neo_pass))
        except Exception as e:
            logger.error(f"无法连接到 Neo4j: {e}")
            self.g = None
        self.num_limit = 20
        
        # 多样化回复模板
        self.templates = {
            'disease_symptom': [
                '🩺 {0}的常见症状包括：{1}',
                '📋 患有{0}时，通常会出现以下症状：{1}',
                '💊 {0}的主要临床表现有：{1}',
                '🔍 如果您患有{0}，可能会有这些症状：{1}'
            ],
            'symptom_disease': [
                '🏥 出现{0}，可能与以下疾病有关：{1}',
                '⚠️ {0}可能是以下疾病的表现：{1}',
                '🔬 有{0}时，建议排查以下疾病：{1}'
            ],
            'disease_cause': [
                '🔍 {0}的可能病因包括：{1}',
                '📖 {0}通常由以下原因引起：{1}',
                '💡 导致{0}的常见原因有：{1}'
            ],
            'disease_prevent': [
                '🛡️ 预防{0}的措施包括：{1}',
                '💪 要预防{0}，建议：{1}',
                '✅ {0}的预防方法：{1}'
            ],
            'disease_lasttime': [
                '⏱️ {0}的治疗周期通常为：{1}',
                '📅 {0}一般需要治疗：{1}',
                '🕐 {0}的康复时间大约是：{1}'
            ],
            'disease_cureway': [
                '💊 {0}的治疗方法包括：{1}',
                '🏥 针对{0}，可以采取以下治疗方式：{1}',
                '✨ {0}常用的治疗方案有：{1}'
            ],
            'symptom_cureway': [
                '💊 出现{0}症状时，可以采取以下治疗方法：{1}',
                '🏥 针对{0}，建议的治疗方式包括：{1}',
                '✨ {0}的常用治疗方案：{1}'
            ],
            'disease_cureprob': [
                '📊 {0}的治愈率大约为：{1}（仅供参考）',
                '💯 {0}的治愈概率约为：{1}',
                '📈 根据统计，{0}的治愈率约为：{1}'
            ],
            'disease_easyget': [
                '👥 {0}的易感人群包括：{1}',
                '⚠️ 以下人群更容易患{0}：{1}',
                '🎯 {0}好发于：{1}'
            ],
            'disease_desc': [
                '📚 关于{0}：{1}',
                '💡 {0}简介：{1}',
                '📖 {0}是一种{1}'
            ],
            'disease_acompany': [
                '⚠️ {0}可能伴随以下并发症：{1}',
                '🔗 {0}常见的并发症有：{1}',
                '❗ 患有{0}时，需警惕以下并发症：{1}'
            ],
            'disease_not_food': [
                '🚫 患有{0}时应避免食用：{1}',
                '❌ {0}患者忌食：{1}',
                '⛔ 如果您有{0}，请不要吃：{1}'
            ],
            'disease_do_food': [
                '✅ {0}患者宜食：{1}\n\n🍽️ 推荐食谱：{2}',
                '🥗 患有{0}时建议多吃：{1}\n\n👨‍🍳 推荐食谱：{2}',
                '💚 {0}患者可以多吃：{1}\n\n📋 食谱推荐：{2}'
            ],
            'food_not_disease': [
                '⚠️ 患有以下疾病的人不宜食用{1}：{0}',
                '🚫 {1}不适合以下疾病患者食用：{0}',
                '❌ 如果您有以下疾病，请避免吃{1}：{0}'
            ],
            'food_do_disease': [
                '✅ {1}适合以下疾病患者食用：{0}',
                '💚 患有以下疾病时可以多吃{1}：{0}',
                '🥗 {1}对以下疾病患者有益：{0}'
            ],
            'disease_drug': [
                '💊 {0}常用药物包括：{1}',
                '💉 治疗{0}的药物有：{1}',
                '🏥 {0}患者常用的药品：{1}'
            ],
            'symptom_drug': [
                '💊 出现{0}症状时，可以使用以下药物：{1}',
                '💉 针对{0}，建议的药物包括：{1}',
                '🏥 {0}的常用药品：{1}'
            ],
            'drug_disease': [
                '💊 {0}主要用于治疗：{1}',
                '🏥 {0}可以治疗以下疾病：{1}',
                '📋 {0}的适应症包括：{1}'
            ],
            'disease_check': [
                '🔬 {0}的诊断检查项目包括：{1}',
                '🏥 怀疑{0}时，建议做以下检查：{1}',
                '📋 确诊{0}通常需要：{1}'
            ],
            'check_disease': [
                '🔬 {0}检查可以诊断以下疾病：{1}',
                '📋 通过{0}可以检查出：{1}',
                '🏥 {0}主要用于诊断：{1}'
            ],
            'disease_department': [
                '🏥 {0}建议挂：{1}',
                '📋 {0}应该挂：{1}',
                '💡 患有{0}时，建议就诊：{1}'
            ]
            ,
            'drug_producer': [
                '🏭 {0} 的生产厂家包括：{1}',
                '📦 {0}（药品）由以下厂家生产：{1}',
                '🔎 查询到 {0} 的生产厂商：{1}'
            ]
        }

    def search_main(self, sqls):
        """执行cypher查询，并返回相应结果"""
        if not self.g:
            logger.error("Neo4j 未初始化，（AnswerSearcher.g is None）")
            return []
        final_answers = []
        seen_answer_keys = set() # 用于去重
        for sql_ in sqls:
            question_type = sql_['question_type']
            queries = sql_['sql']
            answers = []
            for query in queries:
                try:
                    ress = self.g.run(query).data()
                    answers += ress
                    if not ress and question_type == 'symptom_disease':
                        logger.warning(f"症状查询结果为空，查询语句: {query}")
                except Exception as e:
                    logger.error(f"查询错误: {e}, 查询语句: {query}")
            final_answer = self.answer_prettify(question_type, answers)
            if final_answer:
                # 基于答案的关键内容生成去重key
                answer_key = self._generate_answer_key(question_type, answers)
                if answer_key not in seen_answer_keys:
                    seen_answer_keys.add(answer_key)
                    final_answers.append(final_answer)
        return final_answers
    
    def _generate_answer_key(self, question_type, answers):
        """生成答案的key用于去重"""
        if not answers:
            return ""
        # 提取实体名称和结果列表
        key_parts = []
        if question_type == 'disease_department':
            # 对于科室查询，key是疾病名+科室名列表
            disease = answers[0].get('m.name', '') if answers else ''
            depts = sorted(set([a.get('n.name', '') for a in answers if a.get('n.name')]))
            key_parts = [disease, ','.join(depts)]
        else:
            # 对于其他类型，使用问题类型+关键实体
            key_parts = [question_type]
            for a in answers[:3]:  # 只取前3个结果作为key
                for k, v in a.items():
                    if v and k in ['m.name', 'n.name', 'd.name', 's.name']:
                        key_parts.append(str(v))
        return '|'.join(key_parts)

    def get_template(self, question_type):
        """回复模板从列表里随机挑"""
        templates = self.templates.get(question_type, ['{0}: {1}'])
        return random.choice(templates)

    def answer_prettify(self, question_type, answers):
        """根据问题类型格式化答案"""
        if not answers:
            return ''
        
        final_answer = ''
        template = self.get_template(question_type)
        
        if question_type == 'disease_symptom':
            desc = [i['n.name'] for i in answers if i.get('n.name')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'symptom_disease':
            desc = [i['m.name'] for i in answers if i.get('m.name')]
            subject = answers[0].get('n.name', '') if answers else ''
            # 如果subject为空，尝试从查询中推断（通常症状名会在查询中）
            if not subject and answers:
                # 尝试从其他字段获取
                for ans in answers:
                    if ans.get('n.name'):
                        subject = ans.get('n.name')
                        break
            
            if desc:
                unique_diseases = []
                seen = set()
                for d in desc:
                    if d not in seen:
                        unique_diseases.append(d)
                        seen.add(d)
                
                # 只返回前5-8个最相关的疾病
                limit = min(8, len(unique_diseases))
                limited_diseases = unique_diseases[:limit]
                
                # 如果subject为空，使用"该症状"
                if not subject:
                    subject = "该症状"
                
                if len(unique_diseases) > limit:
                    final_answer = template.format(subject, '、'.join(limited_diseases)) + f"\n\n💡 提示：共找到{len(unique_diseases)}种相关疾病，以上为最常见的{limit}种。建议结合其他症状或前往医院进一步诊断。"
                else:
                    final_answer = template.format(subject, '、'.join(limited_diseases))
            else:
                if not subject:
                    subject = "该症状"
                final_answer = f"🤔 抱歉，暂时没有找到与{subject}相关的疾病信息。建议：\n1. 检查症状名称是否正确\n2. 尝试使用更具体的症状描述\n3. 结合其他症状一起查询\n4. 咨询专业医生"

        elif question_type == 'disease_cause':
            desc = [i['m.cause'] for i in answers if i.get('m.cause')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '\n'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_prevent':
            desc = [i['m.prevent'] for i in answers if i.get('m.prevent')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '\n'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_lasttime':
            desc = [i['m.cure_lasttime'] for i in answers if i.get('m.cure_lasttime')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_cureway':
            desc = []
            for i in answers:
                if i.get('m.cure_way'):
                    if isinstance(i['m.cure_way'], list):
                        desc.extend(i['m.cure_way'])
                    else:
                        desc.append(i['m.cure_way'])
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))
        
        elif question_type == 'symptom_cureway':
            # 症状对应的疾病的治疗方法
            disease_cureways = {}
            for i in answers:
                disease = i.get('d.name', '')
                cure_way = i.get('d.cure_way', '')
                if disease and cure_way:
                    if disease not in disease_cureways:
                        disease_cureways[disease] = []
                    if isinstance(cure_way, list):
                        disease_cureways[disease].extend(cure_way)
                    else:
                        disease_cureways[disease].append(cure_way)
            
            if disease_cureways:
                # 格式化：疾病1：治疗方法1、治疗方法2；疾病2：治疗方法1...
                cureway_list = []
                for disease, cures in list(disease_cureways.items())[:5]:  # 只显示前5个疾病
                    unique_cures = list(set(cures))[:3]  # 每个疾病最多3个治疗方法
                    cureway_list.append(f"{disease}：{'、'.join(unique_cures)}")
                
                subject = answers[0].get('n.name', '') if answers else '该症状'
                if not subject:
                    # 如果没有症状名，尝试从原始查询中提取
                    subject = '该症状'
                
                final_answer = template.format(subject, '；'.join(cureway_list))

        elif question_type == 'disease_cureprob':
            desc = [i['m.cured_prob'] for i in answers if i.get('m.cured_prob')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_easyget':
            desc = [i['m.easy_get'] for i in answers if i.get('m.easy_get')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_desc':
            desc = [i['m.desc'] for i in answers if i.get('m.desc')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '\n'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_acompany':
            desc1 = [i['n.name'] for i in answers if i.get('n.name')]
            desc2 = [i['m.name'] for i in answers if i.get('m.name')]
            subject = answers[0].get('m.name', '')
            desc = [i for i in desc1 + desc2 if i != subject]
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_not_food':
            desc = [i['n.name'] for i in answers if i.get('n.name')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_do_food':
            do_desc = [i['n.name'] for i in answers if i.get('r.name') == '宜吃' and i.get('n.name')]
            recommand_desc = [i['n.name'] for i in answers if i.get('r.name') == '推荐食谱' and i.get('n.name')]
            subject = answers[0].get('m.name', '')
            if do_desc or recommand_desc:
                final_answer = template.format(
                    subject, 
                    '、'.join(list(set(do_desc))[:self.num_limit]) or '暂无数据',
                    '、'.join(list(set(recommand_desc))[:self.num_limit]) or '暂无数据'
                )

        elif question_type == 'food_not_disease':
            desc = [i['m.name'] for i in answers if i.get('m.name')]
            subject = answers[0].get('n.name', '')
            if desc:
                final_answer = template.format('、'.join(list(set(desc))[:self.num_limit]), subject)

        elif question_type == 'food_do_disease':
            desc = [i['m.name'] for i in answers if i.get('m.name')]
            subject = answers[0].get('n.name', '')
            if desc:
                final_answer = template.format('、'.join(list(set(desc))[:self.num_limit]), subject)

        elif question_type == 'disease_drug':
            desc = [i['n.name'] for i in answers if i.get('n.name')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))
        
        elif question_type == 'symptom_drug':
            # 症状对应的疾病的用药
            symptom_drugs = {}
            for i in answers:
                disease = i.get('d.name', '')
                drug = i.get('n.name', '')
                symptom = i.get('s.name', '')
                if disease and drug:
                    if disease not in symptom_drugs:
                        symptom_drugs[disease] = []
                    if drug not in symptom_drugs[disease]:
                        symptom_drugs[disease].append(drug)
            
            if symptom_drugs:
                # 格式化：疾病1：药物1、药物2；疾病2：药物1...
                drug_list = []
                for disease, drugs in list(symptom_drugs.items())[:5]:  # 只显示前5个疾病
                    unique_drugs = list(set(drugs))[:3]  # 每个疾病最多3个药物
                    drug_list.append(f"{disease}：{'、'.join(unique_drugs)}")
                
                subject = answers[0].get('s.name', '') if answers else '该症状'
                if not subject:
                    subject = '该症状'
                
                final_answer = template.format(subject, '；'.join(drug_list))

        elif question_type == 'drug_disease':
            desc = [i['m.name'] for i in answers if i.get('m.name')]
            subject = answers[0].get('n.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'drug_producer':
            # 查询药品的生产厂家，sql 返回字段为 n.name (drug), m.name (producer)
            producers = [i.get('m.name') for i in answers if i.get('m.name')]
            drug = answers[0].get('n.name', '') if answers else ''
            if producers:
                unique_producers = list(dict.fromkeys(producers))  # 保持顺序且去重
                final_answer = template.format(drug or '该药品', '、'.join(unique_producers[:self.num_limit]))
            else:
                final_answer = f"🤔 抱歉，虽然识别到您在问 [{drug or '该药品'}]，但知识库中暂时没有生产厂家相关数据。"

        elif question_type == 'disease_check':
            desc = [i['n.name'] for i in answers if i.get('n.name')]
            subject = answers[0].get('m.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'check_disease':
            desc = [i['m.name'] for i in answers if i.get('m.name')]
            subject = answers[0].get('n.name', '')
            if desc:
                final_answer = template.format(subject, '、'.join(list(set(desc))[:self.num_limit]))

        elif question_type == 'disease_department':
            desc = [i['n.name'] for i in answers if i.get('n.name')]
            subject = answers[0].get('m.name', '') if answers else ''
            if desc:
                unique_desc = list(set(desc))
                final_answer = template.format(subject, '、'.join(unique_desc[:self.num_limit]))
            else:
                final_answer = f"🤔 抱歉，暂时没有找到{subject}的科室信息。建议咨询医院导诊台或使用在线挂号系统。"

        return final_answer


if __name__ == '__main__':
    searcher = AnswerSearcher()

