import sys
import networkx as nx
from graph_builder import build_graph

# 画像指标计算

def get_investor_profile(G, node_id, pr_centrality, deg_centrality, out_deg, in_deg):
    node = G.nodes[node_id]
    name = node.get('name', node_id)
    typ = node.get('type', '未知类型')
    pr = pr_centrality.get(node_id, 0.0)
    deg = deg_centrality.get(node_id, 0.0)
    outd = out_deg.get(node_id, 0)
    ind = in_deg.get(node_id, 0)
    return f"{name} (类型: {typ}, PageRank: {pr:.4f}, 度: {deg:.4f}, 出度: {outd}, 入度: {ind})"

def global_common_investor_analysis(G):
    print("\n全局共同投资方分析 (哪些公司有多个股东共同投资):\n" + "="*50)
    pr_centrality = nx.pagerank(G, alpha=0.85)
    deg_centrality = nx.degree_centrality(G)
    out_deg = dict(G.out_degree())
    in_deg = dict(G.in_degree())
    sorted_nodes_by_in_degree = sorted(G.nodes(), key=lambda n: G.in_degree(n), reverse=True)
    companies_reported = 0
    max_companies = 15
    max_shareholders = 10
    for node_id in sorted_nodes_by_in_degree:
        if companies_reported >= max_companies:
            print(f"\n  (已显示前 {max_companies} 个存在共同投资情况的公司，更多请用脚本筛查)")
            break
        if G.in_degree(node_id) > 1:
            shareholders_details = []
            for shareholder_id in G.predecessors(node_id):
                if shareholder_id not in G.nodes:
                    continue
                sh_node_data = G.nodes[shareholder_id]
                sh_name = sh_node_data.get('name', shareholder_id)
                sh_type = sh_node_data.get('type', '未知类型')
                edge_data = G.get_edge_data(shareholder_id, node_id)
                percent_on_edge = edge_data.get('percent', None) if edge_data else None
                percent_str = f"{percent_on_edge*100:.2f}%" if percent_on_edge is not None else "未知%"
                pr = pr_centrality.get(shareholder_id, 0.0)
                deg = deg_centrality.get(shareholder_id, 0.0)
                outd = out_deg.get(shareholder_id, 0)
                ind = in_deg.get(shareholder_id, 0)
                shareholders_details.append(f"{sh_name} (类型: {sh_type}, 持股: {percent_str}, PageRank: {pr:.4f}, 度: {deg:.4f}, 出度: {outd}, 入度: {ind})")
            if len(shareholders_details) > 1:
                company_name = G.nodes[node_id].get('name', node_id)
                print(f"\n公司: {company_name} (总入股方数: {G.in_degree(node_id)})")
                print(f"  共同投资方 ({len(shareholders_details)}):")
                for sh_detail in shareholders_details[:max_shareholders]:
                    print(f"    - {sh_detail}")
                if len(shareholders_details) > max_shareholders:
                    print(f"    - ...以及其他 {len(shareholders_details) - max_shareholders} 个投资方。")
                companies_reported += 1
    if companies_reported == 0:
        print("未发现多股东共同投资于同一公司的情况。")

if __name__ == '__main__':
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == '--global'):
        G = build_graph()
        global_common_investor_analysis(G)
        sys.exit(0)
    target_name = sys.argv[1]
    G = build_graph()
    # 查找目标公司ID
    target_id = None
    for node_id, data in G.nodes(data=True):
        if data.get('name') == target_name:
            target_id = node_id
            break
    if not target_id:
        print(f"未找到公司: {target_name}")
        sys.exit(1)
    print(f"公司: {target_name}")
    # 预先计算画像指标
    pr_centrality = nx.pagerank(G, alpha=0.85)
    deg_centrality = nx.degree_centrality(G)
    out_deg = dict(G.out_degree())
    in_deg = dict(G.in_degree())
    # 上游（投资方）
    investors = list(G.predecessors(target_id))
    if investors:
        print("\n上游投资方:")
        for inv in investors:
            edge_data = G.get_edge_data(inv, target_id)
            percent = edge_data.get('percent', None) if edge_data else None
            percent_str = f"{percent*100:.2f}%" if percent is not None else "未知%"
            profile = get_investor_profile(G, inv, pr_centrality, deg_centrality, out_deg, in_deg)
            print(f"- {profile}, 持股比例: {percent_str}")
    else:
        print("\n无直接投资方。")
    # 下游（被投资企业）
    investees = list(G.successors(target_id))
    if investees:
        print("\n下游被投资企业:")
        for sub in investees:
            sub_name = G.nodes[sub].get('name', sub)
            edge_data = G.get_edge_data(target_id, sub)
            percent = edge_data.get('percent', None) if edge_data else None
            percent_str = f"{percent*100:.2f}%" if percent is not None else "未知%"
            print(f"- {sub_name}，持股比例: {percent_str}")
    else:
        print("\n无直接被投资企业。") 