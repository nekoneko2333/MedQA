"""
实体识别和意图分类

"""
import os
import ahocorasick

class QuestionClassifier:
    def __init__(self):
        # 获取根目录
        cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 特征词路径
        self.disease_path = os.path.join(cur_dir, 'dict', 'disease.txt')
        self.department_path = os.path.join(cur_dir, 'dict', 'department.txt')
        self.check_path = os.path.join(cur_dir, 'dict', 'check.txt')
        self.drug_path = os.path.join(cur_dir, 'dict', 'drug.txt')
        self.food_path = os.path.join(cur_dir, 'dict', 'food.txt')
        self.producer_path = os.path.join(cur_dir, 'dict', 'producer.txt')
        self.symptom_path = os.path.join(cur_dir, 'dict', 'symptom.txt')
        self.deny_path = os.path.join(cur_dir, 'dict', 'deny.txt')
        # 加载特征词
        self.disease_wds= [i.strip() for i in open(self.disease_path,encoding="utf-8") if i.strip()]#encoding="utf-8"
        self.department_wds= [i.strip() for i in open(self.department_path,encoding="utf-8") if i.strip()]
        self.check_wds= [i.strip() for i in open(self.check_path,encoding="utf-8") if i.strip()]
        self.drug_wds= [i.strip() for i in open(self.drug_path,encoding="utf-8") if i.strip()]
        self.food_wds= [i.strip() for i in open(self.food_path,encoding="utf-8") if i.strip()]
        self.producer_wds= [i.strip() for i in open(self.producer_path,encoding="utf-8") if i.strip()]
        self.symptom_wds= [i.strip() for i in open(self.symptom_path,encoding="utf-8") if i.strip()]
        # 同义词文件
        self.synonym_path = os.path.join(cur_dir, 'dict', 'synonym.txt')
        self.synonym_map = self._load_synonym_map()
        # 按长度降序排列同义词，优先替换长词避免部分匹配
        self._synonym_keys_sorted = sorted(self.synonym_map.keys(), key=lambda x: len(x), reverse=True)
        self.region_words = set(self.department_wds + self.disease_wds + self.check_wds + self.drug_wds + self.food_wds + self.producer_wds + self.symptom_wds)
        self.deny_words = [i.strip() for i in open(self.deny_path,encoding="utf-8") if i.strip()]
        # 确保否定词包含关键项
        for _w in ['不适合', '不能', '忌']:
            if _w not in self.deny_words:
                self.deny_words.append(_w)
        # 构造领域actree
        self.region_tree = self.build_actree(list(self.region_words))
        # 构建词典
        self.wdtype_dict = self.build_wdtype_dict()
        # 问句疑问词
        self.symptom_qwds = [
            '症状', '表征', '现象', '症候', '表现', '哪些病', '什么病', '可能是什么病', '常见于', '会是什么病',
            '不舒服', '哪里不对劲', '异常', '表现为', '症状有哪些', '症状是啥', '表现症状', '体征', '临床表现',
            '有哪些异常', '哪里出问题', '一般会怎样', '通常会怎样'
        ]

        self.cause_qwds = [
            '原因', '成因', '为什么', '怎么会', '怎样才', '咋样才', '怎样会', '如何会', '为啥', '为何', 
            '如何才会', '怎么才会', '会导致', '会造成', '怎么了',
            '原因是什么', '是什么原因', '为什么会这样', '为什么会那样', '什么导致的', '何因', '什么引起',
            '致病因素', '诱因', '形成原因', '怎么形成的', '如何造成', '怎么造成', '怎么引发', '怎么产生'
        ]

        self.acompany_qwds = [
            '并发症', '并发', '一起发生', '一并发生', '一起出现', '一并出现', '一同发生', '一同出现', 
            '伴随发生', '伴随', '共现',
            '伴随症状', '通常伴随', '会不会带来', '可能还会出现', '会伴随哪些', '伴发', '合并症',
            '一起有啥', '同时会怎样', '相关症状'
        ]

        self.food_qwds = [
            '饮食', '饮用', '吃', '食', '伙食', '膳食', '喝', '菜', '忌口', '补品', '保健品', 
            '食谱', '菜谱', '食用', '食物','补品','有益', '好处', '适合',
            '能吃什么', '不能吃什么', '忌吃', '宜吃', '饮食注意', '饮食建议', '吃什么好', '吃啥', '能不能吃',
            '饮食禁忌', '饮食搭配', '饮食上注意', '喝什么好', '适宜食物', '有益食物', '补什么', '补啥'
        ]

        self.drug_qwds = [
            '药', '药品', '用药', '胶囊', '口服液', '炎片',
            '药丸', '药剂', '吃什么药', '要吃什么药', '药物', '用啥药', '治疗药物', '药片', '药膏', '注射剂',
            '处方药', '非处方药', '药名', '药的作用'
        ]

        self.prevent_qwds = [
            '预防', '防范', '抵制', '抵御', '防止','躲避','逃避','避开','免得','逃开','避开','避掉','躲开','躲掉','绕开',
            '怎样才能不', '怎么才能不', '咋样才能不','咋才能不', '如何才能不',
            '怎样才不', '怎么才不', '咋样才不','咋才不', '如何才不',
            '怎样才可以不', '怎么才可以不', '咋样才可以不', '咋才可以不', '如何可以不',
            '怎样才可不', '怎么才可不', '咋样才可不', '咋才可不', '如何可不',
            '怎么预防', '如何预防', '怎样避免', '避免办法', '如何减少风险', '怎样降低风险', '预防措施',
            '需要注意什么', '如何防护', '防护方法', '怎样才安全', '如何保护自己', '避免什么', '注意事项'
        ]

        self.lasttime_qwds = [
            '周期', '多久', '多长时间', '多少时间', '几天', '几年', '多少天', '多少小时', 
            '几个小时', '多少年',
            '时间长短', '要多久', '会持续多久', '多久可以好', '多长', '多长才好', '能撑多久', '一般持续多久'
        ]

        self.cureway_qwds = [
            '怎么治疗', '如何医治', '怎么医治', '怎么治', '怎么医', '如何治', '医治方式', 
            '疗法', '咋治', '怎么办', '咋办', '咋治', '治疗方法', '治疗措施', '办法', '怎么弄',
            '治疗方案', '如何处理', '怎么处理', '治疗手段', '治疗步骤', '治疗建议', '如何治疗',
            '治疗需要什么', '治法', '用什么方式治', '怎样治', '需不需要治疗', '怎么医好'
        ]

        self.cureprob_qwds = [
            '多大概率能治好', '多大几率能治好', '治好希望大么', '几率', '几成', '比例', '可能性', 
            '能治', '可治', '可以治', '可以医', '治愈率', '成活率',
            '治好概率', '成功率', '治愈可能', '治愈机会', '痊愈率', '痊愈可能性', '治好的机会大吗',
            '有希望吗', '治好难不难', '能不能治好', '治好的几率'
        ]

        self.easyget_qwds = [
            '易感人群', '容易感染', '易发人群', '什么人', '哪些人', '感染', '染上', '得上', '高发人群', 
            '多发人群', '多发',
            '谁容易得', '哪些人容易得', '什么人群容易', '高危人群', '风险人群', '容易患病的人', 
            '好发人群', '易患人群'
        ]

        self.check_qwds = [
            '检查', '检查项目', '查出', '检查', '测出', '试出',
            '做什么检查', '检查哪些', '检测', '检测项目', '怎么查', '如何查', '需要检查吗',
            '诊断方法', '检测方法', '要做什么检查', '检查手段', '查什么', '查得出来吗'
        ]

        self.belong_qwds = [
            '属于什么科', '属于', '什么科', '科室', '挂哪个科', '哪个科', '去哪个科',' 什么科室','挂哪个科室',
            '看什么科', '挂什么科', '应该挂哪个科', '属于哪个科室', '什么科看', '哪个科负责', 
            '看哪个科', '属于哪个科'
        ]

        self.drug_disease_qwds = [
            '适用于', '主治', '治疗什么', '治啥', '功能主治',
            '用于治疗', '针对什么', '治疗作用', '有什么疗效', '治什么病', '适应症', 
            '适用范围', '对什么有效'
        ]

        self.producer_qwds = [
            '厂家', '生产厂家', '生产商', '生产厂商', '供应商', '哪里产的',
            '哪家公司生产', '哪个厂做的', '来源', '产地', '生产单位', '制造商',
            '厂家信息', '生产哪里'
        ]

        self.cure_qwds = [
            '治疗什么', '治啥', '治疗啥', '医治啥', '治愈啥', '主治啥', '主治什么', 
            '有什么用', '有何用', '用处', '用途', '有什么好处', '有什么益处', 
            '有何益处', '用来', '用来做啥', '用来作甚', '需要', '要',
            '干什么的', '有什么作用', '效用', '功效', '能用来做什么', '能用来治疗什么', 
            '起什么作用', '用于什么', '功用', '用途是什么', '作用是啥', '有什么效果'
        ]

        return

    '''分类主函数'''
    def classify(self, question):
        data = {}
        medical_dict = self.check_medical(question)
        if not medical_dict:
            return {}
        data['args'] = medical_dict

        # 遍历 medical_dict，处理 disease/symptom 混合类型
        disambiguated_dict = {}
        for wd, types in medical_dict.items():
            # 如果既是疾病又是症状
            if 'disease' in types and 'symptom' in types:
                if self.check_words(self.symptom_qwds, question):
                    disambiguated_dict[wd] = ['symptom']
                elif self.check_words(self.cureway_qwds, question):
                    disambiguated_dict[wd] = ['disease']
                else:
                    disambiguated_dict[wd] = types
            else:
                disambiguated_dict[wd] = types

        # 收集问句涉及的实体类型
        types = []
        for type_ in disambiguated_dict.values():
            types += type_

        # 检测到多个症状且无其它实体时，自动触发 symptom_disease 意图
        symptom_entities = [wd for wd, tps in disambiguated_dict.items() if 'symptom' in tps]
        other_types = set()
        for tps in disambiguated_dict.values():
            for tp in tps:
                if tp != 'symptom':
                    other_types.add(tp)
        auto_symptom_intent = (len(symptom_entities) >= 2 and len(other_types) == 0)

        question_types = []
        # 如果自动触发多症状意图，优先加入
        if auto_symptom_intent:
            question_types.append('symptom_disease')

        # 症状查疾病（优先处理症状且无疾病时）
        if self.check_words(self.symptom_qwds, question) and ('symptom' in types):
            if 'symptom_disease' not in question_types:
                question_types.append('symptom_disease')
        # 疾病查症状
        if self.check_words(self.symptom_qwds, question) and ('disease' in types):
            question_types.append('disease_symptom')
        
        # 药品相关：查药品对应的疾病、查生产厂家
        if 'drug' in types:
            if hasattr(self, 'drug_disease_qwds') and self.check_words(self.drug_disease_qwds, question):
                question_types.append('drug_disease')
            
            if hasattr(self, 'producer_qwds') and self.check_words(self.producer_qwds, question):
                question_types.append('drug_producer')
        # 原因
        if self.check_words(self.cause_qwds, question) and ('disease' in types):
            question_types.append('disease_cause')
        # 并发症
        if self.check_words(self.acompany_qwds, question) and ('disease' in types):
            question_types.append('disease_acompany')
        # 推荐食品
        if self.check_words(self.food_qwds, question) and 'disease' in types:
            deny_status = self.check_words(self.deny_words, question)
            if deny_status:
                question_types.append('disease_not_food')
            else:
                question_types.append('disease_do_food')
        # 已知食物找疾病
        # 如果识别出 food 实体，则根据否定词决定方向）
        if 'food' in types:
            if self.check_words(self.deny_words, question):
                question_types.append('food_not_disease')
            else:
                if self.check_words(self.cure_qwds + self.food_qwds, question):
                    question_types.append('food_do_disease')
        # 推荐药品
        if self.check_words(self.drug_qwds, question) and 'disease' in types:
            question_types.append('disease_drug')
        # 药品治啥病
        if self.check_words(self.cure_qwds, question) and 'drug' in types:
            question_types.append('drug_disease')
        # 疾病接受检查项目
        if self.check_words(self.check_qwds, question) and 'disease' in types:
            question_types.append('disease_check')
        # 已知检查项目查相应疾病
        if self.check_words(self.check_qwds+self.cure_qwds, question) and 'check' in types:
            question_types.append('check_disease')
        #　症状预防
        if self.check_words(self.prevent_qwds, question) and 'disease' in types:
            question_types.append('disease_prevent')
        # 疾病医疗周期
        if self.check_words(self.lasttime_qwds, question) and 'disease' in types:
            question_types.append('disease_lasttime')
        # 疾病治疗方式
        if self.check_words(self.cureway_qwds, question) and 'disease' in types:
            question_types.append('disease_cureway')
        # 疾病治愈可能性
        if self.check_words(self.cureprob_qwds, question) and 'disease' in types:
            question_types.append('disease_cureprob')
        # 疾病易感染人群
        if self.check_words(self.easyget_qwds, question) and 'disease' in types:
            question_types.append('disease_easyget')
        # 挂号科室
        if self.check_words(self.belong_qwds, question) and 'disease' in types:
            question_types.append('disease_department')

        # 若没有查到相关的外部查询信息
        if not question_types:
            if 'disease' in types:
                question_types = ['disease_desc']
            elif 'symptom' in types:
                question_types = ['symptom_disease']
            elif 'drug' in types:
                question_types = ['drug_desc']

        data['question_types'] = question_types
        return data

    '''构造词对应的类型'''
    def build_wdtype_dict(self):
        wd_dict = dict()
        for wd in self.region_words:
            wd_dict[wd] = []
            if wd in self.disease_wds:
                wd_dict[wd].append('disease')
            if wd in self.department_wds:
                wd_dict[wd].append('department')
            if wd in self.check_wds:
                wd_dict[wd].append('check')
            if wd in self.drug_wds:
                wd_dict[wd].append('drug')
            if wd in self.food_wds:
                wd_dict[wd].append('food')
            if wd in self.symptom_wds:
                wd_dict[wd].append('symptom')
            if wd in self.producer_wds:
                wd_dict[wd].append('producer')
        return wd_dict

    def _load_synonym_map(self):
        """从同义词文件加载映射：同义词 -> 标准词"""
        syn_map = {}
        if not os.path.exists(self.synonym_path):
            return syn_map
        try:
            with open(self.synonym_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split('=') if p.strip()]
                    if not parts:
                        continue
                    standard = parts[0]
                    for alias in parts:
                        # 将每个别名映射到标准词（包括标准词自身）
                        syn_map[alias] = standard
        except Exception:
            return {}
        return syn_map

    def expand_synonyms(self, text: str) -> str:
        """
        将输入文本中的同义词替换为标准词并返回。
        """
        if not text:
            return text
        if not getattr(self, 'synonym_map', None):
            return text
        result = text
        for syn in self._synonym_keys_sorted:
            if syn in result:
                std = self.synonym_map.get(syn, syn)
                result = result.replace(syn, std)
        return result

    '''构造actree，加速过滤'''
    def build_actree(self, wordlist):
        actree = ahocorasick.Automaton()
        for index, word in enumerate(wordlist):
            actree.add_word(word, (index, word))
        actree.make_automaton()
        return actree

    '''问句过滤'''
    def check_medical(self, question):
        region_wds = []
        for i in self.region_tree.iter(question):
            wd = i[1][1]
            region_wds.append(wd)
    # 保留所有类型，不去重
        final_dict = {}
        for wd in region_wds:
            types = self.wdtype_dict.get(wd)
            if types:
                final_dict[wd] = types
        return final_dict

    '''基于特征词进行分类'''
    def check_words(self, wds, sent):
        for wd in wds:
            if wd in sent:
                return True
        return False


if __name__ == '__main__':
    handler = QuestionClassifier()