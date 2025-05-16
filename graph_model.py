# -*- coding: utf-8 -*-
# import pandas as pd # No longer needed directly here
import networkx as nx
import matplotlib.pyplot as plt # Re-added for visualization
import os # 添加导入os模块
# import json # No longer needed directly here
# from matplotlib.font_manager import FontProperties # Removed

# 从新模块导入功能
from font_config import get_font_properties # Re-added for visualization
from graph_builder import build_graph

# 确保输出目录存在
os.makedirs('outputs/reports', exist_ok=True)
os.makedirs('outputs/images', exist_ok=True)
os.makedirs('outputs/temp', exist_ok=True)

# 1. 获取字体配置 (在构建图之前或之后都可以，这里放在前面)
font = get_font_properties()

# 2. 构建图
print("正在从 graph_builder 构建图...")
G = build_graph() # Uses graph_builder to get the graph object
print("图构建完成。")

# 移除本地的 parse_children 函数，因为它已在 graph_builder 中
# 移除本地的图构建循环 for _, row in df.iterrows(): 因为它已在 graph_builder 中

# 创建文本报告文件
report_file_path = 'outputs/reports/graph_model_report.txt'
with open(report_file_path, 'w', encoding='utf-8') as report_file:
    # 检查图是否为空
    if G.number_of_nodes() == 0:
        message = "图为空。请检查CSV文件和 graph_builder.py 的日志输出。"
        print(message)
        report_file.write(message + "\n")
    else:
        # 输出一些网络统计信息
        report_file.write("股权网络模型基础统计报告\n")
        report_file.write("=" * 40 + "\n\n")

        stats_message = f"节点总数: {G.number_of_nodes()}"
        print(stats_message)
        report_file.write(stats_message + "\n")
        
        stats_message = f"边总数: {G.number_of_edges()}"
        print(stats_message)
        report_file.write(stats_message + "\n")

        # 找出入度最高的前5个节点（被最多公司/个人持股的实体）
        if G.number_of_nodes() > 0:
            report_file.write("\n被持股最多的实体 (前5名):\n")
            print("\n被持股最多的实体 (前5名):")
            in_degrees = sorted(G.in_degree(), key=lambda x: x[1], reverse=True)
            for node, degree in in_degrees[:5]:
                node_name = G.nodes[node].get('name', str(node))
                # 检查节点是否存在于图中，以防万一
                if node not in G:
                    message = f"- 节点ID {node} (在度数计算中出现，但无法在G.nodes中找到详细信息)"
                    print(message)
                    report_file.write(message + "\n")
                    continue
                message = f"- {node_name}: 被{degree}个实体持股"
                print(message)
                report_file.write(message + "\n")

            # 找出出度最高的前5个节点（持有最多公司股份的股东）
            report_file.write("\n持股最多的股东 (前5名):\n")
            print("\n持股最多的股东 (前5名):")
            out_degrees = sorted(G.out_degree(), key=lambda x: x[1], reverse=True)
            for node, degree in out_degrees[:5]:
                node_name = G.nodes[node].get('name', str(node))
                if node not in G:
                    message = f"- 节点ID {node} (在度数计算中出现，但无法在G.nodes中找到详细信息)"
                    print(message)
                    report_file.write(message + "\n")
                    continue
                message = f"- {node_name}: 持有{degree}个实体的股份"
                print(message)
                report_file.write(message + "\n")

        report_file.write("\n" + "=" * 40 + "\n")
        report_file.write("基础统计报告结束。")

    # 3. 可视化并导出最终的图模型图片
    print("\n正在生成图模型可视化图片...")
    plt.figure(figsize=(25, 20)) # 保持较大的图像尺寸

    # 调整布局算法和参数以提高可读性
    pos = None
    print("尝试使用 spring_layout 进行布局 (k=0.35, iterations=70)...")
    try:
        pos = nx.spring_layout(G, k=0.35, iterations=70, seed=42)
        print("初步 spring_layout 成功。")
    except Exception as e_spring1:
        print(f"初步 spring_layout 失败 ({e_spring1}), 尝试 kamada_kawai_layout...")
        try:
            pos = nx.kamada_kawai_layout(G)
            print("kamada_kawai_layout 成功。")
        except Exception as e_kk:
            print(f"kamada_kawai_layout 也失败 ({e_kk}), 尝试 k 值较小的 spring_layout (k=0.15, iterations=50)...")
            try:
                pos = nx.spring_layout(G, k=0.15, iterations=50, seed=42) # 之前的回退方案
                print("备用 spring_layout 成功。")
            except Exception as e_spring2:
                print(f"备用 spring_layout 也失败 ({e_spring2}), 使用随机布局。")
                pos = nx.random_layout(G, seed=42)
    
    # 按类型为节点着色
    node_colors = []
    for node_id in G.nodes(): # Iterate over node_id directly
        node_data = G.nodes[node_id]
        node_type = node_data.get('type', '')
        if node_type == 'P':  # 个人股东
            node_colors.append('skyblue')
        elif node_type == 'E':  # 企业股东
            node_colors.append('lightgreen')
        else:  # 其他类型或未知类型
            node_colors.append('lightcoral') # Changed for better visibility

    # 画节点
    nx.draw_networkx_nodes(G, pos, node_size=350, node_color=node_colors, alpha=0.9)

    # 画边
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrows=True, arrowsize=12, connectionstyle='arc3,rad=0.05')

    # 添加节点标签（显示名称和Level）
    labels = {}
    for nid in G.nodes():
        name = G.nodes[nid].get('name', str(nid))[:20] # Truncate name
        level = G.nodes[nid].get('level', 'N/A')
        labels[nid] = f"{name}\nLvl: {level}" # Display name and level
    
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=6, font_family=font.get_name() if font else None, bbox=dict(facecolor='white', alpha=0.3, edgecolor='none', boxstyle='round,pad=0.1'))

    # 添加边标签（显示持股比例）
    edge_labels = {}
    for u, v, data in G.edges(data=True):
        percent_val = data.get('percent', '')
        if percent_val and str(percent_val).strip() != '':
            edge_labels[(u, v)] = str(percent_val)[:5] # Truncate for clarity

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=5, font_family=font.get_name() if font else None)

    # 设置标题
    title_text = '股权关系网络图 (由graph_model.py生成) - Child -> Parent'
    plt.title(title_text, fontproperties=font, fontsize=18)
        
    plt.axis('off')
    plt.tight_layout()

    # 保存图像到新的输出目录
    output_image_path = 'outputs/images/graph_model_visualization.png'
    try:
        plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"\n图模型已保存至 '{output_image_path}'")
    except Exception as e_save:
        print(f"保存图像 '{output_image_path}' 失败: {e_save}")

    # (可选) 显示图像 - 在某些环境下可能不希望自动弹出
    # plt.show() 

print(f"\n基础统计报告已保存至: {report_file_path}")
print("\ngraph_model.py 执行完毕。") 