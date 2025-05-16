# -*- coding: utf-8 -*-
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from graph_builder import build_graph
from font_config import get_font_properties
import os # For path operations

# 确保输出目录存在
os.makedirs('outputs/reports', exist_ok=True)
os.makedirs('outputs/images', exist_ok=True)
os.makedirs('outputs/temp', exist_ok=True)

def find_node_by_name(graph, name_query):
    """在图中根据'name'属性查找节点ID。"""
    for node_id, data in graph.nodes(data=True):
        if data.get('name') == name_query:
            return node_id
    # Consider partial match if exact match fails
    partial_matches = []
    for node_id, data in graph.nodes(data=True):
        if name_query.lower() in data.get('name', '').lower():
            partial_matches.append((data.get('name'), node_id))
    if partial_matches:
        if len(partial_matches) == 1:
            print(f"提示: 未找到精确匹配，但找到一个部分匹配: '{partial_matches[0][0]}' (ID: {partial_matches[0][1]}) 将使用此节点。")
            return partial_matches[0][1]
        else:
            print(f"提示: 未找到精确匹配，但找到多个部分匹配。请使用更精确的名称:")
            for name, nid in partial_matches[:5]: # Show first 5 partial matches
                print(f"  - '{name}' (ID: {nid})")
            return None
    return None

def write_and_print(file_handle, message, to_console=True):
    """同时写入文件和打印到控制台。"""
    if file_handle:
        file_handle.write(message + "\n")
    if to_console:
        print(message)

