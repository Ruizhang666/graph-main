import networkx as nx
import graph_builder # 假设 graph_builder.py 在同一个目录下或者在PYTHONPATH中
import os

# 定义默认的图文件路径
DEFAULT_GRAPH_FILE = "outputs/graph_model_updated.graphml"

def save_graph(graph, file_path):
    """
    将NetworkX图保存到指定的文件路径。

    参数:
    graph (nx.DiGraph): 需要保存的NetworkX有向图。
    file_path (str): 保存图的文件路径 (推荐使用 .graphml 格式)。
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        # 创建图的副本以进行修改，避免更改原始图对象
        graph_copy = graph.copy()

        # 预处理节点属性：将 None 替换为空字符串
        for node, data in graph_copy.nodes(data=True):
            for key, value in data.items():
                if value is None:
                    data[key] = ""
        
        # 预处理边属性：将 None 替换为空字符串
        for u, v, data in graph_copy.edges(data=True):
            for key, value in data.items():
                if value is None:
                    data[key] = ""

        nx.write_graphml(graph_copy, file_path)
        print(f"Graph successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving graph to {file_path}: {e}")

def load_graph(file_path):
    """
    从指定的文件路径加载NetworkX图。

    参数:
    file_path (str): 图文件的路径 (应该是 .graphml 格式)。

    返回:
    nx.DiGraph: 加载的NetworkX有向图，如果加载失败则返回None。
    """
    try:
        graph = nx.read_graphml(file_path)
        print(f"Graph successfully loaded from {file_path}")
        # GraphML会把所有节点属性都读成字符串，需要根据情况转换类型，尤其是数值类型
        # 例如，如果'level'应该是整数，'amount'和'percent'应该是浮点数
        for node_id, data in graph.nodes(data=True):
            if 'level' in data and data['level'] is not None:
                try:
                    data['level'] = int(data['level'])
                except ValueError:
                    # print(f"Warning: Could not convert level '{data['level']}' to int for node {node_id}")
                    pass # 保留原样或设为None/默认值
            # 可以为其他属性添加类似的转换逻辑
        
        for u, v, data in graph.edges(data=True):
            if 'amount' in data and data['amount'] is not None:
                try:
                    data['amount'] = float(data['amount'])
                except ValueError:
                    pass
            if 'percent' in data and data['percent'] is not None:
                try:
                    data['percent'] = float(data['percent'])
                except ValueError:
                    pass
        return graph
    except FileNotFoundError:
        print(f"Error: Graph file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error loading graph from {file_path}: {e}")
        return None

if __name__ == '__main__':
    # --- 示例用法 ---

    # 1. 构建图 (使用 graph_builder.py)
    print("Attempting to build the graph...")
    original_graph = graph_builder.build_graph(csv_path='三层股权穿透输出数据_1.csv')

    if original_graph:
        print(f"Graph built: {original_graph.number_of_nodes()} nodes, {original_graph.number_of_edges()} edges.")

        # 2. 保存图
        graph_file_to_save = DEFAULT_GRAPH_FILE
        print(f"\nSaving graph to {graph_file_to_save}...")
        save_graph(original_graph, graph_file_to_save)

        # 3. 加载图
        print(f"\nLoading graph from {graph_file_to_save}...")
        loaded_graph = load_graph(graph_file_to_save)

        if loaded_graph:
            print(f"Graph loaded: {loaded_graph.number_of_nodes()} nodes, {loaded_graph.number_of_edges()} edges.")
            
            # 后续可以在这里对 loaded_graph 进行操作，例如添加新的边
            # print("\nGraph is ready for further modifications.")

        else:
            print("Failed to load the graph.")
    else:
        print("Failed to build the initial graph.")

    print("\nScript finished.") 