# -*- coding: utf-8 -*-
import pandas as pd # Added import
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os # 添加导入os模块
# from matplotlib.font_manager import FontProperties # Imported via font_config
from community import best_partition # type: ignore
import seaborn as sns
from collections import defaultdict
# import json # No longer needed directly here

# 从新模块导入功能
from font_config import get_font_properties
from graph_builder import build_graph

# 确保输出目录存在
os.makedirs('outputs/reports', exist_ok=True)
os.makedirs('outputs/images', exist_ok=True)
os.makedirs('outputs/temp', exist_ok=True)

# 辅助函数：同时写入文件和打印到控制台
def write_and_print(file_handle, message, to_console=True):
    """同时写入文件和打印到控制台。"""
    if file_handle:
        file_handle.write(message + "\n")
    if to_console:
        print(message)

# 1. 设置字体
font = get_font_properties() # This will also handle plt.rcParams

# 2. 构建图
G = build_graph() # Uses graph_builder to get the graph object

# 创建文本报告文件
report_file_path = 'outputs/reports/advanced_analysis_report.txt'
report_file = open(report_file_path, 'w', encoding='utf-8')
write_and_print(report_file, "高级网络分析报告")
write_and_print(report_file, "=" * 50)

# --- 后续代码为原 advanced_analysis.py 中的分析部分 (保持不变) ---
# (确保下面的代码不依赖于被删除的 pandas 'df' 或本地定义的 'parse_children')

if G.number_of_nodes() == 0:
    write_and_print(report_file, "图为空，无法进行高级分析。请检查CSV文件和graph_builder.py的输出。")
    report_file.close()
    # exit() # Consider exiting if the graph is empty and analysis cannot proceed
