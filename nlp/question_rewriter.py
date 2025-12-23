"""
问句改写与模板扩展
1. 口语化表达转标准问法
2. 支持更多问法变体
3. 能把包含推理的复合问题分解

"""
import re
from typing import List, Dict, Tuple, Optional


class QuestionRewriter:
    def __init__(self):
        # 口语化表达 -> 标准表达的映射规则
        self.rewrite_rules = [
            # 药品相关
            (r'吃啥药', '用什么药'),
            (r'吃什么药', '用什么药'),
            (r'该吃啥', '应该吃什么'),
            (r'能吃啥', '可以吃什么'),
            (r'要吃啥', '应该吃什么'),
            (r'咋治', '怎么治疗'),
            (r'咋办', '怎么办'),
            (r'咋整', '怎么治疗'),
            (r'咋弄', '怎么治疗'),
            
            # 症状相关
            (r'啥症状', '什么症状'),
            (r'有啥表现', '有什么症状'),
            (r'啥表现', '什么症状'),
            (r'会咋样', '会怎么样'),
            (r'会咋', '会怎么样'),
            
            # 原因相关
            (r'咋回事', '是什么原因'),
            (r'咋得的', '是什么原因导致的'),
            (r'咋引起的', '是什么原因引起的'),
            (r'为啥会', '为什么会'),
            (r'咋会', '怎么会'),
            
            # 饮食相关
            (r'能吃不', '能吃吗'),
            (r'能不能吃', '可以吃吗'),
            (r'吃了会咋样', '吃了会怎么样'),
            (r'忌口啥', '忌口什么'),
            (r'不能吃啥', '不能吃什么'),
            (r'注意啥', '注意什么'),
            
            # 检查相关
            (r'查啥', '检查什么'),
            (r'做啥检查', '做什么检查'),
            (r'要查啥', '需要检查什么'),
            
            # 科室相关
            (r'挂啥科', '挂什么科'),
            (r'看啥科', '看什么科'),
            (r'去哪个科', '挂什么科'),
            (r'该找哪个科', '挂什么科'),
            
            # 通用
            (r'是啥', '是什么'),
            (r'有啥', '有什么'),
            (r'咋样', '怎么样'),
            (r'多久能好', '治疗周期多长'),
            (r'能治好吗', '能治愈吗'),
            (r'能根治吗', '能治愈吗'),
            (r'严重吗', '严重程度如何'),
            (r'要紧吗', '严重吗'),
            (r'啥毛病', '什么病'),
            (r'啥病', '什么病'),
        ]
        
        # 身体部位词典
        self.body_parts = ['头', '胸', '胃', '肚子', '腹', '腰', '背', '腿', '脚', '手', '眼', '耳', '鼻', '嗓子', '喉咙', '脖子', '肩', '膝盖', '关节', '心', '肺', '肝', '肾']
        
        # 症状动词
        self.symptom_verbs = {
            '疼': '痛', '痛': '痛', '酸': '酸痛', '胀': '胀痛', '闷': '闷',
            '晕': '晕', '麻': '麻木', '痒': '瘙痒', '肿': '肿胀',
        }
        
        # 口语症状表达 -> 标准症状词
        self.symptom_normalize_rules = [
            # 直接表达：我/我的 + 部位 + 修饰词 + 症状动词
            (r'我(的)?(.{1,3}?)(老是|总是|经常|一直|有点|有些|好|很|特别|非常)([疼痛晕麻痒酸胀闷])', self._normalize_symptom_with_context),
            # 通用模式：感觉/觉得 + 部位 + 修饰词 + 症状动词
            (r'感觉(.{1,3}?)(老是|总是|经常|一直|有点|有些|好|很|特别|非常)?([疼痛晕麻痒酸胀闷])', self._normalize_symptom),
            (r'觉得(.{1,3}?)(老是|总是|经常|一直|有点|有些|好|很|特别|非常)?([疼痛晕麻痒酸胀闷])', self._normalize_symptom),
            (r'(.{1,3}?)(老是|总是|经常|一直|有点|有些|好|很|特别|非常)([疼痛晕麻痒酸胀闷])', self._normalize_symptom),
            # 简单表达：部位 + 修饰词 + 症状动词
            (r'^(.{1,3}?)(好|很|特别|非常|有点|有些)([疼痛晕麻痒酸胀闷])', self._normalize_symptom),
            
            # 不舒服模式
            (r'(.{1,3}?)不太?舒服', self._normalize_discomfort),
            (r'(.{1,3}?)难受', self._normalize_discomfort),
            
            # 特定症状
            (r'浑身没劲|全身没劲|没有力气|没力气|乏力', '乏力'),
            (r'感觉很累|特别累|很疲惫|疲劳', '疲劳'),
            (r'老是犯困|总犯困|嗜睡', '嗜睡'),
            (r'睡不着觉?|晚上睡不好|睡眠不好|失眠', '失眠'),
            (r'喘不上气|呼吸不畅|喘不过气|呼吸困难', '呼吸困难'),
            (r'老是咳嗽|一直咳|咳个不停|咳嗽', '咳嗽'),
            (r'心跳很快|心跳加速|心慌|心悸', '心悸'),
            (r'血压有点高|血压偏高|血压高', '高血压'),
            (r'血糖有点高|血糖偏高|血糖高', '糖尿病'),
            (r'拉肚子|拉稀|腹泻', '腹泻'),
            (r'恶心想吐|想吐|恶心', '恶心'),
            (r'吃不下饭|没食欲|不想吃东西|食欲不振', '食欲不振'),
            (r'看不清东西|看不清|视力模糊|眼睛花|视力下降', '视力下降'),
            (r'听不清|耳鸣|听力下降', '听力下降'),
            (r'嗓子疼|喉咙疼|咽喉疼|咽喉痛', '咽喉痛'),
            (r'流鼻涕|鼻塞', '鼻塞'),
            (r'我发烧了|我发热了|我发烧|我发热|发烧了|发热了|发烧|发热|体温高', '发热'),
            (r'头痛|头疼|我头痛|我头疼', '头痛'),
            (r'头晕|我头晕|头好晕|头很晕', '头晕'),
            (r'胸闷|我胸闷|胸好闷|胸很闷|我胸好闷', '胸闷'),
            (r'胸痛|我胸痛|胸好痛|胸很痛|我胸好痛', '胸痛'),
            (r'腹痛|我腹痛|腹好痛|腹很痛|我腹好痛|肚子痛|我肚子痛', '腹痛'),
            (r'腰痛|我腰痛|腰好痛|腰很痛|我腰好痛', '腰痛'),
            (r'背痛|我背痛|背好痛|背很痛|我背好痛', '背痛'),
            (r'关节痛|我关节痛|关节好痛', '关节痛'),
            (r'胃痛|我胃痛|胃好痛|胃很痛|我胃好痛', '胃痛'),
            (r'恶心呕吐|想吐|呕吐', '恶心'),
            (r'发热|发烧|体温升高|体温高', '发热'),
            (r'乏力|没力气|浑身无力', '乏力'),
            (r'失眠|睡不着|睡眠不好', '失眠'),
            (r'食欲不振|不想吃|没胃口', '食欲不振'),
        ]
        
        # 编译正则表达式
        self.compiled_rules = [(re.compile(pattern), replacement) 
                               for pattern, replacement in self.rewrite_rules]
        
        # 编译症状规则
        self.compiled_symptom_rules = []
        for pattern, replacement in self.symptom_normalize_rules:
            self.compiled_symptom_rules.append((re.compile(pattern), replacement))
    
    def _normalize_symptom(self, match) -> str:
        """将口语症状转为标准症状词"""
        groups = match.groups()
        if len(groups) >= 3:
            part = groups[0]  
            symptom_verb = groups[2]  
        elif len(groups) >= 1:
            part = groups[0]
            symptom_verb = groups[-1] if len(groups) > 1 else '痛'
        else:
            return match.group(0)
        
        # 部位标准化
        part_map = {
            '脑袋': '头', '脑壳': '头', '头脑': '头',
            '肚子': '腹', '小肚子': '腹', 
            '嗓子': '咽喉', '喉咙': '咽喉',
            '后背': '背', '后腰': '腰',
            '胳膊': '手臂', '大腿': '腿', '小腿': '腿',
        }
        part = part_map.get(part, part)
        
        # 症状动词标准化
        verb_map = {
            '疼': '痛', '痛': '痛', '酸': '酸痛', '胀': '胀痛', 
            '闷': '闷',  
            '晕': '晕',  
            '麻': '麻木', '痒': '瘙痒', '肿': '肿胀',
        }
        symptom = verb_map.get(symptom_verb, symptom_verb)
        
        # 组合成标准症状，只返回症状词，不包含"我"等主语
        return f"{part}{symptom}"
    
    def _normalize_symptom_with_context(self, match) -> str:
        groups = match.groups()
        # 格式：我(的)? + 部位 + 修饰词 + 症状动词
        # groups[0] = "的"或None, groups[1] = 部位, groups[2] = 修饰词, groups[3] = 症状动词
        if len(groups) >= 4:
            part = groups[1]  # 身体部位
            symptom_verb = groups[3]  # 症状动词
        elif len(groups) >= 2:
            part = groups[1] if groups[1] else groups[0]
            symptom_verb = groups[-1] if len(groups) > 2 else '痛'
        else:
            return self._normalize_symptom(match)
        
        # 部位标准化
        part_map = {
            '脑袋': '头', '脑壳': '头', '头脑': '头',
            '肚子': '腹', '小肚子': '腹', 
            '嗓子': '咽喉', '喉咙': '咽喉',
            '后背': '背', '后腰': '腰',
            '胳膊': '手臂', '大腿': '腿', '小腿': '腿',
        }
        part = part_map.get(part, part)
        
        # 症状动词标准化
        verb_map = {
            '疼': '痛', '痛': '痛', '酸': '酸痛', '胀': '胀痛', 
            '闷': '闷',  
            '晕': '晕',  
            '麻': '麻木', '痒': '瘙痒', '肿': '肿胀',
        }
        symptom = verb_map.get(symptom_verb, symptom_verb)
        
        # 返回标准症状词
        return f"{part}{symptom}"
    
    def _normalize_discomfort(self, match) -> str:
        """将'XX不舒服'转为标准症状"""
        part = match.group(1)
        part_to_symptom = {
            '头': '头痛', '胸': '胸痛', '胃': '胃痛', '肚子': '腹痛',
            '腰': '腰痛', '背': '背痛', '腿': '腿痛', '嗓子': '咽喉痛',
            '眼': '眼痛', '心': '心悸', '肺': '呼吸困难',
        }
        return part_to_symptom.get(part, f"{part}痛")
        
        # 编译正则表达式
        self.compiled_rules = [(re.compile(pattern), replacement) 
                               for pattern, replacement in self.rewrite_rules]
    
    def rewrite(self, question: str) -> Tuple[str, List[str]]:
        """
        改写问句
        返回: (改写后的问句, 应用的规则列表)
        """
        rewritten = question
        applied_rules = []
        
        # 预处理：移除语气词（啊、呢、吧等），保留"了"
        rewritten = re.sub(r'[啊呢吧呀啦哦]$', '', rewritten)
        
        # 先做症状归一化
        for pattern, replacement in self.compiled_symptom_rules:
            match = pattern.search(rewritten)
            if match:
                if callable(replacement):
                    new_text = replacement(match)
                    rewritten = pattern.sub(new_text, rewritten, count=1)
                    applied_rules.append(f"症状识别: {new_text}")
                else:
                    rewritten = pattern.sub(replacement, rewritten)
                    applied_rules.append(f"症状识别: {replacement}")
        
        # 再做问句改写
        for pattern, replacement in self.compiled_rules:
            if pattern.search(rewritten):
                rewritten = pattern.sub(replacement, rewritten)
                applied_rules.append(f"{pattern.pattern} → {replacement}")
        
        return rewritten, applied_rules


