from flask import Flask, jsonify, request, render_template, send_from_directory
import networkx as nx
import json
import os
from graph_builder import build_graph
from query_node_neighborhood import find_node_by_name

app = Flask(__name__, static_folder='static', template_folder='templates')

# 修改Jinja2模板分隔符，避免与Vue.js的{{ }}冲突
app.jinja_env.variable_start_string = '{['
app.jinja_env.variable_end_string = ']}'
app.jinja_env.block_start_string = '{%'
app.jinja_env.block_end_string = '%}'

# 确保输出目录存在
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/data', exist_ok=True)

# 全局图对象和指标缓存
G = None
node_metrics = {}

def calculate_node_metrics():
    """计算并缓存节点各项指标"""
    global G, node_metrics
    
    if G is None:
        return
    
    # 初始化指标字典
    node_metrics = {
        "pagerank": {},
        "degree_centrality": {},
        "betweenness_centrality": {},
        "in_degree": {},
        "out_degree": {}
    }
    
    # 计算PageRank
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
        node_metrics["pagerank"] = pagerank
    except Exception as e:
        print(f"计算PageRank时出错: {e}")
    
    # 计算度中心性
    try:
        degree_centrality = nx.degree_centrality(G)
        node_metrics["degree_centrality"] = degree_centrality
    except Exception as e:
        print(f"计算度中心性时出错: {e}")
    
    # 计算中介中心性（可能计算时间较长）
    try:
        betweenness_centrality = nx.betweenness_centrality(G, k=100)  # 使用采样以提高性能
        node_metrics["betweenness_centrality"] = betweenness_centrality
    except Exception as e:
        print(f"计算中介中心性时出错: {e}")
    
    # 计算入度和出度
    for node in G.nodes():
        node_metrics["in_degree"][node] = G.in_degree(node)
        node_metrics["out_degree"][node] = G.out_degree(node)

@app.route('/')
def index():
    """返回主页"""
    return render_template('index.html')

@app.route('/api/graph/stats')
def get_graph_stats():
    """获取图的基本统计信息"""
    global G, node_metrics
    if G is None:
        G = build_graph()
        calculate_node_metrics()
    
    # 计算基本统计数据
    stats = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
    }
    
    # 入度最高的前5个节点
    in_degrees = sorted(node_metrics["in_degree"].items(), key=lambda x: x[1], reverse=True)[:5]
    stats["top_in_degree"] = []
    for node, degree in in_degrees:
        node_name = G.nodes[node].get('name', str(node))
        stats["top_in_degree"].append({
            "id": node,
            "name": node_name, 
            "degree": degree
        })
    
    # 出度最高的前5个节点
    out_degrees = sorted(node_metrics["out_degree"].items(), key=lambda x: x[1], reverse=True)[:5]
    stats["top_out_degree"] = []
    for node, degree in out_degrees:
        node_name = G.nodes[node].get('name', str(node))
        stats["top_out_degree"].append({
            "id": node,
            "name": node_name, 
            "degree": degree
        })
    
    # 中心性分析
    try:
        # PageRank中心性
        top_pagerank = sorted(node_metrics["pagerank"].items(), key=lambda x: x[1], reverse=True)[:5]
        stats["top_pagerank"] = []
        for node, pr in top_pagerank:
            node_name = G.nodes[node].get('name', str(node))
            stats["top_pagerank"].append({
                "id": node,
                "name": node_name, 
                "score": pr
            })
        
        # 度中心性
        top_degree = sorted(node_metrics["degree_centrality"].items(), key=lambda x: x[1], reverse=True)[:5]
        stats["top_degree_centrality"] = []
        for node, centrality in top_degree:
            node_name = G.nodes[node].get('name', str(node))
            stats["top_degree_centrality"].append({
                "id": node,
                "name": node_name, 
                "score": centrality
            })
    except Exception as e:
        stats["centrality_error"] = str(e)
    
    # 计算环
    try:
        cycles = list(nx.simple_cycles(G))[:5]  # 最多返回5个环
        stats["cycles"] = []
        for cycle in cycles:
            cycle_info = []
            for node in cycle:
                node_name = G.nodes[node].get('name', str(node))
                cycle_info.append(node_name)
            stats["cycles"].append(cycle_info)
    except Exception as e:
        stats["cycles_error"] = str(e)
    
    return jsonify(stats)