else:
    # 创建无向图版本用于一些算法 (如果后续分析需要)
    UG = G.to_undirected()

    # 1. 中心性分析
    write_and_print(report_file, "中心性分析:")
    write_and_print(report_file, "="*50)

    # 度中心性：连接节点最多的实体
    degree_centrality = nx.degree_centrality(G)
    top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    write_and_print(report_file, "\n度中心性前5名（连接最多的实体）:")
    for node, centrality in top_degree:
        write_and_print(report_file, f"{G.nodes[node]['name']}: {centrality:.4f}")

    # 接近中心性：到其他所有节点距离最短的实体
    try:
        closeness_centrality = nx.closeness_centrality(G)
        top_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        write_and_print(report_file, "\n接近中心性前5名（到其他节点平均距离最短的实体）:")
        for node, centrality in top_closeness:
            write_and_print(report_file, f"{G.nodes[node]['name']}: {centrality:.4f}")
    except:
        write_and_print(report_file, "\n计算接近中心性时出错，可能是图不连通")

    # 中介中心性：位于最多最短路径上的实体（信息流/控制流的"桥梁"）
    try:
        betweenness_centrality = nx.betweenness_centrality(G)
        top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        write_and_print(report_file, "\n中介中心性前5名（最关键的'桥梁'实体）:")
        for node, centrality in top_betweenness:
            write_and_print(report_file, f"{G.nodes[node]['name']}: {centrality:.4f}")
    except:
        write_and_print(report_file, "\n计算中介中心性时出错")

    # 特征向量中心性：连接到其他重要节点的实体
    try:
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
        top_eigen = sorted(eigenvector_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        write_and_print(report_file, "\n特征向量中心性前5名（连接到重要实体的实体）:")
        for node, centrality in top_eigen:
            write_and_print(report_file, f"{G.nodes[node]['name']}: {centrality:.4f}")
    except:
        write_and_print(report_file, "\n计算特征向量中心性时出错，尝试用无向图计算")
        try:
            eigenvector_centrality = nx.eigenvector_centrality(UG, max_iter=1000)
            top_eigen = sorted(eigenvector_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            write_and_print(report_file, "\n特征向量中心性前5名（连接到重要实体的实体）- 基于无向图:")
            for node, centrality in top_eigen:
                write_and_print(report_file, f"{G.nodes[node]['name']}: {centrality:.4f}")
        except:
            write_and_print(report_file, "无向图也无法计算特征向量中心性")

    # 2. 社区检测（使用python-louvain库中的社区检测算法）
    try:
        # 在无向图上执行社区检测
        partition = best_partition(UG)
        
        # 统计社区信息
        communities = defaultdict(list)
        for node, community_id in partition.items():
            communities[community_id].append(node)
        
        write_and_print(report_file, "\n\n社区检测结果:")
        write_and_print(report_file, "="*50)
        write_and_print(report_file, f"检测到 {len(communities)} 个社区")
        
        # 显示前3个最大社区
        largest_communities = sorted(communities.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        for i, (community_id, members) in enumerate(largest_communities):
            write_and_print(report_file, f"\n社区 {i+1}（{len(members)}个成员）:")
            for j, node in enumerate(members[:5]):  # 只显示前5个成员
                write_and_print(report_file, f"  - {G.nodes[node]['name']}")
            if len(members) > 5:
                write_and_print(report_file, f"  - ... 以及其他 {len(members) - 5} 个成员")
            
        # 可视化社区
        plt.figure(figsize=(20, 15))
        
        # 使用spring_layout算法
        pos = nx.spring_layout(UG, k=0.2, iterations=50)
        
        # 为每个社区分配一个颜色
        community_colors = sns.color_palette("husl", len(communities))
        node_colors = [community_colors[partition[node]] for node in UG.nodes()]
        
        # 绘制节点
        nx.draw_networkx_nodes(UG, pos, node_size=300, node_color=node_colors, alpha=0.8)
        
        # 绘制边
        nx.draw_networkx_edges(UG, pos, width=0.5, alpha=0.5)
        
        # 添加节点标签
        labels = {node: G.nodes[node]['name'] for node in G.nodes()}
        
        # 绘制节点标签
        font_kwargs = {}
        if font is not None:
            font_kwargs['font_family'] = font.get_name()
        nx.draw_networkx_labels(UG, pos, labels=labels, font_size=8, **font_kwargs)
        
        # 设置标题
        plt.title('股权关系社区结构', fontsize=20)
        if font is not None:
            plt.title('股权关系社区结构', fontproperties=font, fontsize=20)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('outputs/images/股权关系社区结构.png', dpi=300, bbox_inches='tight')
        write_and_print(report_file, f"\n社区结构可视化已保存至: outputs/images/股权关系社区结构.png")
        
    except ImportError:
        write_and_print(report_file, "无法进行社区检测，请安装python-louvain库: pip install python-louvain")
    except Exception as e:
        write_and_print(report_file, f"社区检测过程中出错: {e}")

    # 3. 寻找循环持股关系（环）
    write_and_print(report_file, "\n\n循环持股关系分析:")
    write_and_print(report_file, "="*50)

    cycles = list(nx.simple_cycles(G))
    if cycles:
        write_and_print(report_file, f"发现 {len(cycles)} 个循环持股关系")
        
        # 显示前5个循环
        for i, cycle in enumerate(cycles[:5]):
            write_and_print(report_file, f"\n循环 {i+1}:")
            for node in cycle:
                write_and_print(report_file, f"  - {G.nodes[node]['name']}")
            
            # 计算这个循环中的持股比例
            total_control = 1.0
            write_and_print(report_file, "持股路径:")
            for j in range(len(cycle)):
                source = cycle[j]
                target = cycle[(j+1) % len(cycle)]
                if G.has_edge(source, target):
                    percent_str = G.edges[source, target].get('percent', '未知')
                    # 尝试将百分比转为浮点数
                    try:
                        if isinstance(percent_str, str) and '%' in percent_str:
                            percent = float(percent_str.replace('%', '')) / 100
                        else:
                            percent = float(percent_str) if percent_str != '未知' else 0
                        total_control *= percent
                    except:
                        percent = '未知'
                    
                    write_and_print(report_file, f"  {G.nodes[source]['name']} -> {G.nodes[target]['name']}: {percent_str}")
            
            # 如果成功计算了所有百分比，显示总体控制比例
            if isinstance(total_control, float):
                write_and_print(report_file, f"  循环控制比例: {total_control:.6f} ({total_control*100:.4f}%)")
    else:
        write_and_print(report_file, "未发现循环持股关系")

    # 4. 集中控制分析 - 找出控制多个实体的关键股东及其控制的企业网络
    write_and_print(report_file, "\n\n关键控制者分析:")
    write_and_print(report_file, "="*50)

    # 按出度（控制的企业数量）排序
    out_degrees = dict(G.out_degree())
    top_controllers = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)

    # 分析前3名控制者
    for i, (node, degree) in enumerate(top_controllers[:3]):
        if degree > 0:  # 确保有出边
            write_and_print(report_file, f"\n关键控制者 {i+1}: {G.nodes[node]['name']} (控制 {degree} 个实体)")
            
            # 获取控制的所有实体
            controlled_entities = []
            for _, target, data in G.out_edges(node, data=True):
                percent = data.get('percent', '未知')
                controlled_entities.append((target, G.nodes[target]['name'], percent))
            
            # 按持股比例排序（如果可行）
            try:
                controlled_entities.sort(key=lambda x: float(x[2].replace('%', '')) if isinstance(x[2], str) and '%' in x[2] else 0, reverse=True)
            except:
                pass  # 排序失败就使用原顺序
            
            # 打印前5个控制的实体
            for j, (entity_id, entity_name, percent) in enumerate(controlled_entities[:5]):
                write_and_print(report_file, f"  - {entity_name}: {percent}")
            
            if len(controlled_entities) > 5:
                write_and_print(report_file, f"  - ... 以及其他 {len(controlled_entities) - 5} 个实体")

    # 5. 最终控制人分析
    write_and_print(report_file, "\n\n5. 最终控制人分析:")
    write_and_print(report_file, "="*50)

    # 寻找没有入边的节点（树的根，最终控制人）
    ultimate_controllers = [node for node, in_degree in G.in_degree() if in_degree == 0]

    write_and_print(report_file, f"发现 {len(ultimate_controllers)} 个潜在的最终控制人")

    # 分析每个最终控制人控制的实体
    for i, controller in enumerate(ultimate_controllers[:5]):  # 只显示前5个
        write_and_print(report_file, f"\n最终控制人 {i+1}: {G.nodes[controller]['name']}")
        
        # 计算这个控制人的影响力 - 从这个节点可到达的所有节点
        reachable = nx.descendants(G, controller)
        write_and_print(report_file, f"  可直接或间接影响 {len(reachable)} 个实体")
        # 可以进一步分析这些实体，例如按类型统计等

    # 6. 股权穿透分析
    write_and_print(report_file, "\n\n6. 股权穿透分析:")
    write_and_print(report_file, "="*50)

    def get_shareholding_paths(graph, target_node_id, current_path=None, visited_in_path=None, all_paths=None, max_depth=10, current_depth=0, accumulated_percent=1.0):
        """
        递归向上查找指定目标节点的所有最终股东路径及其累积持股比例。
        target_node_id: 目标公司的ID。
        current_path: 当前正在构建的路径 [ (node, percent_from_previous_in_path), ... ]。
                     对于路径的第一个节点(即target_node_id)，percent_from_previous_in_path 为 1.0。
        visited_in_path: 当前路径中已访问的节点，用于防环。
        all_paths: 收集所有找到的完整路径。
        max_depth: 最大穿透层数。
        current_depth: 当前递归深度。
        accumulated_percent: 从路径起始点到当前节点上一节点的累积百分比。
        返回: 路径列表，每条路径是 [(node_name, percent_on_edge_to_next, cumulative_percent_to_node), ...]
        """
        if current_path is None:
            current_path = []
        if visited_in_path is None:
            visited_in_path = set()
        if all_paths is None:
            all_paths = []

        current_path.append({
            'id': target_node_id, 
            'name': graph.nodes[target_node_id].get('name', target_node_id),
            'cumulative_percent': accumulated_percent 
        })
        visited_in_path.add(target_node_id)

        predecessors = list(graph.predecessors(target_node_id))

        if not predecessors or current_depth >= max_depth:
            formatted_path = []
            for i in range(len(current_path)):
                node_info = current_path[i]
                formatted_path.append({
                    'id': node_info['id'],
                    'name': node_info['name'],
                    'cumulative_percent_at_node': node_info['cumulative_percent']
                })
            all_paths.append(list(reversed(formatted_path))) 
        else:
            for shareholder_node_id in predecessors:
                if shareholder_node_id not in visited_in_path:
                    edge_data = graph.get_edge_data(shareholder_node_id, target_node_id)
                    percent_on_edge = edge_data.get('percent', 0.0) if edge_data else 0.0
                    if percent_on_edge is None: percent_on_edge = 0.0 
                    
                    new_accumulated_percent = accumulated_percent * percent_on_edge
                    
                    get_shareholding_paths(graph, shareholder_node_id, 
                                             current_path, visited_in_path, 
                                             all_paths, max_depth, current_depth + 1, 
                                             new_accumulated_percent)
        
        visited_in_path.remove(target_node_id)
        current_path.pop()
        return all_paths

    def get_investment_paths(graph, source_node_id, current_path=None, visited_in_path=None, all_paths=None, max_depth=10, current_depth=0, accumulated_percent=1.0):
        """
        递归向下查找指定源节点的所有投资路径及其累积控制比例。
        source_node_id: 源公司/个人的ID。
        返回: 路径列表，格式类似 get_shareholding_paths
        """
        if current_path is None:
            current_path = []
        if visited_in_path is None:
            visited_in_path = set()
        if all_paths is None:
            all_paths = []

        current_path.append({
            'id': source_node_id,
            'name': graph.nodes[source_node_id].get('name', source_node_id),
            'cumulative_percent': accumulated_percent
        })
        visited_in_path.add(source_node_id)

        successors = list(graph.successors(source_node_id))

        if not successors or current_depth >= max_depth:
            formatted_path = []
            for node_info in current_path:
                formatted_path.append({
                    'id': node_info['id'],
                    'name': node_info['name'],
                    'cumulative_percent_at_node': node_info['cumulative_percent'] 
                })
            all_paths.append(formatted_path) 
        else:
            for invested_node_id in successors:
                if invested_node_id not in visited_in_path:
                    edge_data = graph.get_edge_data(source_node_id, invested_node_id)
                    percent_on_edge = edge_data.get('percent', 0.0) if edge_data else 0.0
                    if percent_on_edge is None: percent_on_edge = 0.0
                    
                    new_accumulated_percent = accumulated_percent * percent_on_edge
                    
                    get_investment_paths(graph, invested_node_id, 
                                         current_path, visited_in_path, 
                                         all_paths, max_depth, current_depth + 1, 
                                         new_accumulated_percent)
        
        visited_in_path.remove(source_node_id)
        current_path.pop()
        return all_paths

    example_target_node_for_upward = None 
    example_source_node_for_downward = None

    if G.number_of_nodes() > 0:
        for node_id in G.nodes():
            if G.out_degree(node_id) > 0:
                example_source_node_for_downward = node_id
                break
        for node_id in G.nodes():
            if G.in_degree(node_id) > 0:
                example_target_node_for_upward = node_id
                break

    if example_target_node_for_upward:
        node_name_up = G.nodes[example_target_node_for_upward].get('name', example_target_node_for_upward)
        write_and_print(report_file, f"\n向上穿透分析 (查找股东路径) for node: {node_name_up} (ID: {example_target_node_for_upward})")
        upward_paths = get_shareholding_paths(G, example_target_node_for_upward, max_depth=5)
        if upward_paths:
            write_and_print(report_file, f"  发现 {len(upward_paths)} 条到最终股东的路径:")
            for i, path in enumerate(upward_paths[:5]): 
                path_str_parts = []
                if not path: continue
                for j in range(len(path)):
                    step = path[j]
                    path_str_parts.append(step['name'])
                    if j < len(path) - 1: # If not the last node in the path display (which is the target for upward)
                        # Edge is from path[j]['id'] to path[j+1]['id']
                        edge_data = G.get_edge_data(step['id'], path[j+1]['id'])
                        percent_on_edge = edge_data.get('percent', 0.0) if edge_data else 0.0
                        if percent_on_edge is None: percent_on_edge = 0.0
                        path_str_parts.append(f" --[{percent_on_edge*100:.2f}%]--> ")
                
                final_cumulative_percent = path[0]['cumulative_percent_at_node'] # First node in reversed path is ultimate owner
                write_and_print(report_file, f"    路径 {i+1}: {''.join(path_str_parts)}. (最终累积: {final_cumulative_percent*100:.4f}%)")
        else:
            write_and_print(report_file, "  未找到向上的股东路径或节点为根节点。")
    else:
        write_and_print(report_file, "\n未能选择有效的向上穿透分析起始节点。")

    if example_source_node_for_downward:
        node_name_down = G.nodes[example_source_node_for_downward].get('name', example_source_node_for_downward)
        write_and_print(report_file, f"\n向下穿透分析 (查找投资路径) for node: {node_name_down} (ID: {example_source_node_for_downward})")
        downward_paths = get_investment_paths(G, example_source_node_for_downward, max_depth=5)
        if downward_paths:
            write_and_print(report_file, f"  发现 {len(downward_paths)} 条投资路径:")
            for i, path in enumerate(downward_paths[:5]): 
                path_str_parts = []
                if not path: continue
                for j in range(len(path)):
                    step = path[j]
                    path_str_parts.append(step['name'])
                    if j < len(path) - 1: # If not the last node in the path
                        edge_data = G.get_edge_data(step['id'], path[j+1]['id'])
                        percent_on_edge = edge_data.get('percent', 0.0) if edge_data else 0.0
                        if percent_on_edge is None: percent_on_edge = 0.0
                        path_str_parts.append(f" --[{percent_on_edge*100:.2f}%]--> ")
                
                # For downward path, the cumulative percent of the last node is the one we care about to that specific leaf/depth.
                # However, the 'cumulative_percent_at_node' for the first node (source) is 1.0.
                # The path[0]['cumulative_percent_at_node'] is the initial 1.0 for the source.
                # The path[-1]['cumulative_percent_at_node'] is the cumulative effect AT THE LAST NODE of the path.
                final_cumulative_percent_at_leaf = path[-1]['cumulative_percent_at_node']
                write_and_print(report_file, f"    路径 {i+1}: {''.join(path_str_parts)}. (至路径末端累积: {final_cumulative_percent_at_leaf*100:.4f}%)")
        else:
            write_and_print(report_file, "  未找到向下的投资路径或节点为叶子节点。")
    else:
        write_and_print(report_file, "\n未能选择有效的向下穿透分析起始节点。")

    # 7. 关联方初步分析 (共同投资)
    write_and_print(report_file, "\n\n7. 关联方初步分析 (共同投资):")
    write_and_print(report_file, "="*50)
    
    found_common_investments = False
    # Limit the number of companies to report to avoid excessive output
    companies_reported_for_common_investment = 0
    max_companies_to_report_ci = 10 # 最多报告10家公司的情况
    max_shareholders_to_display_per_company = 10 # 每家公司最多显示10个股东

    # 按入度对节点排序，优先分析被较多实体投资的公司
    sorted_nodes_by_in_degree = sorted(G.nodes(), key=lambda n: G.in_degree(n), reverse=True)

    for node_id in sorted_nodes_by_in_degree:
        if companies_reported_for_common_investment >= max_companies_to_report_ci:
            if found_common_investments: # 只有在已经找到一些共同投资的情况下才打印这条消息
                write_and_print(report_file, f"\n  (已显示前 {max_companies_to_report_ci} 个存在共同投资情况的公司，更多信息请直接查询图数据或调整脚本参数)")
            break

        # 只考虑确实有多个入边的节点 (即被多个股东投资)
        if G.in_degree(node_id) > 1: 
            shareholders_details = []
            for shareholder_id in G.predecessors(node_id):
                # 确保 shareholder_id 存在于图中 (通常应该存在，但作为安全检查)
                if shareholder_id not in G.nodes:
                    # print(f"Warning: Shareholder ID {shareholder_id} found as predecessor but not in G.nodes. Skipping.")
                    continue 
                
                sh_node_data = G.nodes[shareholder_id]
                sh_name = sh_node_data.get('name', shareholder_id)
                sh_type = sh_node_data.get('type', '未知类型')
                
                edge_data = G.get_edge_data(shareholder_id, node_id)
                percent_on_edge = edge_data.get('percent', None) if edge_data else None
                percent_str = f"{percent_on_edge*100:.2f}%" if percent_on_edge is not None else "未知%"
                
                shareholders_details.append(f"{sh_name} (ID: {shareholder_id}, 类型: {sh_type}, 持股: {percent_str})")
            
            # 再次确认确实收集到了多个股东信息 (以防上面的continue跳过了一些)
            if len(shareholders_details) > 1:
                if not found_common_investments:
                    write_and_print(report_file, "发现以下公司存在共同投资的股东情况 (按被投资公司总入股方数排序，显示部分)：")
                    found_common_investments = True
                
                target_company_name = G.nodes[node_id].get('name', node_id)
                write_and_print(report_file, f"\n公司: {target_company_name} (ID: {node_id}, 总入股方数: {G.in_degree(node_id)})")
                write_and_print(report_file, f"  共同投资方 ({len(shareholders_details)}):")
                for sh_detail in shareholders_details[:max_shareholders_to_display_per_company]: 
                    write_and_print(report_file, f"    - {sh_detail}")
                if len(shareholders_details) > max_shareholders_to_display_per_company:
                    write_and_print(report_file, f"    - ...以及其他 {len(shareholders_details) - max_shareholders_to_display_per_company} 个投资方。")
                companies_reported_for_common_investment +=1

    if not found_common_investments:
        write_and_print(report_file, "未发现多股东共同投资于同一公司的情况。")

    # 8. 链路合理性检查 (Sanity Checks for Links)
    write_and_print(report_file, "\n\n8. 链路合理性检查:")
    write_and_print(report_file, "="*50)

    # 检查 8.1: 自循环
    self_loops = []
    for u, v_node_id in G.edges(): # Renamed v to v_node_id to avoid conflict
        if u == v_node_id:
            self_loops.append(u)

    if self_loops:
        write_and_print(report_file, f"\n警告：发现 {len(self_loops)} 个自循环:")
        for node_id in self_loops[:5]: # 显示前5个
            write_and_print(report_file, f"  - 节点 '{G.nodes[node_id].get('name', node_id)}' 指向自身")
    else:
        write_and_print(report_file, "\n检查通过：未发现自循环。")

    # 检查 8.2: 父节点（投资方）缺少名称信息
    parents_missing_names = []
    for node_id, data in G.nodes(data=True):
        if G.out_degree(node_id) > 0:  # 这是一个父节点 (投资方)
            node_name = data.get('name')
            if pd.isna(node_name) or (isinstance(node_name, str) and node_name.strip() == ''):
                parents_missing_names.append(node_id)

    if parents_missing_names:
        write_and_print(report_file, f"\n警告：发现 {len(set(parents_missing_names))} 个父节点（投资方）缺少名称信息。这可能表明其定义不完整:")
        for p_id in list(set(parents_missing_names))[:5]: # 显示前5个独特的父节点ID
            # 获取该父节点投资的子公司名称以提供上下文
            children_names = []
            for _, child_id in G.out_edges(p_id):
                if child_id in G.nodes and G.nodes[child_id].get('name'):
                     children_names.append(G.nodes[child_id].get('name'))
                else:
                     children_names.append(f"ID: {child_id} (名称缺失)")
            write_and_print(report_file, f"  - 父节点ID '{p_id}' (名称缺失) 投资了: {children_names[:3]}")
    else:
        write_and_print(report_file, "\n检查通过：所有父节点（投资方）均具有名称信息。")

    # 检查 8.3: 边属性 'percent' (持股比例) 的合理性
    invalid_percentages = []
    num_edges_checked = 0
    for u, v_node_id, data in G.edges(data=True): # Renamed v to v_node_id
        num_edges_checked += 1
        percent_str = data.get('percent')
        
        # 安全地获取节点名称，如果节点或名称不存在则使用ID
        u_name = G.nodes[u].get('name', f"ID:{u}") if u in G.nodes else f"ID:{u}"
        v_name = G.nodes[v_node_id].get('name', f"ID:{v_node_id}") if v_node_id in G.nodes else f"ID:{v_node_id}"
        edge_info = f"从 '{u_name}' 到 '{v_name}'"

        if pd.isna(percent_str) or (isinstance(percent_str, str) and percent_str.strip() == ''):
            invalid_percentages.append(f"  - {edge_info}: 持股比例缺失")
            continue

        try:
            percent_val_temp = -1.0 # 初始化一个临时值
            if isinstance(percent_str, str):
                # 清理字符串，移除可能的空白符
                cleaned_percent_str = percent_str.strip()
                if '%' in cleaned_percent_str:
                    percent_val_temp = float(cleaned_percent_str.replace('%', '').strip())
                elif cleaned_percent_str: # 非空字符串但没有 '%'
                    percent_val_temp = float(cleaned_percent_str)
                else: # 空字符串处理（虽然上面已检查，但作为双重保障）
                     invalid_percentages.append(f"  - {edge_info}: 持股比例为空字符串")
                     continue
            elif isinstance(percent_str, (int, float)): # 如果已经是数字
                percent_val_temp = float(percent_str)
            else: # 未知类型
                 invalid_percentages.append(f"  - {edge_info}: 持股比例 '{percent_str}' 类型未知 ({type(percent_str)})")
                 continue
            
            # 检查范围
            if not (0 <= percent_val_temp <= 100):
                invalid_percentages.append(f"  - {edge_info}: 持股比例 '{percent_str}' (解析为 {percent_val_temp:.2f}) 超出合理范围 (0-100%)")

        except ValueError:
            invalid_percentages.append(f"  - {edge_info}: 持股比例 '{percent_str}' 无法解析为有效数字")
        except Exception as e: 
            invalid_percentages.append(f"  - {edge_info}: 解析持股比例 '{percent_str}' 时发生意外错误: {e}")


    if invalid_percentages:
        write_and_print(report_file, f"\n警告：发现 {len(invalid_percentages)} 条边的持股比例数据存在问题 (共检查 {num_edges_checked} 条边):")
        for issue in invalid_percentages[:10]: # 显示前10条问题记录
            write_and_print(report_file, issue)
    else:
        write_and_print(report_file, f"\n检查通过：所有 {num_edges_checked} 条边的持股比例数据格式和范围基本合理。") 
    
    # 关闭报告文件
    write_and_print(report_file, "\n" + "="*50)
    write_and_print(report_file, "分析报告完成。")
    report_file.close()

    print(f"\n分析报告已保存至: {report_file_path}")
    print(f"可视化图像已保存至: outputs/images/") 