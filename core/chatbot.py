"""
医疗问答

- 基于知识图谱的医疗问答
- 支持多跳知识推理
- 支持多轮对话和上下文理解
- 问题改写和同义词扩展

"""

import re
from utils.logger import get_logger
from nlp.question_classifier import QuestionClassifier
from nlp.question_parser import QuestionPaser
from nlp.answer_search import AnswerSearcher
from nlp.question_rewriter import EnhancedQuestionProcessor
from advanced.knowledge_reasoner import KnowledgeReasoner
from ui.utils import format_long_text

logger = get_logger(__name__)


class MedicalChatBot:
    def __init__(self):
        """
        初始化聊天
        """
        try:
            self.classifier = QuestionClassifier()
            self.parser = QuestionPaser()
            self.searcher = AnswerSearcher()
            self.question_processor = EnhancedQuestionProcessor()
            self.reasoner = KnowledgeReasoner()
        except Exception as e:
            logger.warning(f"初始化警告: {e}")
            self.question_processor = None
    
    def chat(self, question, context=None):
        default_answer = "🤔 抱歉，我暂时无法理解您的问题。请尝试描述更具体的症状或疾病名称。"
        process_info = {'method': 'rule'}
        
        try:
            # 上下文理解
            resolved_question = self._resolve_context(question, context)
            if resolved_question != question:
                process_info['context_resolved'] = {
                    'original': question,
                    'resolved': resolved_question
                }
            
            # 句子预处理
            rewritten_question = resolved_question
            if self.question_processor:
                process_result = self.question_processor.process(resolved_question)
                rewritten_question = process_result['rewritten']
                process_info['rewrite'] = {
                    'original': resolved_question,
                    'rewritten': rewritten_question,
                    'rules': process_result['rewrite_rules']
                }
                if rewritten_question != resolved_question and process_result.get('rewrite_rules'):
                    process_info['show_rewrite_hint'] = True
            
            # 检测是否包含多跳推理
            if self.reasoner:
                try:
                    reasoning_result = self.reasoner.execute_reasoning(rewritten_question)
                except Exception as e:
                    logger.warning(f"reasoner.execute_reasoning 报错，降级为规则查询: {e}")
                    reasoning_result = None

                if reasoning_result and reasoning_result.get('success'):
                    process_info['method'] = 'reasoning'
                    hop_info = reasoning_result.get('hop_info') or {}
                    process_info['reasoning'] = {
                        'type': hop_info.get('type', reasoning_result.get('type', 'unknown')),
                        'description': hop_info.get('description', reasoning_result.get('description', '多跳查询')),
                        'path': reasoning_result.get('reasoning_path')
                    }
                    answer = reasoning_result['answer']
                    answer = self._format_reasoning_answer(answer, reasoning_result, process_info)
                    return answer, {'reasoning': True}, process_info
            
            # 开始处理问题
            res_classify = self.classifier.classify(rewritten_question)
            process_info['classify'] = res_classify

            # 情况 A：意图识别失败或没有识别到实体
            if not res_classify or not res_classify.get('args'):
                return "🤔 抱歉，我暂时无法理解您的问题，请描述具体的症状或实体。", None, process_info
            
            res_sql = self.parser.parser_main(res_classify)
            final_answers = self.searcher.search_main(res_sql)
            
            if not final_answers:
                # 情况 B：识别出意图但查询无数据
                entity_names = ','.join(res_classify.get('args', {}).keys()) if res_classify.get('args') else '未知实体'
                intent_types = ','.join(res_classify.get('question_types', [])) if res_classify.get('question_types') else '未知类型'
                return f"📚 抱歉，虽然识别到您在问 [{entity_names}]，但知识库中暂时没有 [{intent_types}] 的相关数据。", res_classify, process_info
            
            # 合并多个意图的答案，用分隔符分开，多个答案之间用双换行分隔
            if len(final_answers) > 1:
                answer = '\n\n'.join(final_answers)  
            else:
                answer = final_answers[0]
            
            formatted_answer = format_long_text(answer)
            formatted_answer = self._add_process_hint(
                formatted_answer, question, rewritten_question, 
                process_info
            )
            
            return formatted_answer, res_classify, process_info
            
        except Exception as e:
            logger.exception(f"chat 主流程异常: {e}")
            return f"系统繁忙或连接错误: {str(e)}", None, process_info
    
    def _resolve_context(self, question, context):
        """
        解析上下文，处理代词和追问
        """
        if not context:
            return question
        
        # 追问关键词，支持疾病和症状的追问
        followup_patterns = [
            ('它', '这个病', '这种病', '该病', '这个症状', '这个'),  # 指代疾病/症状
            ('怎么预防', '如何预防', '预防方法', '怎么预防'),
            ('怎么治疗', '如何治疗', '治疗方法', '怎么办', '咋办', '怎么治'),
            ('吃什么药', '用什么药', '有什么药', '该吃什么药', '能吃什么药'),
            ('吃什么好', '能吃什么', '饮食', '应该吃什么', '可以吃什么'),
            ('不能吃什么', '忌口', '禁忌', '不能吃', '忌什么'),
            ('有什么症状', '症状是什么', '什么表现', '有哪些症状'),
            ('挂什么科', '看什么科', '去什么科', '该挂什么科'),
            ('什么原因', '怎么引起', '为什么会', '是什么原因'),
            ('做什么检查', '需要检查什么', '要做什么检查', '检查什么'),
        ]
        
        last_disease = context.get('last_disease')
        last_symptom = context.get('last_symptom')
        
        resolved = question
        
        # 替换代词，优先使用疾病，其次使用症状
        if last_disease:
            if '这些并发症' in resolved:
                resolved = resolved.replace('这些并发症', f"{last_disease}的并发症")
            if '该并发症' in resolved:
                resolved = resolved.replace('该并发症', f"{last_disease}的并发症")
            # 通用的“这些”指代，替换为上文疾病
            if '这些' in resolved and '并发症' not in resolved:
                resolved = resolved.replace('这些', last_disease)

            for pronoun in ['它', '这个病', '这种病', '该病', '这病', '这个']:
                if pronoun in resolved:
                    resolved = resolved.replace(pronoun, last_disease)
                    return resolved
        elif last_symptom:
            for pronoun in ['它', '这个症状', '这个']:
                if pronoun in resolved:
                    resolved = resolved.replace(pronoun, last_symptom)
                    return resolved
        
        # 没有明确实体的问句检查是否追问
        has_entity = False
        if self.classifier:
            try:
                test_classify = self.classifier.classify(question)
                if test_classify and test_classify.get('args'):
                    has_entity = True
            except:
                pass
        
        # 如果没有实体，尝试补充上下文中的实体
        if not has_entity:
            # 检查是否是追问模式
            for patterns in followup_patterns:
                for pattern in patterns:
                    if pattern in question:
                        # 优先使用疾病
                        if last_disease:
                            # 在问句开头或合适位置补充疾病名
                            if question.startswith(pattern):
                                    resolved = f"{last_disease}{question}"
                            else:
                                    resolved = f"{last_disease}{question}"
                            return resolved
                        # 如果没有疾病，使用症状
                        elif last_symptom:
                            # 在问句开头或合适位置补充症状名
                            if question.startswith(pattern):
                                    resolved = f"{last_symptom}{question}"
                            else:
                                    resolved = f"{last_symptom}{question}"
                            return resolved
        
        return resolved
    
    def _add_process_hint(self, answer, question, rewritten, process_info):
        hints = []
        
        # 上下文解析提示
        if process_info.get('context_resolved'):
            orig = process_info['context_resolved']['original']
            resolved = process_info['context_resolved']['resolved']
            hints.append(f"🔗 已理解追问：「{orig}」→「{resolved}」")
        
        # 问句改写提示
        if process_info.get('rewrite') and process_info['rewrite']['rules']:
            orig = process_info['rewrite']['original']
            hints.append(f"💡 口语转换：「{orig}」→「{rewritten}」")
        
        if hints:
            hint_html = '<div style="color:#888; font-size:0.85em; margin-bottom:10px;">' + '<br>'.join(hints) + '</div>'
            return hint_html + answer
        return answer
    
    def _format_reasoning_answer(self, answer, reasoning_result, process_info):
        """格式化推理结果，展示推理过程"""
        hop_info = reasoning_result.get('hop_info', {})
        reasoning_path = reasoning_result.get('reasoning_path', [])

        chain_display = ""
        if reasoning_path:
            steps_html = []
            for step in reasoning_path:
                step_num = step.get('step', '?')
                action = step.get('action', '')
                relation = step.get('relation', '')
                result = step.get('result', [])
                
                if isinstance(result, list):
                    result_str = ', '.join(str(r)[:20] for r in result[:3])
                    if len(result) > 3:
                        result_str += '...'
                else:
                    result_str = str(result)[:50]
                
                steps_html.append(
                    f"<div style='padding:5px 10px; background:var(--card-bg, #F8F9FA); border-radius:4px; margin:3px 0;'>"
                    f"<span style='color:var(--primary-color, #5B7AA6); font-weight:bold;'>Step {step_num}</span>: {action}"
                    f"<span style='color:var(--text-secondary, #888); font-size:0.9em;'> ({relation})</span>"
                    f"</div>"
                )
            chain_display = ''.join(steps_html)
        
        header_html = f"""
        <div style="background:linear-gradient(135deg, #667eea11 0%, #764ba211 100%); 
                    border-left:4px solid #667eea; padding:12px; border-radius:8px; margin-bottom:15px;">
            <div style="font-size:0.9em; color:#667eea; margin-bottom:5px;">
                🔗 <strong>知识推理</strong> · {hop_info.get('description', '多跳查询')}
            </div>
            {chain_display}
        </div>
        """
        
        return header_html + answer