def query_and_visualize(target_node_name, radius=2):
    """根据节点名称查询其N度邻域节点，打印信息到控制台和TXT文件，并可视化。"""
    print(f"正在加载股权网络图...")
    G_full = build_graph()
    font = get_font_properties()

    if G_full.number_of_nodes() == 0:
        write_and_print(None, "错误: 图为空，无法执行查询。")
        return

    print(f"正在图中查找节点: '{target_node_name}'...")
    target_node_id = find_node_by_name(G_full, target_node_name)

    if target_node_id is None:
        write_and_print(None, f"错误: 未在图中找到与 '{target_node_name}' 匹配的节点。请检查名称是否准确。")
        return
    
    # Sanitize node name for filenames
    sanitized_node_name = target_node_name.replace(' ', '_').replace('/', '_').replace('(','_').replace(')','_')
    txt_output_filename = f"outputs/reports/query_result_{sanitized_node_name}.txt"
    img_output_filename = f"outputs/images/query_result_{sanitized_node_name}.png"

    with open(txt_output_filename, 'w', encoding='utf-8') as f_out:
        write_and_print(f_out, f"查询报告: 节点 '{target_node_name}' (ID: {target_node_id}) 的 {radius}-度邻域分析")
        write_and_print(f_out, "="*50)

        # 提取N度邻居子图 (包括中心节点)
        # ego_graph includes the target_node_id itself
        write_and_print(f_out, f"\n正在提取 {radius}-度邻域子图...")
        G_sub = nx.ego_graph(G_full, target_node_id, radius=radius, undirected=False).copy()
        write_and_print(f_out, f"子图包含 {G_sub.number_of_nodes()} 个节点和 {G_sub.number_of_edges()} 条边。")

        if G_sub.number_of_nodes() == 0:
            write_and_print(f_out, "\n错误: 生成的子图为空。查询的节点可能是一个孤立节点。")
            return
        
        write_and_print(f_out, f"\n--- 子图内节点详细信息 (按节点ID排序) ---")
        sorted_sub_nodes = sorted(list(G_sub.nodes(data=True)), key=lambda x: x[0])

        for node_id, node_data in sorted_sub_nodes:
            is_target_node_marker = " (查询中心节点)" if node_id == target_node_id else ""
            write_and_print(f_out, f"\n节点: {node_data.get('name', node_id)}{is_target_node_marker}")
            write_and_print(f_out, f"  ID: {node_id}")
            for attr, value in node_data.items():
                write_and_print(f_out, f"    {attr}: {value}")
            
            # 打印该节点在子图内的入边
            write_and_print(f_out, f"    子图内入边 (指向此节点):")
            has_incoming = False
            for pred_id_sub, _, edge_data_sub in G_sub.in_edges(node_id, data=True):
                has_incoming = True
                pred_name_sub = G_sub.nodes[pred_id_sub].get('name', pred_id_sub)
                write_and_print(f_out, f"      <- 来自: {pred_name_sub} (ID: {pred_id_sub}) | 属性: {edge_data_sub}")
            if not has_incoming:
                write_and_print(f_out, "        无")

            # 打印该节点在子图内的出边
            write_and_print(f_out, f"    子图内出边 (从此节点指出):")
            has_outgoing = False
            for _, succ_id_sub, edge_data_sub in G_sub.out_edges(node_id, data=True):
                has_outgoing = True
                succ_name_sub = G_sub.nodes[succ_id_sub].get('name', succ_id_sub)
                write_and_print(f_out, f"      -> 指向: {succ_name_sub} (ID: {succ_id_sub}) | 属性: {edge_data_sub}")
            if not has_outgoing:
                write_and_print(f_out, "        无")
        write_and_print(f_out, "="*50)
        write_and_print(f_out, f"报告结束。保存在 {txt_output_filename}")

    print(f"\n详细信息已写入: {txt_output_filename}")
    print(f"\n正在生成 '{target_node_name}' 的 {radius}-度邻域可视化图...")
    plt.figure(figsize=(15, 12)) # Increased figure size slightly for potentially larger graph
    
    try:
        pos = nx.spring_layout(G_sub, k=0.4, iterations=60, seed=42) # Adjusted k for potentially larger graph
    except Exception as e_layout1:
        print(f"Spring layout failed ({e_layout1}), trying Kamada-Kawai...")
        try:
            pos = nx.kamada_kawai_layout(G_sub) 
        except Exception as e_layout2:
            print(f"Kamada-Kawai layout failed ({e_layout2}), using random layout.")
            pos = nx.random_layout(G_sub, seed=42)

    node_colors = []
    node_sizes = []
    for node_id_viz in G_sub.nodes():
        if node_id_viz == target_node_id:
            node_colors.append('red') 
            node_sizes.append(800)
        else:
            node_type = G_sub.nodes[node_id_viz].get('type', '')
            if node_type == 'P': node_colors.append('skyblue')
            elif node_type == 'E': node_colors.append('lightgreen')
            else: node_colors.append('lightcoral')
            node_sizes.append(500)

    nx.draw_networkx_nodes(G_sub, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(G_sub, pos, width=1.0, alpha=0.6, arrows=True, arrowsize=15, connectionstyle='arc3,rad=0.05')

    labels = {}
    for nid_viz in G_sub.nodes():
        name = G_sub.nodes[nid_viz].get('name', str(nid_viz))[:15] # Truncated name
        level = G_sub.nodes[nid_viz].get('level', 'N/A')
        labels[nid_viz] = f"{name}\nL{level}" # Shortened Lvl to L
    nx.draw_networkx_labels(G_sub, pos, labels=labels, font_size=7, font_family=font.get_name() if font else None, bbox=dict(facecolor='white', alpha=0.35, edgecolor='none', boxstyle='round,pad=0.1'))

    edge_labels_viz = {}
    for u, v, data_viz in G_sub.edges(data=True):
        percent = data_viz.get('percent', '')
        if percent and str(percent).strip() != '':
            edge_labels_viz[(u,v)] = f"{str(percent)[:5]}%"
    nx.draw_networkx_edge_labels(G_sub, pos, edge_labels=edge_labels_viz, font_size=6, font_family=font.get_name() if font else None)

    plt.title(f"'{target_node_name}' 的 {radius}-度邻域网络 (Child -> Parent)", fontproperties=font, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    
    try:
        plt.savefig(img_output_filename, dpi=250, bbox_inches='tight') # Added bbox_inches
        print(f"邻域图已保存为: {img_output_filename}")
    except Exception as e_save_img:
        print(f"保存邻域图失败: {e_save_img}")
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='查询股权网络中特定节点的邻域信息并可视化。')
    parser.add_argument('node_name', type=str, help='要查询的节点名称。')
    parser.add_argument('--radius', type=int, default=2, help='查询的邻域半径 (默认为2度)。')
    
    args = parser.parse_args()
    query_and_visualize(args.node_name, args.radius) 