"""
知识图谱可视化

根据疾病名称生成知识图谱子图

"""

from streamlit_echarts import st_echarts
from py2neo import Graph
from utils.logger import get_logger

logger = get_logger(__name__)

class KnowledgeGraphVisualizer:
    """
    从Neo4j知识图谱中提取疾病相关的子图并展示
    """
    
    def __init__(self):
        try:
            self.g = Graph("bolt://localhost:7687", auth=("neo4j", "2512macf"))
        except Exception:
            self.g = None
    
    def get_disease_subgraph(self, disease_name):
        """
        获取指定疾病的知识图谱子图
        retuen:
        nodes: 节点列表（包含位置信息）
        links: 边列表
        categories: 节点类别列表
        error: 错误信息（如果有）
        """
        if not self.g:
            return None, None, None, "数据库未连接"
        
        nodes = []
        links = []
        categories = [
            {"name": "疾病", "itemStyle": {"color": "#E74C3C"}},  # 红色 - 中心
            {"name": "症状", "itemStyle": {"color": "#3498DB"}},  # 蓝色 - 左上
            {"name": "药品", "itemStyle": {"color": "#2ECC71"}},  # 绿色 - 右上
            {"name": "食物", "itemStyle": {"color": "#F39C12"}},  # 橙色 - 左下
            {"name": "检查", "itemStyle": {"color": "#9B59B6"}},  # 紫色 - 右下
            {"name": "科室", "itemStyle": {"color": "#1ABC9C"}},  # 青色 - 顶部
        ]
        
        try:
            # 先尝试精确匹配
            res = self.g.run("MATCH (d:Disease) WHERE d.name = $name RETURN d.name as name", name=disease_name).data()
            actual_disease_name = disease_name
            
            # 如果精确匹配失败，尝试模糊匹配
            if not res:
                res = self.g.run("MATCH (d:Disease) WHERE d.name CONTAINS $name RETURN d.name as name LIMIT 1", name=disease_name).data()
                if res:
                    actual_disease_name = res[0]['name']
            
            # 如果还是找不到，尝试反向匹配，疾病名称包含输入的关键词
            if not res:
                res = self.g.run("MATCH (d:Disease) WHERE $name CONTAINS d.name RETURN d.name as name ORDER BY length(d.name) DESC LIMIT 1", name=disease_name).data()
                if res:
                    actual_disease_name = res[0]['name']
            
            if not res:
                return None, None, None, f"未找到「{disease_name}」，请检查疾病名称是否正确"
            
            # 使用实际匹配到的疾病名称
            disease_name = actual_disease_name
        except Exception as e:
            return None, None, None, str(e)
        
        # 2查询关联节点，按类别分组
        queries = [
            ("MATCH (d:Disease)-[:has_symptom]->(n:Symptom) WHERE d.name = $name RETURN n.name LIMIT 10", 1, "症状"),
            ("MATCH (d:Disease)-[:common_drug]->(n:Drug) WHERE d.name = $name RETURN n.name LIMIT 6", 2, "药品"),
            ("MATCH (d:Disease)-[:recommand_drug]->(n:Drug) WHERE d.name = $name RETURN n.name LIMIT 6", 2, "药品"),
            ("MATCH (d:Disease)-[:do_eat]->(n:Food) WHERE d.name = $name RETURN n.name LIMIT 6", 3, "食物"),
            ("MATCH (d:Disease)-[:need_check]->(n:Check) WHERE d.name = $name RETURN n.name LIMIT 6", 4, "检查"),
            ("MATCH (d:Disease)-[:belongs_to]->(n:Department) WHERE d.name = $name RETURN n.name LIMIT 3", 5, "科室"),
        ]
        
        added_names = {disease_name}
        category_nodes = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        for query, category, rel_type in queries:
            try:
                data = self.g.run(query, name=disease_name).data()
                for item in data:
                    name = item.get('n.name')
                    if name and name not in added_names:
                        category_nodes[category].append(name)
                        added_names.add(name)
            except:
                continue
        
        # 按类别放置在不同区域
        center_x, center_y = 0, 0
        nodes.append({"name": disease_name, "symbolSize": 65, "category": 0, "x": center_x, "y": center_y})
        
        # 分区位置定义（左上、右上、左下、右下、顶部）
        # category 1: 症状 - 左侧
        # category 2: 药品 - 右侧
        # category 3: 食物 - 左下
        # category 4: 检查 - 右下
        # category 5: 科室 - 顶部
        
        region_config = {
            1: {'base_x': -200, 'base_y': 0, 'spread_x': 0, 'spread_y': 40, 'label': 'left'},      # 症状 - 左侧竖排
            2: {'base_x': 200, 'base_y': 0, 'spread_x': 0, 'spread_y': 40, 'label': 'right'},      # 药品 - 右侧竖排
            3: {'base_x': -150, 'base_y': 180, 'spread_x': 50, 'spread_y': 0, 'label': 'bottom'},  # 食物 - 左下横排
            4: {'base_x': 150, 'base_y': 180, 'spread_x': 50, 'spread_y': 0, 'label': 'bottom'},   # 检查 - 右下横排
            5: {'base_x': 0, 'base_y': -150, 'spread_x': 80, 'spread_y': 0, 'label': 'top'},       # 科室 - 顶部横排
        }
        
        for category in [1, 2, 3, 4, 5]:
            category_list = category_nodes[category]
            if not category_list:
                continue
            
            config = region_config[category]
            n = len(category_list)
            
            for i, name in enumerate(category_list):
                if config['spread_y'] != 0:  
                    offset = (i - (n - 1) / 2) * config['spread_y']
                    x = config['base_x']
                    y = config['base_y'] + offset
                else:  
                    offset = (i - (n - 1) / 2) * config['spread_x']
                    x = config['base_x'] + offset
                    y = config['base_y']
                
                nodes.append({
                    "name": name,
                    "symbolSize": 35,
                    "category": category,
                    "x": x,
                    "y": y,
                    "label": {"position": config['label']}
                })
                links.append({"source": disease_name, "target": name})
                
        return nodes, links, categories, None

    def render_graph(self, nodes, links, categories, dark_mode=False):
        """
        使用ECharts渲染知识图谱
        """
        if not nodes:
            return
        
        # 深色模式的css
        if dark_mode:
            label_color = "#FFFFFF"  # 白色文字
            legend_text_color = "#E0E0E0"  # 浅灰色图例
            tooltip_bg = "rgba(30,30,30,0.95)"
            tooltip_border = "#555"
        else:
            label_color = "#333"  # 深灰色文字
            legend_text_color = "#555"  # 灰色图例
            tooltip_bg = "rgba(50,50,50,0.95)"
            tooltip_border = "#333"
        
        option = {
            "tooltip": {
                "formatter": "{b}",
                "backgroundColor": tooltip_bg,
                "borderColor": tooltip_border,
                "textStyle": {"color": "#fff", "fontSize": 13},
                "padding": [8, 12]
            },
            "legend": {
                "data": [c["name"] for c in categories],
                "bottom": 5,
                "textStyle": {"color": legend_text_color, "fontSize": 12},
                "itemGap": 20,
                "itemWidth": 14,
                "itemHeight": 14
            },
            "series": [{
                "type": "graph",
                "layout": "none",
                "data": nodes,
                "links": links,
                "categories": categories,
                "roam": True,
                "zoom": 0.9,
                "focusNodeAdjacency": True,
                "label": {
                    "show": True,
                    "color": label_color,
                    "fontSize": 11,
                    "fontWeight": 500
                },
                "lineStyle": {
                    "color": "#BDC3C7",
                    "width": 2,
                    "curveness": 0.1,
                    "opacity": 0.8
                },
                "emphasis": {
                    "focus": "adjacency",
                    "label": {"fontSize": 13, "fontWeight": "bold", "color": label_color},
                    "lineStyle": {"width": 3, "color": "#5B7AA6"}
                }
            }]
        }
        st_echarts(options=option, height="550px", key=f"graph_{hash(str(nodes))}")

