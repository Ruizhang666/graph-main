# -*- coding: utf-8 -*-
import pandas as pd
import networkx as nx
import json
import ast

# 新增辅助函数：规范化百分比数据
def _normalize_percent(value):
    """
    将各种格式的百分比值规范化为0.0到1.0之间的小数。
    如果无法解析，则返回 None。
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if 0 <= value <= 1: # 假设已经是0-1之间的小数
            return float(value)
        elif 1 < value <= 100: # 假设是1-100之间的百分比数字
             return float(value) / 100.0
        else: # 其他范围的数字，可能代表错误或特殊含义，暂定为None
            # print(f"GraphBuilder Warn: Numeric percent value {value} is out of expected range (0-1 or 1-100), treating as None.")
            return None 
    
    if isinstance(value, str):
        original_value_str = value # 保存原始字符串用于可能的警告
        value = value.strip()
        if not value: # 空字符串
            return None
        
        has_percent_symbol = value.endswith('%')
        if has_percent_symbol:
            value = value[:-1].strip() # 去掉百分号

        try:
            num_val = float(value)
            if has_percent_symbol: # 如果原始有百分号，直接除以100
                return num_val / 100.0
            else: # 如果原始没有百分号
                if 0 <= num_val <= 1: # 已经是0-1的小数
                    return num_val
                elif 1 < num_val <= 100: # 是1-100的数字，当作百分比
                    return num_val / 100.0
                else: # 其他范围，视为无效
                    # print(f"GraphBuilder Warn: String percent value '{original_value_str}' (parsed as {num_val}) is out of expected range, treating as None.")
                    return None
        except ValueError:
            # print(f"GraphBuilder Warn: Could not convert percent string '{original_value_str}' to float, treating as None.")
            return None # 无法转换为浮点数
    
    # print(f"GraphBuilder Warn: Unhandled percent value type: {value} (type: {type(value)}), treating as None.")
    return None # 其他未处理的类型

# 辅助函数，用于递归解析children字段并添加节点和边
def _parse_children_recursive(main_row_entity_id, children_data, graph):
    if isinstance(children_data, str):
        try:
            # 首先尝试使用 ast.literal_eval，它可以更安全地处理包含单引号的 Python 字面量
            children_list = ast.literal_eval(children_data)
            if not isinstance(children_list, list): # 确保结果是列表
                # 如果解析结果不是列表（例如，如果字符串只是一个字典），将其包装在列表中
                # 或者根据您的数据结构决定如何处理这种情况。这里假设我们总是期望一个子节点列表。
                print(f"GraphBuilder Warn: ast.literal_eval on children_data for {main_row_entity_id} did not return a list. Data: {children_data[:100]}") # Log a snippet
                # 根据实际情况，你可能需要将其视为错误并返回，或尝试其他解析。
                # 为了与后续逻辑兼容，如果不是list，尝试将其包装成list或者进行json解析的回退
                raise ValueError("ast.literal_eval did not result in a list.")
        except (ValueError, SyntaxError) as e_ast: # ast.literal_eval 失败
            # print(f"GraphBuilder Info: ast.literal_eval failed for '{children_data[:100]}...' for main entity '{main_row_entity_id}'. Error: {e_ast}. Falling back to JSON parsing.")
            try:
                # 替换策略：
                # 1. 将 CSV 中的 \\' (代表实际的单引号) 替换为特殊占位符
                # 2. 将结构性的 ' 替换为 "
                # 3. 将占位符替换回 JSON 字符串中合法的 '
                processed_str = children_data.replace("\\\\\'", "__TEMP_SINGLE_QUOTE__") 
                processed_str = processed_str.replace("'", '"')
                processed_str = processed_str.replace("__TEMP_SINGLE_QUOTE__", "'") 
                children_list = json.loads(processed_str)
            except json.JSONDecodeError as e_json_primary:
                try:
                    # 备用：简单替换，如果上面的方法因为复杂引号失败
                    children_list = json.loads(children_data.replace("'", '"'))
                except json.JSONDecodeError as e_json_fallback:
                    print(f"GraphBuilder Warn: Could not parse children JSON string '{children_data}' for main entity '{main_row_entity_id}'. AST error: {e_ast}, Primary JSON error: {e_json_primary}. Fallback JSON error: {e_json_fallback}")
                    return
            except Exception as e_general:
                print(f"GraphBuilder Warn: Unknown error parsing children string '{children_data}' for main entity '{main_row_entity_id}' after AST eval. Error: {e_general}")
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
            'percent': _normalize_percent(child_info_from_json.get('percent')), # 使用规范化函数
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
    encodings_to_try = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'gb2312', 'big5']
    df = None
    read_successful = False

    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(csv_path, encoding=encoding, dtype=str) # 读取所有列为字符串以保留原始格式
            # print(f"GraphBuilder: Successfully read CSV '{csv_path}' with encoding: {encoding}") # Commented out
            read_successful = True
            break
        except UnicodeDecodeError:
            # print(f"GraphBuilder: Failed to decode CSV '{csv_path}' with encoding: {encoding}") # Commented out
            pass # Continue to the next encoding
        except pd.errors.EmptyDataError:
            print(f"GraphBuilder Warn: CSV file '{csv_path}' is empty or could not be read with encoding {encoding}.")
            # 如果文件就是空的，不应该继续尝试其他编码或报错，而是返回空图或相应处理
            G = nx.DiGraph()
            print(f"GraphBuilder: Returning empty graph due to empty or unreadable CSV: {csv_path}")
            return G
        except Exception as e:
            print(f"GraphBuilder: An unexpected error occurred while reading '{csv_path}' with {encoding}: {e}")
            # 对于其他pandas读取错误或一般错误，也记录并尝试下一种编码
    
    if not read_successful or df is None:
        print(f"GraphBuilder Error: Could not read CSV file '{csv_path}' with any of the attempted encodings.")
        # 可以选择抛出异常或者返回一个空图，这里选择后者以便调用方可以处理
        G = nx.DiGraph()
        print(f"GraphBuilder: Returning empty graph as CSV could not be loaded: {csv_path}")
        return G
    
    # Check if DataFrame is empty after successful read (e.g. header only or all rows filtered out previously)
    if df.empty:
        print(f"GraphBuilder Warn: CSV file '{csv_path}' was read successfully but resulted in an empty DataFrame.")
        G = nx.DiGraph()
        print(f"GraphBuilder: Returning empty graph due to empty DataFrame from: {csv_path}")
        return G

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
                edge_attrs = {
                    'amount': row['amount'] if pd.notna(row['amount']) else '',
                    'percent': _normalize_percent(row.get('percent')), # 使用规范化函数
                    'sh_type': row['sh_type'] if pd.notna(row['sh_type']) else '',
                    'source_info': 'parent_id_field' # Mark that this edge came from parent_id
                }
                # If parent_id_val node doesn't exist, it will be created by add_edge
                if not G.has_node(parent_id_val):
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
    graph = build_graph("三层股权穿透输出数据_1.csv")
    # print("Graph nodes:")
    # for node, data in list(graph.nodes(data=True))[:5]:
    # print(f"  {node}: {data}")
    # print("Graph edges:")
    # for u, v, data in list(graph.edges(data=True))[:5]:
    #     if 'percent' in data:
    #         print(f"  {u} -> {v}: percent={data['percent']} (type: {type(data['percent'])})")
    #     else:
    #         print(f"  {u} -> {v}: {data}")
    print(f"Test graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.") 