@app.route('/api/search')
def search_nodes():
    """搜索节点"""
    global G
    if G is None:
        G = build_graph()
        calculate_node_metrics()
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "查询参数为空"}), 400
    
    # 查找精确匹配
    node_id = find_node_by_name(G, query)
    if node_id is not None:
        node_data = G.nodes[node_id]
        result = {
            "id": node_id,
            "name": node_data.get('name', str(node_id)),
            "type": node_data.get('type', ''),
            "level": node_data.get('level', '')
        }
        return jsonify(result)
    
    # 查找部分匹配
    partial_matches = []
    for node_id, data in G.nodes(data=True):
        if query.lower() in data.get('name', '').lower():
            partial_matches.append({
                "id": node_id,
                "name": data.get('name', str(node_id)),
                "type": data.get('type', ''),
                "level": data.get('level', '')
            })
    
    if partial_matches:
        return jsonify({"partial_matches": partial_matches})
    else:
        return jsonify({"error": "未找到匹配的节点"}), 404

@app.route('/api/node/<node_id>')
def get_node_info(node_id):
    """获取特定节点的详细信息及其邻居"""
    global G, node_metrics
    if G is None:
        G = build_graph()
        calculate_node_metrics()
    
    if node_id not in G.nodes:
        return jsonify({"error": "节点不存在"}), 404
    
    # 节点基本信息
    node_data = G.nodes[node_id]
    result = {
        "id": node_id,
        "name": node_data.get('name', str(node_id)),
        "type": node_data.get('type', ''),
        "level": node_data.get('level', ''),
        "short_name": node_data.get('short_name', ''),
        "investors": [],  # 投资方
        "investees": [],  # 被投资企业
        "metrics": {}     # 节点指标
    }
    
    # 添加节点指标
    for metric_name in node_metrics:
        if node_id in node_metrics[metric_name]:
            if "metrics" not in result:
                result["metrics"] = {}
            result["metrics"][metric_name] = node_metrics[metric_name][node_id]
    
    # 获取投资方（predecessors）
    for pred_id in G.predecessors(node_id):
        pred_data = G.nodes[pred_id]
        edge_data = G.get_edge_data(pred_id, node_id)
        percent = edge_data.get('percent', None) if edge_data else None
        percent_str = f"{percent*100:.2f}%" if percent is not None else "未知%"
        
        # 添加投资方的指标数据
        metrics = {}
        for metric_name in node_metrics:
            if pred_id in node_metrics[metric_name]:
                # 直接添加度量值到指标字典
                metrics[metric_name] = node_metrics[metric_name][pred_id]
        
        # 确保对象有pagerank字段，这是前端重点使用的
        if "pagerank" in node_metrics and pred_id in node_metrics["pagerank"]:
            pagerank = node_metrics["pagerank"][pred_id]
        else:
            pagerank = None
            
        result["investors"].append({
            "id": pred_id,
            "name": pred_data.get('name', str(pred_id)),
            "type": pred_data.get('type', ''),
            "percent": percent_str,
            "level": pred_data.get('level', ''),
            "short_name": pred_data.get('short_name', ''),
            "metrics": metrics,
            "pagerank": pagerank  # 直接在对象上添加PageRank值
        })
    
    # 获取被投资企业（successors）
    for succ_id in G.successors(node_id):
        succ_data = G.nodes[succ_id]
        edge_data = G.get_edge_data(node_id, succ_id)
        percent = edge_data.get('percent', None) if edge_data else None
        percent_str = f"{percent*100:.2f}%" if percent is not None else "未知%"
        
        # 添加被投资企业的指标数据
        metrics = {}
        for metric_name in node_metrics:
            if succ_id in node_metrics[metric_name]:
                metrics[metric_name] = node_metrics[metric_name][succ_id]
        
        # 确保对象有pagerank字段，这是前端重点使用的
        if "pagerank" in node_metrics and succ_id in node_metrics["pagerank"]:
            pagerank = node_metrics["pagerank"][succ_id]
        else:
            pagerank = None
            
        result["investees"].append({
            "id": succ_id,
            "name": succ_data.get('name', str(succ_id)),
            "type": succ_data.get('type', ''),
            "percent": percent_str,
            "level": succ_data.get('level', ''),
            "short_name": succ_data.get('short_name', ''),
            "metrics": metrics,
            "pagerank": pagerank  # 直接在对象上添加PageRank值
        })
    
    return jsonify(result)

