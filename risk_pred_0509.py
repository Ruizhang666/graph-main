# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 11:05:11 2025

@author: jiangjun
"""
import os  
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import tushare as ts
from scipy.stats import rankdata    
from datetime import datetime,timedelta
from scipy import stats 
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


font_path = r'C:/Windows/Fonts/simhei.ttf'
prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = prop.get_name()
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False
file_dir=r"D:\work\数据产品2025\客商风控"

df=pd.read_excel(file_dir+"\\化工测试数据.xlsx")  
nodes=set(df['公司名称']).union(set(df['交易单位']))
edges=[(row['公司名称'], row['交易单位'], row['交易金额']) for _, row in df.iterrows()]

# 创建图谱并添加节点和边
#- networkx.Graph() ：创建无向图 - networkx.DiGraph() ：创建有向图 - networkx.MultiGraph() ：创建多重无向图 - networkx.MultiDigraph() ：创建多重有向图
G = nx.Graph()
G.add_nodes_from(nodes)
for edge in edges:
    G.add_edge(edge[0], edge[1], weight=edge[2])

print(nx.info(G))

pos = nx.spring_layout(G, k=1, iterations=1000)  # k值越大节点越分散，默认0.1  
#pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=5, node_color="skyblue", width=1, linewidths=1, font_size=5, font_color="black")
plt.show()
plt.figure(figsize=(40, 40))
nx.draw(
    G,
    pos,
    node_size=3,
    node_color="skyblue",
    edge_color="gray",
    alpha=0.2,
    width=0.1,
    with_labels=False
)

# 可视化图谱
nx.draw(G, with_labels=True, node_color='lightblue', node_size=10, edge_color='gray', width=1, linewidths=1, font_size=10, font_color='black')
plt.title("Social Network Graph")
plt.show()


# 计算节点的度数
degree_dict = dict(G.degree(G.nodes))
nx.set_node_attributes(G, degree_dict, 'degree')

max_degree_node = max(degree_dict, key=degree_dict.get)

print(f"度数最高的节点是：{max_degree_node}，度数为：{degree_dict[max_degree_node]}")

# 计算边的权重
edge_weights = nx.get_edge_attributes(G, 'weight')
max_weight_edge = max(edge_weights, key=edge_weights.get)
print(f"权重最高的边是：{max_weight_edge}，权重为：{edge_weights[max_weight_edge]}")
# 找出图谱中的连通分量
connected_components = list(nx.connected_components(G))

#找出最大的连通分量
largest_component = max(connected_components, key=len)
print(f"最大的连通分量包含的节点数为：{len(largest_component)}")
##############################################################################################################
A = np.array([[0,9,2,4,7],
              [9,0,3,4,0],
              [2,3,0,8,4],
              [4,4,8,0,6],
              [7,0,4,6,0]])
# 创建无向图
G = nx.Graph(A)
print("输出全部节点：{}".format(G.nodes()))
print("输出全部边：{}".format(G.edges()))
print("输出全部边的数量：{}".format(G.number_of_edges()))
nx.draw(G,with_labels=True)
plt.figure(figsize=(4, 2))

# np.nonzero()获取非零元素位置索引
i,j = np.nonzero(A)
# 提出A中的非零元素
w = A[i,j]
# (i,j)就是无向图的边，wi的值为边对应的权值
edges=list(zip(i,j,w))
g = nx.Graph(A)
g.add_weighted_edges_from(edges)
nx.draw(g,with_labels=True)
plt.figure(figsize=(4, 2))

# 对得到无向图的边标注权重
# 节点在同心圆上分布
pos=nx.shell_layout(G)
nx.draw(G,pos,with_labels=True)
# 从G中获取边的权值
w = nx.get_edge_attributes(G,'weight')
# 绘图
nx.draw_networkx_edge_labels(G,pos,font_size=12,edge_labels=w)
plt.show()

#  创建有向图
G=nx.DiGraph()

List=[(1,2),(1,3),(2,3),(3,2),(3,5),(4,2),(4,6),
      (5,2),(5,4),(5,6),(6,5)]
# 添加顶点和弧
G.add_nodes_from(range(1,7))
G.add_edges_from(List)
# 节点在同心圆上分布
pos=nx.shell_layout(G) 
# font_weight：字体粗细；node_color：顶点颜色
nx.draw(G,pos,with_labels=True, font_weight='bold',node_color='r')
plt.figure(figsize=(6, 3)) 
plt.show()

##################################################################################################### 
import plotly.graph_objects as go
pos = nx.spring_layout(G)
x_nodes = [pos[node][0] for node in G.nodes]
y_nodes = [pos[node][1] for node in G.nodes]
edge_x = []
edge_y = []
for edge in G.edges:
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)
    
node_trace = go.Scatter(
    x=x_nodes, y=y_nodes,
    mode='markers+text',
    text=list(G.nodes),
    textposition="bottom center",
    marker=dict(size=10, color="skyblue")
)

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1, color='gray'),
    hoverinfo='none',
    mode='lines'
)

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0,l=0,r=0,t=0),
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=False, zeroline=False))
               )
fig.show()
#######################################################################################################
#人物社交网络分析,设置不同的边属性类型和展示呈现颜色
import networkx as nx
df_net=pd.read_csv("input/red_social_net_weight.csv")
df_net['weight']=df_net.chapweight/120
df_net2=df_net[df_net['weight']>0.45].reset_index(drop=True)
plt.figure(figsize=(12,12))
plt.rcParams['font.sans-serif']=['SimHei']
#生成社交图
G=nx.Graph()
#添加边
for i in df_net2.index:
    G.add_edge(df_net2.First[i],df_net2.Second[i],weight=df_net2.weight[i])
#定义三种边，以便后续不同边设置不同的参数
elarge = [(u,v) for (u,v,d) in G.edges(data=True) if d['weight']>0.2]
emidle = [(u,v) for (u,v,d) in G.edges(data=True) if (d['weight']>0.1 )&( d['weight'] <=0.2)]
esmall =  [(u,v) for (u,v,d) in G.edges(data=True) if d['weight']<=0.1]
#进行图布局
#网络图的三种布局方式
pos=nx.spring_layout(G)
#pos=nx.circular_layout(G)
#pos=nx.random_layout(G)
#计算中心度
Gdegree=nx.degree(G)
Gdegree=dict(Gdegree)
Gdegree=pd.DataFrame({'name':list(Gdegree.keys()),'degree':list(Gdegree.values())})
#node 
# nx.draw_networkx_nodes(G,pos,alpha=0.6,node_size=800)  #指定结点大小
#依据出度和入度进行节点大小的设置
nx.draw_networkx_nodes(G,pos,alpha=0.6,node_size=Gdegree.degree * 100) 
#edge
nx.draw_networkx_edges(G,pos,edgelist=elarge,width=0.5,alpha=0.6,edg_color='r')
nx.draw_networkx_edges(G,pos,edgelist=emidle,width=0.3,alpha=0.5,edg_color='b')
nx.draw_networkx_edges(G,pos,edgelist=esmall,width=0.1,alpha=0.1,edg_color='y',style='dashed')
#label
nx.draw_networkx_labels(G,pos,font_size=10)
plt.axis('off')
plt.title('红楼梦社交网络')
plt.show()

#计算中心度-点度中心度
Gdegree=nx.degree(G)
Gdegree=dict(Gdegree)
Gdegree=pd.DataFrame({'name':list(Gdegree.keys()),'degree':list(Gdegree.values())})
Gdegree.sort_values(by="degree",ascending=False).head(15).plot(x='name',y='degree',kind='bar',figsize=(12,6),legend=False)
plt.xlabel("name",fontsize=10)
plt.ylabel("degree",fontsize=10)
plt.show()

#################################################################################################
#多重图是允许任意一对节点之间存在多条边的图。要创建多重图，可以使用 MultiGraph 类：
MG = nx.MultiGraph()
MG.add_nodes_from(["A", "B", "C"])
MG.add_edges_from([("A", "B"), ("A", "B"), ("B", "C")])

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=800, node_color="skyblue", edge_color="gray")
plt.show()

#度中心性是衡量网络中节点重要性的指标。它只是连接到节点的边的数量，由节点的最大可能度标准化。
G = nx.Graph()
G.add_edges_from([("A", "B"), ("A", "C"), ("B", "C"), ("B", "D")])
degree_centrality = nx.degree_centrality(G)
print(degree_centrality)

辅助参数：
node_color, node_size, node_shape, node_edgecolor, node_facecolor, node_zorder (等)
类型: 各自对应的数据类型（例如颜色字符串、数值、形状字符串、Z-order 整数等）
edge_color, width, style, alpha, edge_zorder (等)
类型: 各自对应的数据类型（例如颜色字符串、数值、线条样式字符串、透明度浮点数、Z-order 整数等）

df_relations = pd.read_csv('triples.csv')
for _, row in df_relations.iterrows():
    a,b,c,d=row
    print(f'a:{a},b:{b},c:{c},d:{d}')

G = nx.Graph()
for _, row in df_relations.iterrows():
    person_A, person_B,relationship_english, relationship = row
    G.add_node(person_A)
    G.add_node(person_B)
    G.add_edge(person_A, person_B, type=relationship)

center_nodes = ['刘备', '曹操', '孙权']
 
# 使用你喜欢的布局算法，这里以spring_layout为例
pos = nx.spring_layout(G, k=0.6, iterations=50)
 
# 手动调整中心节点的位置
center_pos = {'刘备': (0, 0), '曹操': (-0.2, 0), '孙权': (0.2, 0)}
for node, coord in center_pos.items():
    pos[node] = coord
 
# 可以微调其他节点的位置以避免过于拥挤
plt.rcParams['font.sans-serif']='SimHei'
plt.rcParams['axes.unicode_minus']=False
 
node_colors = [ 'lightblue' if node in center_nodes else 'white' for node in G.nodes()]
node_sizes = [1000 if node in center_nodes else 300 for node in G.nodes()]
 
fig=plt.figure(figsize=(16, 16))
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
nx.draw_networkx_edges(G, pos, alpha=0.5)
nx.draw_networkx_labels(G, pos, font_size=10)
 
plt.axis('off')
plt.title('三国人物关系图')
plt.show()
fig.savefig('三国人物关系图.jpg')