class TemplateExpander:
    def __init__(self):
        # 扩展的意图识别模板
        self.templates = {
            'symptom_query': [
                r'^(.+?)有什么症状',
                r'^(.+?)的症状是什么',
                r'^(.+?)会有哪些表现',
                r'^(.+?)的临床表现',
                r'^得了(.+?)会怎样',
                r'^患(.+?)有什么感觉',
            ],
            
            'symptom_to_disease': [
                r'^(.+?)是什么病',
                r'^(.+?)可能是什么病',
                r'^(.+?)是怎么回事',
                r'^为什么会(.+)',
                r'^经常(.+?)是什么原因',
                r'^总是(.+?)怎么回事',
                r'^老是(.+?)是什么病',
            ],
            
            'drug_query': [
                r'^(.+?)用什么药$',
                r'^(.+?)吃什么药好',
                r'^(.+?)该吃什么药',
                r'^治疗(.+?)的药',
                r'^(.+?)吃什么药能好',
            ],
            
            'food_query': [
                r'^(.+?)能吃什么$',
                r'^(.+?)吃什么好$',
                r'^(.+?)应该吃什么',
                r'^(.+?)饮食注意什么',
            ],
            
            'food_forbidden': [
                r'^(.+?)不能吃什么',
                r'^(.+?)忌口什么',
                r'^(.+?)忌什么',
                r'^(.+?)有什么忌口',
            ],
            
            'check_query': [
                r'^(.+?)做什么检查$',
                r'^(.+?)需要检查什么',
                r'^(.+?)要做哪些检查',
                r'^怎么检查(.+)',
            ],
            
            'cause_query': [
                r'^(.+?)是什么原因$',
                r'^(.+?)是怎么引起的',
                r'^为什么会得(.+)',
                r'^(.+?)的病因',
            ],
            
            'cure_query': [
                r'^(.+?)怎么治疗$',
                r'^(.+?)如何治疗',
                r'^怎么治(.+)',
                r'^(.+?)能治好吗',
            ],
            
            'prevent_query': [
                r'^怎么预防(.+)',
                r'^如何预防(.+)',
                r'^(.+?)怎么预防',
            ],
            
            'department_query': [
                r'^(.+?)挂什么科$',
                r'^(.+?)看什么科',
                r'^(.+?)属于什么科',
            ],
        }
        
        # 编译模板
        self.compiled_templates = {}
        for intent, patterns in self.templates.items():
            self.compiled_templates[intent] = [re.compile(p) for p in patterns]
    
    def match_template(self, question: str) -> List[Dict]:
        """匹配问句模板"""
        matches = []
        
        for intent, patterns in self.compiled_templates.items():
            for pattern in patterns:
                match = pattern.search(question)
                if match:
                    entity = match.group(1).strip() if match.groups() else None
                    if entity:
                        matches.append({
                            'intent': intent,
                            'entity': entity,
                            'pattern': pattern.pattern,
                            'confidence': 0.9
                        })
        
        return matches


class EnhancedQuestionProcessor:
    def __init__(self):
        self.rewriter = QuestionRewriter()
        self.template_expander = TemplateExpander()
    
    def process(self, question: str) -> Dict:
        """处理问句，返回分析结果"""
        result = {
            'original': question,
            'rewritten': question,
            'rewrite_rules': [],
            'template_matches': [],
            'enhanced': False
        }
        
        # 问句改写
        rewritten, rules = self.rewriter.rewrite(question)
        result['rewritten'] = rewritten
        result['rewrite_rules'] = rules
        
        # 模板匹配
        template_matches = self.template_expander.match_template(rewritten)
        result['template_matches'] = template_matches
        
        result['enhanced'] = bool(rules or template_matches)
        
        return result


if __name__ == '__main__':
    processor = EnhancedQuestionProcessor()