@app.route('/api/equity_analysis/<node_id>')
def get_equity_analysis(node_id):
    """获取节点的股权穿透分析"""
    global G, node_metrics
    if G is None:
        G = build_graph()
        calculate_node_metrics()
    
    if node_id not in G.nodes:
        return jsonify({"error": "节点不存在"}), 404
    
    # 节点基本信息
    node_data = G.nodes[node_id]
    
    # 构建结果对象
    result = {
        "id": node_id,
        "name": node_data.get('name', str(node_id)),
        "type": node_data.get('type', ''),
        "upstream": [],  # 上游股权结构 (投资方)
        "downstream": []  # 下游股权结构 (被投资企业)
    }
    
    # 构建上游股权分析 - 从投资方开始
    for pred_id in G.predecessors(node_id):
        pred_data = G.nodes[pred_id]
        edge_data = G.get_edge_data(pred_id, node_id)
        percent = edge_data.get('percent', None) if edge_data else None
        percent_str = f"{percent*100:.2f}%" if percent is not None else "未知%"
        
        # 添加一级投资方
        investor_node = {
            "id": pred_id,
            "name": pred_data.get('name', str(pred_id)),
            "type": pred_data.get('type', ''),
            "percent": percent_str,
            "children": []
        }
        
        # 递归获取投资方的投资方 (二级投资方)
        for grand_pred_id in G.predecessors(pred_id):
            grand_pred_data = G.nodes[grand_pred_id]
            grand_edge_data = G.get_edge_data(grand_pred_id, pred_id)
            grand_percent = grand_edge_data.get('percent', None) if grand_edge_data else None
            grand_percent_str = f"{grand_percent*100:.2f}%" if grand_percent is not None else "未知%"
            
            # 添加二级投资方
            grand_investor_node = {
                "id": grand_pred_id,
                "name": grand_pred_data.get('name', str(grand_pred_id)),
                "type": grand_pred_data.get('type', ''),
                "percent": grand_percent_str,
                "children": []
            }
            
            investor_node["children"].append(grand_investor_node)
        
        result["upstream"].append(investor_node)
    
    # 构建下游股权分析 - 从被投资企业开始
    for succ_id in G.successors(node_id):
        succ_data = G.nodes[succ_id]
        edge_data = G.get_edge_data(node_id, succ_id)
        percent = edge_data.get('percent', None) if edge_data else None
        percent_str = f"{percent*100:.2f}%" if percent is not None else "未知%"
        
        # 添加一级被投资企业
        investee_node = {
            "id": succ_id,
            "name": succ_data.get('name', str(succ_id)),
            "type": succ_data.get('type', ''),
            "percent": percent_str,
            "children": []
        }
        
        # 递归获取被投资企业的被投资企业 (二级被投资企业)
        for grand_succ_id in G.successors(succ_id):
            grand_succ_data = G.nodes[grand_succ_id]
            grand_edge_data = G.get_edge_data(succ_id, grand_succ_id)
            grand_percent = grand_edge_data.get('percent', None) if grand_edge_data else None
            grand_percent_str = f"{grand_percent*100:.2f}%" if grand_percent is not None else "未知%"
            
            # 添加二级被投资企业
            grand_investee_node = {
                "id": grand_succ_id,
                "name": grand_succ_data.get('name', str(grand_succ_id)),
                "type": grand_succ_data.get('type', ''),
                "percent": grand_percent_str,
                "children": []
            }
            
            investee_node["children"].append(grand_investee_node)
        
        result["downstream"].append(investee_node)
    
    return jsonify(result)

if __name__ == '__main__':
    # 初始化加载图
    print("正在预加载图数据...")
    G = build_graph()
    calculate_node_metrics()
    print(f"图加载完成，共 {G.number_of_nodes()} 个节点和 {G.number_of_edges()} 条边")
    # 尝试使用8888端口，避免冲突
    app.run(debug=True, host='0.0.0.0', port=8888) 