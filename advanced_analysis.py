# -*- coding: utf-8 -*-
import pandas as pd # Added import
import networkx as nx
# import matplotlib.pyplot as plt # Removed
import numpy as np
import os # 添加导入os模块
# from matplotlib.font_manager import FontProperties # Imported via font_config
from community import best_partition # type: ignore
# import seaborn as sns # Removed
from collections import defaultdict
# import json # No longer needed directly here

# 从新模块导入功能
from font_config import get_font_properties # Keep for now, though its direct use (plt.rcParams) is gone
from graph_builder import build_graph

# 确保输出目录存在
os.makedirs('outputs/reports', exist_ok=True)
# os.makedirs('outputs/images', exist_ok=True) # Removed
os.makedirs('outputs/temp', exist_ok=True)

# 辅助函数：同时写入文件和打印到控制台
def write_and_print(file_handle, message, to_console=True):
    """同时写入文件和打印到控制台。"""
    if file_handle:
        file_handle.write(message + "\n")
    if to_console:
        print(message)

# 1. 设置字体
font = get_font_properties() # Keep for now, though plt is removed

# 2. 构建图
G = build_graph("三层股权穿透输出数据_1.csv") # Uses graph_builder to get the graph object

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
    for node, centrality_val in top_degree: # Renamed centrality for clarity
        write_and_print(report_file, f"{G.nodes[node].get('name', node)}: {centrality_val:.4f}")

    # PageRank中心性
    # Initialize pagerank_centrality in case of calculation failure
    pagerank_centrality_map = {} # Use a different name for the map
    try:
        pagerank_centrality_map = nx.pagerank(G, alpha=0.85)
        top_pagerank = sorted(pagerank_centrality_map.items(), key=lambda x: x[1], reverse=True)[:5]
        write_and_print(report_file, "\nPageRank前5名（网络影响力最大）:")
        for node, pr in top_pagerank:
            write_and_print(report_file, f"{G.nodes[node].get('name', node)}: {pr:.4f}")
    except Exception as e:
        write_and_print(report_file, f"\nPageRank计算出错: {e}")
        pagerank_centrality_map = {} # Ensure it's an empty dict on error

    # 接近中心性：到其他所有节点距离最短的实体
    try:
        # closeness_centrality = nx.closeness_centrality(G) # 对于大型不连通图非常耗时，暂时注释
        # top_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        # write_and_print(report_file, "\n接近中心性前5名（到其他节点平均距离最短的实体）:")
        # for node, centrality_val in top_closeness: # Renamed centrality
        #     write_and_print(report_file, f"{G.nodes[node].get('name', node)}: {centrality_val:.4f}")
        write_and_print(report_file, "\n接近中心性：计算成本较高，已在此版本中暂时禁用以提高性能。")
    except Exception as e: # Changed from general except
        write_and_print(report_file, f"尝试处理接近中心性（已禁用）时发生预料之外的错误: {e}")

    # 中介中心性：位于最多最短路径上的实体（信息流/控制流的"桥梁"）
    # Initialize betweenness_centrality in case of calculation failure
    # This variable will be reused later
    betweenness_centrality_map = {} # Use a different name for the map
    try:
        # 为提高性能，引入采样参数 k。对于大型图，不使用采样会非常慢。
        # k 的值可以根据图的大小和可接受的计算时间进行调整。
        # 对于拥有数万节点的图，k=100 或 k=200 是一个合理的起点。
        write_and_print(report_file, "\n计算中介中心性 (采样 k=100)...")
        betweenness_centrality_map = nx.betweenness_centrality(G, k=100, normalized=True) # 添加 k=100 和 normalized=True
        top_betweenness = sorted(betweenness_centrality_map.items(), key=lambda x: x[1], reverse=True)[:5]
        write_and_print(report_file, "中介中心性前5名（最关键的'桥梁'实体）:")
        for node, centrality_val in top_betweenness: # Renamed centrality
            write_and_print(report_file, f"{G.nodes[node].get('name', node)}: {centrality_val:.4f}") 
    except Exception as e: # 更具体地捕获异常
        write_and_print(report_file, f"\n计算中介中心性时出错: {e}")
        betweenness_centrality_map = {} # Ensure it's an empty dict on error


    # 特征向量中心性：连接到其他重要节点的实体
    try:
        eigenvector_centrality_map = nx.eigenvector_centrality(G, max_iter=1000) # Use a different name for the map
        top_eigen = sorted(eigenvector_centrality_map.items(), key=lambda x: x[1], reverse=True)[:5]
        write_and_print(report_file, "\n特征向量中心性前5名（连接到重要实体的实体）:")
        for node, centrality_val in top_eigen: # Renamed centrality
            write_and_print(report_file, f"{G.nodes[node].get('name', node)}: {centrality_val:.4f}")
    except Exception as e_outer: # Catch specific exception
        write_and_print(report_file, f"\n计算特征向量中心性时出错 (有向图): {e_outer}。尝试用无向图计算...")
        try:
            eigenvector_centrality_map = nx.eigenvector_centrality(UG, max_iter=1000) # Use UG
            top_eigen = sorted(eigenvector_centrality_map.items(), key=lambda x: x[1], reverse=True)[:5]
            write_and_print(report_file, "特征向量中心性前5名（连接到重要实体的实体）- 基于无向图:")
            for node, centrality_val in top_eigen: # Renamed centrality
                write_and_print(report_file, f"{G.nodes[node].get('name', node)}: {centrality_val:.4f}")
        except Exception as e_inner: # Catch specific exception
            write_and_print(report_file, f"无向图也无法计算特征向量中心性: {e_inner}")

    # 2. 社区检测（使用python-louvain库中的社区检测算法）
    try:
        # 在无向图上执行社区检测
        write_and_print(report_file, "\n\n社区检测 (Louvain算法):")
        write_and_print(report_file, "="*50)
        partition = best_partition(UG)
        
        # 统计社区信息
        communities = defaultdict(list)
        for node, community_id in partition.items():
            communities[community_id].append(node)
        
        write_and_print(report_file, f"检测到 {len(communities)} 个社区")
        
        # 显示前3个最大社区
        largest_communities = sorted(communities.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        for i, (community_id, members) in enumerate(largest_communities):
            write_and_print(report_file, f"\n社区 {i+1}（{len(members)}个成员）:")
            for j, node in enumerate(members[:5]):  # 只显示前5个成员
                write_and_print(report_file, f"  - {G.nodes[node].get('name', node)}")
            if len(members) > 5:
                write_and_print(report_file, f"  - ... 以及其他 {len(members) - 5} 个成员")
            
        # 可视化社区部分已移除
        write_and_print(report_file, "\n社区结构的可视化部分已移除以优化性能。")
        
    except ImportError:
        write_and_print(report_file, "\n无法进行社区检测，请安装python-louvain库: pip install python-louvain")
    except Exception as e:
        write_and_print(report_file, f"\n社区检测过程中出错: {e}")

    # 3. 寻找循环持股关系（环）
    write_and_print(report_file, "\n\n循环持股关系分析:")
    write_and_print(report_file, "="*50)
    write_and_print(report_file, "警告：计算所有简单循环（nx.simple_cycles）在大型或密集网络中可能非常耗时且占用大量内存。如果脚本在此处长时间无响应，请考虑注释掉此部分或针对特定子图运行。")

    try:
        cycles = list(nx.simple_cycles(G))
        if cycles:
            write_and_print(report_file, f"发现 {len(cycles)} 个循环持股关系")
            
            # 显示前5个循环
            for i, cycle in enumerate(cycles[:5]):
                write_and_print(report_file, f"\n循环 {i+1}:")
                path_names = [G.nodes[node].get('name', node) for node in cycle]
                write_and_print(report_file, " -> ".join(path_names) + f" -> {path_names[0]}") # Show cycle path
                
                # 计算这个循环中的持股比例
                total_control = 1.0
                valid_percents_for_cycle = True
                write_and_print(report_file, "持股路径详情:")
                for j_idx in range(len(cycle)): # Renamed j to j_idx
                    source = cycle[j_idx]
                    target = cycle[(j_idx+1) % len(cycle)]
                    if G.has_edge(source, target):
                        percent_str = G.edges[source, target].get('percent', '未知')
                        percent_val = '未知' # For display
                        try:
                            if isinstance(percent_str, str) and '%' in percent_str:
                                percent = float(percent_str.replace('%', '').strip()) / 100
                            elif isinstance(percent_str, str) and percent_str.strip():
                                percent = float(percent_str.strip())
                            elif isinstance(percent_str, (float, int)):
                                percent = float(percent_str)
                            else: # Includes None or empty string after strip
                                percent = 0 # Assume 0 if unknown or invalid for calculation
                                valid_percents_for_cycle = False
                            
                            if not (0 <= percent <= 1): # Assuming percent is now 0-1 scale
                                percent = 0 # Invalid range, treat as 0 for calculation
                                valid_percents_for_cycle = False

                            total_control *= percent
                            percent_val = percent_str # Display original string

                        except ValueError:
                            percent_val = f"{percent_str} (无法解析)"
                            total_control *= 0 # Invalid, treat as 0 factor
                            valid_percents_for_cycle = False
                        
                        write_and_print(report_file, f"  {G.nodes[source].get('name', source)} -> {G.nodes[target].get('name', target)}: {percent_val}")
                    else: # Should not happen in a simple cycle from nx.simple_cycles
                        write_and_print(report_file, f"  警告: 循环中缺失边 {G.nodes[source].get('name', source)} -> {G.nodes[target].get('name', target)}")
                        valid_percents_for_cycle = False
                
                if valid_percents_for_cycle and isinstance(total_control, float):
                    write_and_print(report_file, f"  该循环的近似累积控制比例: {total_control:.6f} ({total_control*100:.4f}%)")
                else:
                    write_and_print(report_file, "  该循环的累积控制比例无法精确计算（由于部分持股比例未知或无效）。")
        else:
            write_and_print(report_file, "未发现循环持股关系")
    except Exception as e:
        write_and_print(report_file, f"\n寻找循环持股关系时出错: {e}")


    # 4. 集中控制分析 - 找出控制多个实体的关键股东及其控制的企业网络
    write_and_print(report_file, "\n\n关键控制者分析:")
    write_and_print(report_file, "="*50)
    
    # write_and_print(report_file, "关键控制者分析基于以下逻辑：")
    # write_and_print(report_file, "1. 出度高的节点代表控制/投资多个实体的股东")
    # write_and_print(report_file, "2. 持股比例反映控制力的强度")
    # write_and_print(report_file, "3. 与中心性指标结合，可判断节点在网络中的影响力")
    # write_and_print(report_file, "4. 关键控制者的判定综合考虑：控制企业数量、持股比例、PageRank等指标\\n")

    # 按出度（控制的企业数量）排序
    out_degrees = dict(G.out_degree())
    top_controllers = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)

    # 使用前面计算的 PageRank (pagerank_centrality_map)
    # 使用前面计算的、带采样的 Betweenness Centrality (betweenness_centrality_map)
    # betweenness_centrality_map is already defined and populated (or empty if error)

    # 分析前3名控制者
    for i, (node, degree) in enumerate(top_controllers[:3]):
        if degree > 0:  # 确保有出边
            node_name = G.nodes[node].get('name', node) # Get name once
            # 获取节点指标
            pr_score = pagerank_centrality_map.get(node, 0.0) # Use from map
            btw_score = betweenness_centrality_map.get(node, 0.0) # Use from map (sampled)
            node_type = G.nodes[node].get('type', '未知')
            in_degree = G.in_degree(node)
            
            write_and_print(report_file, f"\n关键控制者 {i+1}: {node_name}")
            write_and_print(report_file, f"  • 控制实体数: {degree}")
            write_and_print(report_file, f"  • 节点类型: {node_type}")
            write_and_print(report_file, f"  • PageRank: {pr_score:.4f}")
            write_and_print(report_file, f"  • 中介中心性 (采样 k=100): {btw_score:.4f}") # Clarify sampled
            write_and_print(report_file, f"  • 入度(被投资数): {in_degree}")
            
            # 获取控制的所有实体
            controlled_entities = []
            for _, target, edge_data in G.out_edges(node, data=True): # Renamed data to edge_data
                percent = edge_data.get('percent', '未知')
                controlled_entities.append((target, G.nodes[target].get('name', target), percent))
            
            # 按持股比例排序（如果可行）
            try:
                # Robust sorting for percent strings
                def sort_key_percent(item):
                    p_str = item[2]
                    if isinstance(p_str, str):
                        if '%' in p_str:
                            return float(p_str.replace('%','').strip())
                        elif p_str.strip():
                            return float(p_str.strip())
                    elif isinstance(p_str, (float, int)):
                        return float(p_str)
                    return -1 # Default for unparsable or missing, sort them last
                controlled_entities.sort(key=sort_key_percent, reverse=True)
            except ValueError: # Catch if float conversion fails for some reason
                pass  # 排序失败就使用原顺序
            
            # 打印前5个控制的实体
            write_and_print(report_file, f"  控制的实体（部分按持股比例排序，显示前5个）:")
            for j_idx, (entity_id, entity_name, percent) in enumerate(controlled_entities[:5]): # Renamed j
                target_type = G.nodes[entity_id].get('type', '未知')
                write_and_print(report_file, f"    - {entity_name} (类型: {target_type}, 持股: {percent})")
            
            if len(controlled_entities) > 5:
                write_and_print(report_file, f"    - ... 以及其他 {len(controlled_entities) - 5} 个实体")

    # 7. 链路合理性检查 (Sanity Checks for Links)
    write_and_print(report_file, "\n\n7. 链路合理性检查:")
    write_and_print(report_file, "="*50)

    # 检查 7.1: 自循环
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

    # 检查 7.2: 父节点（投资方）缺少名称信息
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

    # 检查 7.3: 边属性 'percent' (持股比例) 的合理性
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
    # print(f"可视化图像已保存至: outputs/images/") # Removed image message

    print(f"\n分析报告已保存至: {report_file_path}")
    # print(f"可视化图像已保存至: outputs/images/") # Removed image message 