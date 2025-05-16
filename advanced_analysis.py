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
    write_and_print(report_file, "\n\n最终控制人分析:")
    write_and_print(report_file, "="*50)

    # 寻找没有入边的节点（树的根，最终控制人）
    ultimate_controllers = [node for node, in_degree in G.in_degree() if in_degree == 0]

    write_and_print(report_file, f"发现 {len(ultimate_controllers)} 个潜在的最终控制人")

    # 分析每个最终控制人控制的实体
    for i, controller in enumerate(ultimate_controllers[:5]):  # 只显示前5个
        write_and_print(report_file, f"\n最终控制人 {i+1}: {G.nodes[controller]['name']}")
        
        # 计算这个控制人的影响力 - 从这个节点可到达的所有节点
        reachable = nx.descendants(G, controller)
        write_and_print(report_file, f"  控制的实体数量: {len(reachable)}")
        
        # 显示部分被控制实体
        if reachable:
            write_and_print(report_file, "  控制的部分实体:")
            for j, node in enumerate(list(reachable)[:3]):
                write_and_print(report_file, f"    - {G.nodes[node]['name']}")
            if len(reachable) > 3:
                write_and_print(report_file, f"    - ... 以及其他 {len(reachable) - 3} 个实体")

    # 保存最终控制人的控制网络图
    if ultimate_controllers:
        plt.figure(figsize=(20, 15))
        
        # 为不同的最终控制人设置不同的颜色
        controller_colors = sns.color_palette("Set1", len(ultimate_controllers))
        color_map = {}
        
        # 为每个控制人及其控制的节点分配颜色
        for i, controller in enumerate(ultimate_controllers):
            color_map[controller] = controller_colors[i]
            # 为该控制人控制的所有实体分配相同的颜色
            for node in nx.descendants(G, controller):
                color_map[node] = controller_colors[i]
        
        # 对于不属于任何控制网络的节点，使用灰色
        node_colors = [color_map.get(node, 'lightgray') for node in G.nodes()]
        
        # 使用按层次布局，更好地表示控制关系
        pos = nx.spring_layout(G, k=0.15, iterations=50)
        
        # 绘制节点
        nx.draw_networkx_nodes(G, pos, node_size=300, node_color=node_colors, alpha=0.8)
        
        # 绘制边
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrows=True, arrowsize=15)
        
        # 添加节点标签
        labels = {node: G.nodes[node]['name'] for node in G.nodes()}
        
        # 绘制节点标签
        font_kwargs = {}
        if font is not None:
            font_kwargs['font_family'] = font.get_name()
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, **font_kwargs)
        
        # 设置标题
        plt.title('最终控制人及其控制网络', fontsize=20)
        if font is not None:
            plt.title('最终控制人及其控制网络', fontproperties=font, fontsize=20)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('outputs/images/最终控制人网络图.png', dpi=300, bbox_inches='tight')
        write_and_print(report_file, f"\n最终控制人网络图已保存至: outputs/images/最终控制人网络图.png")

    # 6. 链路合理性检查 (Sanity Checks for Links)
    write_and_print(report_file, "\n\n链路合理性检查:")
    write_and_print(report_file, "="*50)

    # 检查 6.1: 自循环
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

    # 检查 6.2: 父节点（投资方）缺少名称信息
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

    # 检查 6.3: 边属性 'percent' (持股比例) 的合理性
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