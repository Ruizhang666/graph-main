# -*- coding: utf-8 -*-
import pandas as pd
import networkx as nx
import json

# 辅助函数，用于递归解析children字段并添加节点和边
def _parse_children_recursive(main_row_entity_id, children_data, graph):
    if isinstance(children_data, str):
        try:
            # 替换策略：
            # 1. 将 CSV 中的 \' (代表实际的单引号) 替换为特殊占位符
            # 2. 将结构性的 ' 替换为 "
            # 3. 将占位符替换回 JSON 字符串中合法的 '
            processed_str = children_data.replace("\\'", "__TEMP_SINGLE_QUOTE__") 
            processed_str = processed_str.replace("'", '"')
            processed_str = processed_str.replace("__TEMP_SINGLE_QUOTE__", "'") 
            children_list = json.loads(processed_str)
        except json.JSONDecodeError as e_json_primary:
            try:
                # 备用：简单替换，如果上面的方法因为复杂引号失败
                children_list = json.loads(children_data.replace("'", '"'))
            except json.JSONDecodeError as e_json_fallback:
                print(f"GraphBuilder Warn: Could not parse children JSON string '{children_data}' for main entity '{main_row_entity_id}'. Primary error: {e_json_primary}. Fallback error: {e_json_fallback}")
                return
        except Exception as e_general:
            print(f"GraphBuilder Warn: Unknown error parsing children string '{children_data}' for main entity '{main_row_entity_id}'. Error: {e_general}")
            return
    elif isinstance(children_data, list):
        children_list = children_data
    else:
        print(f"GraphBuilder Warn: Children data is not a string or list for main entity '{main_row_entity_id}'. Type: {type(children_data)}")
        return

    for child_info_from_json in children_list:
        shareholder_name = child_info_from_json.get('name')
        shareholder_eid = child_info_from_json.get('eid')
        
        if not pd.notna(shareholder_name) or shareholder_name == '':
            # print(f"GraphBuilder Info: Skipping child with no name from children list of {main_row_entity_id}.")
            continue

        shareholder_node_id = shareholder_eid if pd.notna(shareholder_eid) and shareholder_eid != '' else shareholder_name
        
        # 添加或更新股东节点属性
        node_attrs = {
            'name': shareholder_name,
            'type': child_info_from_json.get('type', ''),
            'short_name': child_info_from_json.get('short_name', ''),
            'level': child_info_from_json.get('level', '') # level is from child_info_from_json
        }
        if not graph.has_node(shareholder_node_id):
            graph.add_node(shareholder_node_id, **node_attrs)
        else:
            # 如果节点已存在，用children中的信息补充或更新（如果更详细）
            for attr, value in node_attrs.items():
                 if value or not graph.nodes[shareholder_node_id].get(attr): # 更新空值或使用新值
                    graph.nodes[shareholder_node_id][attr] = value

        # 添加从股东 (shareholder_node_id from JSON) 到被投资公司 (main_row_entity_id) 的边
        edge_attrs = {
            'amount': child_info_from_json.get('amount', ''),
            'percent': child_info_from_json.get('percent', ''),
            'sh_type': child_info_from_json.get('sh_type', ''),
            'source_info': 'children_field' # Mark that this edge came from children field
        }
        # 只有当边 (Shareholder -> Company) 不存在时才从children添加
        if not graph.has_edge(shareholder_node_id, main_row_entity_id):
            graph.add_edge(shareholder_node_id, main_row_entity_id, **edge_attrs)

        # 递归处理孙子节点 (即当前股东的股东)
        # main_row_entity_id for the recursive call will be the current shareholder_node_id
        # grand_children_data will be the 'children' field of the current shareholder_node_id (if any)
        grand_children_data = child_info_from_json.get('children')
        if grand_children_data:
            _parse_children_recursive(shareholder_node_id, grand_children_data, graph)

