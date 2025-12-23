"""
接入LLM的医疗问答机器人

- 基于RAG的检索
- 使用Deepseek API

"""

from typing import List, Dict, Optional
from utils.logger import get_logger
from advanced.llm_client import DeepseekClient
from advanced.rag_retriever import RAGRetriever
from advanced.knowledge_reasoner import KnowledgeReasoner
from nlp.question_classifier import QuestionClassifier
from py2neo import Graph

logger = get_logger(__name__)


class LLMChatBot:
    
    def __init__(self, api_key: Optional[str] = None, graph: Optional[Graph] = None):
        """

        初始化LLM聊天
        api_key: Deepseek API密钥
        graph: Neo4j图数据库

        """
        self.llm_client = DeepseekClient(api_key=api_key)
        self.rag_retriever = RAGRetriever(graph=graph)
        self.classifier = QuestionClassifier()  # 用于实体提取
        self.reasoner = KnowledgeReasoner()
        # 系统提示词
        self.system_prompt = """你是一位专业的医疗助手，基于提供的医疗知识图谱信息回答用户问题。
要求：
1. 基于提供的知识图谱信息回答问题，不要编造信息
2. 如果知识图谱中没有相关信息，明确告知用户
3. 回答要专业、准确、易懂
4. 对于医疗建议，要提醒用户咨询专业医生
5. 使用中文回答

知识图谱信息会以以下格式提供：
[知识图谱信息]
...
[/知识图谱信息]
"""
    
    def chat(self, question: str, context: Optional[Dict] = None, 
             conversation_history: Optional[List[Dict]] = None) -> tuple:
        """
        处理用户问题并生成回答
        
        Args:
            question: 用户问题
            context: 上下文信息
            conversation_history: 对话历史列表
        
        Returns:
            (answer_html, metadata, process_info) 元组
        """
        process_info = {
            'method': 'llm_rag',
            'retrieved_info': None,
            'llm_used': False,
            'error': None
        }
        
        # 解析上下文，处理追问和代词
        resolved_question = self._resolve_context(question, context)
        if resolved_question != question:
            process_info['context_resolved'] = {
                'original': question,
                'resolved': resolved_question
            }
            question = resolved_question  # 使用解析后的问题
        
        # 在RAG检索之前先检测多跳推理
        reasoning_result = None
        if self.reasoner:
            try:
                reasoning_result = self.reasoner.execute_reasoning(question)
                if reasoning_result and reasoning_result.get('success'):
                    # 多跳推理成功，使用推理结果
                    process_info['method'] = 'reasoning_llm'
                    process_info['reasoning'] = {
                        'type': reasoning_result['hop_info']['type'],
                        'description': reasoning_result['hop_info']['description'],
                        'path': reasoning_result['reasoning_path']
                    }
                    # 将推理结果作为检索信息
                    retrieved_info = reasoning_result['answer']
                    process_info['retrieved_info'] = retrieved_info
                    process_info['reasoning_used'] = True
                    
                    # 提取实体
                    classify_result = self.classifier.classify(question)
                    entities = classify_result.get('args', {}) if classify_result else {}
                    
                    # 构建消息并调用LLM
                    messages = self._build_messages(question, retrieved_info, conversation_history, is_reasoning=True)
                    
                    if not self.llm_client.is_available():
                        # LLM不可用，直接返回推理结果
                        answer_html = self._format_reasoning_answer(reasoning_result['answer'], reasoning_result)
                        return answer_html, classify_result, process_info
                    
                    llm_response = self.llm_client.chat(
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    if 'error' in llm_response:
                        # LLM调用失败，使用推理结果作为fallback
                        error_msg = llm_response.get('error', '未知错误')
                        process_info['error'] = error_msg
                        logger.warning(f"LLM调用失败，使用推理结果: {error_msg}")
                        answer_html = self._format_reasoning_answer(reasoning_result['answer'], reasoning_result)
                        error_hint = f"<div style='color: orange; margin-bottom: 10px;'>⚠️ LLM服务暂时不可用，以下是基于知识推理的结果：</div>"
                        return error_hint + answer_html, classify_result, process_info
                    
                    process_info['llm_used'] = True
                    answer = llm_response.get('answer', '')
                    answer_html = self._format_answer(answer)
                    
                    # 添加推理路径提示
                    reasoning_hint = self._format_reasoning_hint(reasoning_result)
                    answer_html = reasoning_hint + answer_html
                    
                    return answer_html, classify_result, process_info
            except Exception as e:
                logger.warning(f"知识推理检测失败: {e}")
                # 继续使用RAG检索
        
        # 如果不是多跳推理，使用RAG检索
        # 提取实体
        classify_result = self.classifier.classify(question)
        entities = classify_result.get('args', {}) if classify_result else {}
        
        # RAG检索
        retrieved_info = self.rag_retriever.retrieve(question, entities=entities)
        process_info['retrieved_info'] = retrieved_info
        
        # 构建消息列表
        messages = self._build_messages(question, retrieved_info, conversation_history)
        
        # 调用LLM
        if not self.llm_client.is_available():
            return self._fallback_answer(question, retrieved_info, entities), classify_result, process_info
        
        llm_response = self.llm_client.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        if 'error' in llm_response:
            # LLM调用失败，使用fallback，但显示错误信息
            error_msg = llm_response.get('error', '未知错误')
            error_detail = llm_response.get('error_detail', '')
            process_info['error'] = error_msg
            process_info['error_detail'] = error_detail
            logger.error(f"LLM调用失败: {error_msg}")
            if error_detail:
                logger.debug(f"错误详情: {error_detail}")
            
            # 如果有检索信息，使用fallback；否则显示错误
            if retrieved_info:
                fallback_answer = self._fallback_answer(question, retrieved_info, entities)
                # 在fallback答案前添加错误提示
                error_hint = f"<div style='color: orange; margin-bottom: 10px;'>⚠️ LLM服务暂时不可用 ({error_msg})，以下是基于知识图谱的信息：</div>"
                return error_hint + fallback_answer, classify_result, process_info
            else:
                error_answer = f"<div>抱歉，暂时无法回答您的问题。<br><br>错误信息: {error_msg}<br>请检查API密钥是否正确，或尝试使用「智能问答」功能。</div>"
                if error_detail:
                    error_answer += f"<br><br><details><summary>详细错误信息</summary><pre>{error_detail[:500]}</pre></details>"
                return error_answer, classify_result, process_info
        
        process_info['llm_used'] = True
        answer = llm_response.get('answer', '')
        answer_html = self._format_answer(answer)
        
        return answer_html, classify_result, process_info
    
    def _build_messages(self, question: str, retrieved_info: str, 
                       conversation_history: Optional[List[Dict]] = None,
                       is_reasoning: bool = False) -> List[Dict[str, str]]:
        """构建LLM消息列表"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 添加对话历史，最近6条消息
        if conversation_history:
            for msg in conversation_history[-6:]: 
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')[:500]  
                })
        
        # 添加检索到的信息或推理结果
        if is_reasoning:
            # 多跳推理结果
            context_content = f"[知识推理结果]\n{retrieved_info}\n[/知识推理结果]\n\n"
            context_content += "注意：以上是通过多跳推理得到的结果，请基于这些信息回答用户问题。\n\n"
        else:
            # RAG检索结果
            if retrieved_info:
                context_content = f"[知识图谱信息]\n{retrieved_info}\n[/知识图谱信息]\n\n"
            else:
                context_content = "[知识图谱信息]\n未找到相关信息\n[/知识图谱信息]\n\n"
        
        # 添加当前问题
        user_message = context_content + f"用户问题: {question}"
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _format_answer(self, answer: str) -> str:
        """
        将Markdown格式转换为HTML，使其显示更美观
        """
        import markdown
        from markdown.extensions import fenced_code, tables, nl2br
        
        # 配置Markdown扩展
        md = markdown.Markdown(extensions=[
            'fenced_code',
            'tables',
            'nl2br',
            'extra'
        ])
        
        # 转换为HTML
        html = md.convert(answer)
        
        # 添加样式，使Markdown渲染更美观
        styled_html = f"""
        <div style="line-height: 1.6; color: var(--text-main, #333);">
            {html}
        </div>
        <style>
            div h1, div h2, div h3 {{
                margin-top: 1em;
                margin-bottom: 0.5em;
                font-weight: 600;
                color: var(--text-main, #2c3e50);
            }}
            div h1 {{ font-size: 1.5em; }}
            div h2 {{ font-size: 1.3em; }}
            div h3 {{ font-size: 1.1em; }}
            div p {{
                margin-bottom: 0.8em;
                line-height: 1.6;
            }}
            div ul, div ol {{
                margin-left: 1.5em;
                margin-bottom: 0.8em;
            }}
            div li {{
                margin-bottom: 0.4em;
            }}
            div strong {{
                font-weight: 600;
                color: var(--text-main, #2c3e50);
            }}
            div code {{
                background-color: rgba(0, 0, 0, 0.05);
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            div pre {{
                background-color: rgba(0, 0, 0, 0.05);
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                margin-bottom: 0.8em;
            }}
            div blockquote {{
                border-left: 3px solid var(--primary-color, #5B7AA6);
                padding-left: 1em;
                margin-left: 0;
                color: var(--text-secondary, #666);
                font-style: italic;
            }}
        </style>
        """
        return styled_html
    
    def _resolve_context(self, question: str, context: Optional[Dict] = None) -> str:
        """
        解析上下文，处理代词和追问,和chatbot类似
        """
        if not context:
            return question
        
        # 追问关键词
        followup_patterns = [
            ('它', '这个病', '这种病', '该病', '这个症状', '这个'),  
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
        
        # 替换代词
        if last_disease:
            for pronoun in ['它', '这个病', '这种病', '该病', '这病', '这个']:
                if pronoun in resolved:
                    resolved = resolved.replace(pronoun, last_disease)
                    return resolved
        elif last_symptom:
            for pronoun in ['它', '这个症状', '这个']:
                if pronoun in resolved:
                    resolved = resolved.replace(pronoun, last_symptom)
                    return resolved
        
        # 没有明确实体的问句，检查是否是追问
        has_entity = False
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
    
    def _fallback_answer(self, question: str, retrieved_info: str, entities: Dict) -> str:
        """LLM不可用时的fallback回答"""
        if retrieved_info:
            return f"<div>基于知识图谱信息：<br><br>{retrieved_info.replace(chr(10), '<br>')}</div>"
        else:
            return "<div>抱歉，暂时无法回答您的问题。请尝试使用「智能问答」功能。</div>"
    
    def _format_reasoning_answer(self, answer: str, reasoning_result: Dict) -> str:
        """格式化推理结果为HTML"""
        # 先格式化Markdown
        formatted = self._format_answer(answer)
        return formatted
    
    def _format_reasoning_hint(self, reasoning_result: Dict) -> str:
        """格式化推理路径提示"""
        hop_info = reasoning_result.get('hop_info', {})
        reasoning_path = reasoning_result.get('reasoning_path', [])
        
        # 构建推理链路展示
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
        
        # 组合最终输出
        header_html = f"""
        <div style="background:linear-gradient(135deg, #667eea11 0%, #764ba211 100%); 
                    border-left:4px solid #667eea; padding:12px; border-radius:8px; margin-bottom:15px;">
            <div style="font-size:0.9em; color:#667eea; margin-bottom:5px;">
                🔗 <strong>知识推理</strong> · {hop_info.get('description', '多跳查询')}
            </div>
            {chain_display}
        </div>
        """
        
        return header_html

