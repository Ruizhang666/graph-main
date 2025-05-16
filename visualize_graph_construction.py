# -*- coding: utf-8 -*-
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
from font_config import get_font_properties # For labels

# 确保输出目录存在
os.makedirs('outputs/reports', exist_ok=True)
os.makedirs('outputs/images', exist_ok=True)
os.makedirs('outputs/temp', exist_ok=True)

def visualize_step_by_step_construction(csv_path='三层股权穿透输出数据.csv', rows_to_visualize=20, pause_duration=0.5, save_final=True):
    """
    逐行读取CSV数据，并使用matplotlib动态可视化NetworkX图的构建过程。
    主要展示基于主行数据和parent_id的节点与边添加。
    """
    font = get_font_properties()
    plt.ion()  # Enable interactive mode
    fig, ax = plt.subplots(figsize=(16, 12)) # Adjusted figure size

    G = nx.DiGraph()
    
    # 尝试多种编码读取CSV
    encodings_to_try = ['gbk', 'gb18030', 'gb2312', 'utf-8', 'big5']
    df = None
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            print(f"成功使用编码 '{encoding}' 读取CSV文件: {csv_path}")
            break
        except UnicodeDecodeError:
            print(f"尝试使用编码 '{encoding}' 读取失败...")
        except FileNotFoundError:
            print(f"错误: CSV文件未找到于路径 '{csv_path}'")
            plt.ioff()
            return
        except Exception as e:
            print(f"读取CSV时发生未知错误 (编码: {encoding}): {e}")
            # Continue to try other encodings unless it's a FileNotFoundError

    if df is None:
        print(f"错误: 无法使用尝试过的所有编码读取CSV文件 '{csv_path}'。请检查文件路径和编码。")
        plt.ioff()
        return

    processed_rows_count = 0
    for index, row in df.iterrows():
        if rows_to_visualize > 0 and processed_rows_count >= rows_to_visualize:
            print(f"已达到可视化行数上限: {rows_to_visualize} 行。")
            break
        
        print(f"\n处理第 {index + 1} 行数据:")

        node_added_this_step = False
        edge_added_this_step = False
        current_node_name_for_title = "未知节点"

        if pd.notna(row['name']):
            current_node_id = row['eid'] if pd.notna(row['eid']) and str(row['eid']).strip() != '' else row['name']
            current_node_name = str(row['name'])
            current_node_name_for_title = current_node_name

            node_attrs = {
                'name': current_node_name,
                'type': str(row.get('type', '')),
                'short_name': str(row.get('short_name', '')),
                'level': str(row.get('level', ''))
            }

            if not G.has_node(current_node_id):
                G.add_node(current_node_id, **node_attrs)
                print(f"  添加节点: '{current_node_name}' (ID: {current_node_id})")
                node_added_this_step = True
            else:
                # 如果节点已存在，更新其属性
                G.nodes[current_node_id].update(node_attrs)
                print(f"  更新节点: '{current_node_name}' (ID: {current_node_id})")

            parent_id_val = row.get('parent_id')
            if pd.notna(parent_id_val) and str(parent_id_val).strip() != '':
                parent_node_id = str(parent_id_val)
                
                # 如果父节点不存在，为可视化目的先添加一个引用
                if not G.has_node(parent_node_id):
                    # 尝试从DataFrame中查找父节点的名字（如果它在之前的行定义过）
                    parent_df_rows = df[df['eid'] == parent_node_id]
                    parent_name_ref = parent_node_id # 默认为ID
                    if not parent_df_rows.empty:
                        parent_name_ref = parent_df_rows.iloc[0].get('name', parent_node_id)
                    
                    G.add_node(parent_node_id, name=f"REF: {str(parent_name_ref)[:20]}...") # 添加占位父节点
                    print(f"  为边连接添加了引用的父节点: '{parent_name_ref}' (ID: {parent_node_id})")

                parent_name_display = G.nodes[parent_node_id].get('name', parent_node_id)

                if not G.has_edge(parent_node_id, current_node_id):
                    edge_attrs = {
                        'amount': str(row.get('amount', '')),
                        'percent': str(row.get('percent', '')),
                        'sh_type': str(row.get('sh_type', ''))
                    }
                    G.add_edge(parent_node_id, current_node_id, **edge_attrs)
                    print(f"  添加边: '{parent_name_display}' -> '{current_node_name}' (持股: {edge_attrs.get('percent', '未知')})")
                    edge_added_this_step = True
                else:
                    # 更新边的属性
                    G.edges[parent_node_id, current_node_id].update({
                        'amount': str(row.get('amount', '')),
                        'percent': str(row.get('percent', '')),
                        'sh_type': str(row.get('sh_type', ''))
                    })
                    print(f"  更新边: '{parent_name_display}' -> '{current_node_name}' (持股: {row.get('percent', '未知')})")


            # 仅在有节点或边变动时，或者作为第一步时更新可视化
            if node_added_this_step or edge_added_this_step or processed_rows_count == 0:
                ax.clear()
                if G.number_of_nodes() > 0:
                    try:
                        pos = nx.spring_layout(G, k=0.3, iterations=20, seed=42) # 调整参数以加快布局
                    except Exception as e_layout:
                        print(f"    布局警告: {e_layout}, 使用随机布局")
                        pos = nx.random_layout(G, seed=42)
                    
                    # 节点颜色逻辑
                    node_colors_list = []
                    for node_id in G.nodes():
                        node_type = G.nodes[node_id].get('type', '')
                        if node_type == 'P': node_colors_list.append('skyblue')
                        elif node_type == 'E': node_colors_list.append('lightgreen')
                        else: node_colors_list.append('lightgrey')
                    
                    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=400, node_color=node_colors_list, alpha=0.8)
                    
                    # 边绘制
                    nx.draw_networkx_edges(G, pos, ax=ax, width=1.0, alpha=0.6, arrows=True, arrowstyle='-|>', arrowsize=12)
                    
                    # 节点标签 (缩短)
                    labels = {nid: str(G.nodes[nid].get('name', nid))[:15] for nid in G.nodes()}
                    nx.draw_networkx_labels(G, pos, ax=ax, labels=labels, font_size=7, font_family=font.get_name() if font else None)
                    
                    # 边标签 (持股比例, 缩短)
                    edge_labels_viz = {}
                    for u, v, data_viz in G.edges(data=True):
                        percent_val = data_viz.get('percent', '')
                        if percent_val:
                             edge_labels_viz[(u,v)] = str(percent_val)[:5] # 显示前5个字符
                    nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels_viz, font_size=6, font_family=font.get_name() if font else None)

                ax.set_title(f"图状态: 处理完第 {index + 1} 行 (当前节点: {current_node_name_for_title})", fontproperties=font, fontsize=10)
                plt.draw()
                plt.pause(pause_duration if pause_duration > 0 else 0.01) # 确保即使pause_duration为0也有一个极小的暂停以刷新
        else:
            print(f"  跳过第 {index + 1} 行: 缺少'name'字段")
        
        processed_rows_count += 1

    plt.ioff() # 关闭交互模式
    ax.set_title(f"最终图状态 ({processed_rows_count} 行数据已处理)", fontproperties=font, fontsize=12)
    
    # 保存最终图状态
    if save_final:
        final_image_path = 'outputs/images/graph_construction_final.png'
        plt.savefig(final_image_path, dpi=300, bbox_inches='tight')
        print(f"\n最终图状态已保存至: {final_image_path}")
        
        # 保存图构建过程的基本统计信息到文本文件
        stats_report_path = 'outputs/reports/graph_construction_stats.txt'
        with open(stats_report_path, 'w', encoding='utf-8') as f:
            f.write(f"图构建统计报告\n{'='*40}\n\n")
            f.write(f"处理的行数: {processed_rows_count}/{len(df) if df is not None else '未知'}\n")
            f.write(f"节点总数: {G.number_of_nodes()}\n")
            f.write(f"边总数: {G.number_of_edges()}\n\n")
            
            f.write("节点类型分布:\n")
            node_type_count = {'P': 0, 'E': 0, '其他': 0}
            for node_id in G.nodes():
                node_type = G.nodes[node_id].get('type', '')
                if node_type == 'P': node_type_count['P'] += 1
                elif node_type == 'E': node_type_count['E'] += 1
                else: node_type_count['其他'] += 1
            for type_name, count in node_type_count.items():
                f.write(f"  - {type_name}: {count}\n")
            
            f.write("\n图构建过程完成。\n")
        print(f"图构建统计信息已保存至: {stats_report_path}")
    
    if not (rows_to_visualize > 0 and processed_rows_count >= rows_to_visualize): # 如果不是因为行数限制而停止
        plt.show() # 保持最后一个窗口打开，除非是被行数限制中断
    else: # 如果是行数限制中断，也显示一下最终状态
        print("\n可视化因达到行数限制而结束。显示当前图状态...")
        plt.show(block=True) # block=True here to keep window until closed

    print("逐步可视化构建过程结束。")
    return G

if __name__ == '__main__':
    print("开始执行逐行图构建可视化脚本...")
    print("注意: 对于大型CSV文件，此过程可能非常缓慢。")
    print("您可以修改脚本中的 'rows_to_visualize' 参数以限制处理的行数。")
    
    # 默认可视化少量行作为演示
    # 要可视化所有行, 设置 rows_to_visualize=0 或一个负数
    # 例如: visualize_step_by_step_construction(csv_path='三层股权穿透输出数据.csv', rows_to_visualize=0, pause_duration=0.1)
    
    visualize_step_by_step_construction(
        csv_path='三层股权穿透输出数据.csv', 
        rows_to_visualize=100,  # 默认可视化100行
        pause_duration=0.7,     # 每步暂停0.7秒
        save_final=True         # 保存最终图状态到输出文件夹
    ) 