def build_graph(csv_path='三层股权穿透输出数据.csv'):
    """
    从指定的CSV文件读取股权数据并构建一个NetworkX DiGraph。
    """
    try:
        df = pd.read_csv(csv_path, encoding='gbk')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding='gb18030')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_path, encoding='gb2312')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(csv_path, encoding='big5')
                except UnicodeDecodeError:
                    print(f"GraphBuilder Error: Could not decode CSV file '{csv_path}' with common Chinese encodings.")
                    raise # 重新抛出异常，让调用者处理
    
    G = nx.DiGraph()

    # 第一遍：添加所有在主行中定义了name的节点，并建立基于parent_id的边
    # Rule: Child (current_node_id) -> Parent (parent_id_val)
    for _, row in df.iterrows():
        if pd.notna(row['name']):
            current_node_id = row['eid'] if pd.notna(row['eid']) and row['eid'] != '' else row['name']
            
            node_attrs = {
                'name': row['name'],
                'type': row['type'] if pd.notna(row['type']) else '',
                'short_name': row['short_name'] if pd.notna(row['short_name']) else '',
                'level': row['level'] if pd.notna(row['level']) else '' # level is from the main row
            }
            if not G.has_node(current_node_id):
                G.add_node(current_node_id, **node_attrs)
            else: 
                for attr, value in node_attrs.items():
                    G.nodes[current_node_id][attr] = value 

            parent_id_val = row.get('parent_id')
            if pd.notna(parent_id_val) and parent_id_val != '':
                # 如果父节点不存在，暂时不创建，期望它有自己的主行数据
                # if not G.has_node(parent_id_val):
                # G.add_node(parent_id_val, name=f"Deferred Parent ({parent_id_val})") # 占位符
                edge_attrs = {
                    'amount': row['amount'] if pd.notna(row['amount']) else '',
                    'percent': row['percent'] if pd.notna(row['percent']) else '',
                    'sh_type': row['sh_type'] if pd.notna(row['sh_type']) else '',
                    'source_info': 'parent_id_field' # Mark that this edge came from parent_id
                }
                # If parent_id_val node doesn't exist, it will be created by add_edge
                # Or, we can pre-add it if we want to control its attributes more finely if it's only mentioned as a parent_id
                if not G.has_node(parent_id_val):
                     # Add a basic node for parent_id if it doesn't exist yet
                     # Its full attributes might be defined if/when it appears as a main row itself
                     G.add_node(parent_id_val, name=str(parent_id_val)) # Simplified name for now
                # MODIFIED EDGE DIRECTION HERE: current_node_id (Child) -> parent_id_val (Parent)
                if not G.has_edge(current_node_id, parent_id_val):
                    G.add_edge(current_node_id, parent_id_val, **edge_attrs)
    
    # 第二遍：处理children字段，补充可能的节点和边
    # shareholder_in_children_json -> current_node_id
    for _, row in df.iterrows():
        if pd.notna(row['name']):
            current_node_id = row['eid'] if pd.notna(row['eid']) and row['eid'] != '' else row['name']
            children_json_str = row.get('children')
            if pd.notna(children_json_str) and children_json_str not in [[], '[]', '']:
                # 确保父节点（current_node_id）在图中，如果它只有children而没有parent_id，第一遍可能没覆盖到
                if not G.has_node(current_node_id):
                     G.add_node(current_node_id, name=row['name'], type=row.get('type', ''), short_name=row.get('short_name', ''), level=row.get('level', ''))
                _parse_children_recursive(current_node_id, children_json_str, G)
                
    print(f"GraphBuilder: Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

if __name__ == '__main__':
    # 测试函数
    print("Testing graph builder...")
    graph = build_graph()
    # print("Graph nodes:")
    # for node, data in list(graph.nodes(data=True))[:5]:
    # print(f"  {node}: {data}")
    # print("Graph edges:")
    # for u, v, data in list(graph.edges(data=True))[:5]:
    # print(f"  {u} -> {v}: {data}")
    print(f"Test graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.") 