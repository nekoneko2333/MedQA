# MedQA 智能医疗问答系统

MedQA 是一个基于 Neo4j 的智能医疗问答系统，支持以下功能：

- **知识图谱问答**：基于 Neo4j 的医疗知识图谱，支持自然语言问题的解析与回答。
- **症状诊断**：通过症状组合匹配，提供可能的疾病诊断建议。
- **数据可视化**：展示知识图谱的结构与数据分析结果。
- **LLM 增强**：可选集成大语言模型（如 Deepseek）以增强问答能力。

系统界面示例：
![](/images/加载界面.png)
![](/images/QA问题2.png)
![](/images/LLM问题1.png)
![](/images/数据分析1.png)
![](/images/知识图谱可视化.png)

## 快速开始

### 环境准备

1. 安装 Python 3.9 或更高版本。
2. 安装 Neo4j 数据库，并确保服务运行。
3. 修改代码中的 Neo4j 用户名和密码：

   打开 `nlp/answer_search.py` 文件，找到以下代码片段：

   ```python
   neo_url = getenv('NEO4J_BOLT_URL', 'bolt://localhost:7687')
   neo_user = getenv('NEO4J_USER', 'neo4j')
   neo_pass = getenv('NEO4J_PASSWORD', '你的密码')
   ```

   将 `你的密码` 替换为您设置的 Neo4j 密码。

### 安装依赖

```bash
pip install -r requirements.txt
```

### 构建知识图谱

运行以下脚本以构建知识图谱：

```bash
python data_build/build_medicalgraph.py
```

### 启动应用

使用 Streamlit 启动 Web 应用：

```bash
streamlit run app.py
```

默认情况下，应用将在浏览器中打开，地址为 `http://localhost:8501`。

## 项目结构

以下是项目的详细目录结构及功能说明：

- `app.py`：
  - 应用的主入口，基于 Streamlit。
- `data_build/`：
  - `build_medicalgraph.py`：构建医疗知识图谱的脚本。
- `views/`：
  - `analysis_page.py`：数据分析页面。
  - `chat_page.py`：聊天页面。
  - `diagnosis_page.py`：诊断页面。
  - `favorites_page.py`：收藏页面。
  - `graph_page.py`：知识图谱页面。
  - `llm_chat_page.py`：大语言模型聊天页面。
  - `sidebar.py`：侧边栏组件。
- `core/`：
  - `analyzer.py`：数据分析模块。
  - `chatbot.py`：问答机器人模块。
  - `diagnoser.py`：症状诊断模块。
  - `visualizer.py`：数据可视化模块。
- `nlp/`：
  - `answer_search.py`：答案搜索模块。
  - `question_classifier.py`：问题分类模块。
  - `question_parser.py`：问题解析模块。
  - `question_rewriter.py`：问题重写模块。
- `advanced/`：
  - `knowledge_reasoner.py`：知识推理模块。
  - `llm_chatbot.py`：大语言模型聊天模块。
  - `llm_client.py`：大语言模型客户端。
  - `rag_retriever.py`：RAG 检索模块。
- `utils/`：
  - `app_init.py`：应用初始化工具。
  - `context.py`：上下文管理模块。
  - `llm_context.py`：大语言模型上下文管理。
  - `logger.py`：日志管理模块。
- `data/`：
  - 存储医疗数据的目录，包括 JSON 文件。
- `dict/`：
  - 存储同义词、疾病、药物等词典数据。
- `logs/`：
  - 存储日志文件的目录。

## 运行要求

- Neo4j 数据库：确保 Neo4j 服务已启动，并导入了医疗知识数据。
- Python 环境：建议使用虚拟环境管理依赖。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目！