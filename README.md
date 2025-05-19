# 三层股权穿透网络分析与查询

本项目使用 Python 和 NetworkX 等库，对符合特定格式的股权穿透数据CSV文件进行网络建模、高级分析、可视化以及节点邻域查询。

## 项目特色

- **股权网络构建**: 从CSV数据准确构建有向图，正确处理`parent_id`和嵌套的`children`字段确定的股权关系 (遵循 Child -> Parent 规则)。
    - **`percent`属性规范化**: `graph_builder.py` 现在会自动将股权比例（`percent`）规范化为0.0到1.0之间的小数，便于后续计算。
- **多样化分析**: 
    - `graph_model.py`: 提供基础的图统计数据和整体股权网络图的可视化。
    - `advanced_analysis.py`: 执行深入分析，包括：
        - 1. 中心性分析（度、接近、中介、特征向量）
        - 2. 社区检测（Louvain算法）
        - 3. 循环持股识别
        - 4. 关键控制者识别
        - 5. 最终控制人分析
        - 6. **股权穿透分析**: 向上（查找最终股东）和向下（查找最终投资）的路径分析。输出路径中每一步的直接持股比例及整个路径的最终累积持股/控制比例。
        - 7. **关联方初步分析 (共同投资)**: 识别被多个股东共同投资的公司，并列出这些共同投资方及其持股详情。
        - 8. 链路合理性检查 (自循环、父节点信息、持股比例有效性)
        - 生成详细的文本报告和可视化图表。
    - `query_node_neighborhood.py`: 允许用户通过节点名称查询其指定度数（默认为2度）的邻域网络，输出详细的节点/边信息到文本文件，并生成邻域可视化图。
- **模块化设计**: 
    - `graph_builder.py`: 封装了核心的图构建逻辑。
    - `graph_persistence.py`: 用于保存和加载图模型（使用GraphML格式），方便后续增量修改和分析。
    - `font_config.py`: 统一管理中文字体配置，确保图表中文显示正常。
- **可配置输出**: 生成多种图片（.png）和文本报告（.txt），统一保存到 `outputs/` 文件夹中。

## 项目结构

```
graph-main/
├── graph_model.py               # 基础网络建模与可视化
├── advanced_analysis.py         # 高级网络分析与报告生成
├── query_node_neighborhood.py   # 节点邻域查询与可视化
├── graph_builder.py             # 核心图构建模块
├── graph_persistence.py         # 图模型持久化（保存/加载）模块
├── font_config.py               # 中文字体配置模块
├── visualize_graph_construction.py # 图构建过程可视化
├── 三层股权穿透输出数据.csv       # 【示例】输入的股权数据CSV文件
├── requirements.txt             # Python依赖包列表
├── README.md                    # 本文件
├── outputs/                     # 输出文件夹
│   ├── reports/                 # 文本报告保存目录
│   │   ├── advanced_analysis_report.txt  # 高级分析报告
│   │   ├── query_result_*.txt           # 节点查询结果报告
│   │   └── graph_construction_stats.txt # 图构建统计报告
│   ├── images/                  # 可视化图像保存目录
│   │   ├── graph_model_visualization.png # 整体网络可视化图
│   │   ├── 股权关系社区结构.png           # 社区检测结果图
│   │   ├── 最终控制人网络图.png           # (旧版，可按需保留或由新分析替代)
│   │   ├── query_result_*.png           # 节点邻域查询图
│   │   └── graph_construction_final.png # 图构建最终状态图
│   ├── graph_model.graphml      # （如果使用 graph_persistence.py 保存）保存的图模型文件
│   └── temp/                    # 临时文件目录
└── [旧版输出文件]               # 项目根目录下可能存在的旧版输出文件
```

## 安装依赖

1.  确保您已安装 Python 3.8 或更高版本。
2.  建议使用虚拟环境以避免包冲突：
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```
3.  安装所需的依赖包：
    ```bash
    pip install -r requirements.txt
    ```

## 数据格式说明

输入的CSV文件（例如 `三层股权穿透输出数据.csv`）应包含但不限于以下关键字段，用于构建股权关系网络：

- `eid`: 实体唯一ID (推荐，如果名称可能重复)。如果缺失，将使用`name`作为ID。
- `name`: 实体名称（公司或个人）。
- `type`: 实体类型 (例如: 'E'代表企业, 'P'代表个人)。用于可视化时的节点区分。
- `level`: 实体在股权结构中的层级。用于可视化标签。
- `parent_id`: 该实体直接父节点的ID。关系为：当前实体 -> `parent_id`实体。
- `children`: 一个JSON字符串，描述直接持有当前实体股份的股东信息。每个股东对象可包含`name`, `eid`, `type`, `level`, `percent`等。关系为：`children`中的股东 -> 当前实体。
- `percent`: 持股比例。在 `graph_builder.py` 中会被规范化为 0.0 到 1.0 之间的小数（`None` 表示未知）。原始数据可以是 '10.5%' 或 10.5 或 '0.105' 等形式。
- `amount`: 投资金额。
- `sh_type`: 股东类型/持股类型。

**重要**: `graph_builder.py` 会尝试使用多种中文编码（gbk, gb18030, gb2312, utf-8, big5）读取CSV文件。

## 使用方法

确保您的CSV数据文件与脚本在同一目录，或在脚本中指定正确的文件路径。

1.  **基础网络建模与整体可视化 (`graph_model.py`)**
    ```bash
    python graph_model.py
    ```
    - 输出: 
        - 控制台打印图的基本统计信息。
        - 生成 `outputs/images/graph_model_visualization.png` 图片。

2.  **高级网络分析与报告生成 (`advanced_analysis.py`)**
    ```bash
    python advanced_analysis.py
    ```
    - 输出:
        - 控制台打印分析过程和总结。
        - 生成 `outputs/reports/advanced_analysis_report.txt` 包含详细分析结果（包括新的股权穿透分析）和逻辑说明的文本报告。
        - 生成 `outputs/images/股权关系社区结构.png` 等可视化图片。

3.  **节点邻域查询 (`query_node_neighborhood.py`)**
    
    查询特定节点的N度邻域信息 (默认为2度)。
    ```bash
    python query_node_neighborhood.py "节点的确切名称"
    ```
    例如:
    ```bash
    python query_node_neighborhood.py "阿里巴巴（中国）网络技术有限公司"
    ```
    查询指定度数的邻域 (例如1度):
    ```bash
    python query_node_neighborhood.py "节点名称" --radius 1
    ```
    - 输出:
        - 控制台打印查询过程和总结。
        - 生成 `outputs/reports/query_result_节点名称.txt` 包含该节点及其N度邻域内其他节点和关系的详细信息。
        - 生成 `outputs/images/query_result_节点名称.png` 可视化该邻域网络。

4.  **图构建过程可视化 (`visualize_graph_construction.py`)**
    ```bash
    python visualize_graph_construction.py
    ```
    - 输出:
        - 控制台打印图构建过程信息。
        - 生成 `outputs/images/graph_construction_final.png` 图构建最终状态图。
        - 生成 `outputs/reports/graph_construction_stats.txt` 图构建统计报告。

5.  **图模型持久化 (`graph_persistence.py`)**
    ```bash
    python graph_persistence.py
    ```
    - 功能: 构建图 -> 保存到 `outputs/graph_model.graphml` -> 从文件加载图。
    - 你可以修改此脚本以加载已保存的图并进行进一步操作（例如添加边、执行分析等）。

## 输出文件夹结构

项目现在使用结构化的输出文件夹组织，文件分类如下：

- **outputs/reports/** - 存放所有文本报告和分析结果
- **outputs/images/** - 存放所有可视化图像
- **outputs/graph_model.graphml** - （如果使用 `graph_persistence.py`）保存的图模型文件。
- **outputs/temp/** - 存放临时文件和中间处理结果

当运行各个脚本时，所有输出文件将自动保存到相应的文件夹中。如果文件夹不存在，将自动创建。

## 注意事项

- **中文字体**: 项目包含 `font_config.py` 以尝试自动配置中文字体。如果图表中的中文显示为方框，请确保您的系统中安装了常见的中文字体 (如SimHei, Microsoft YaHei等)，或者根据需要修改 `font_config.py` 中的字体列表。
- **性能**: 对于非常大的CSV文件和复杂的网络，图的生成、布局计算和分析可能需要较长时间和较多内存。股权穿透分析的深度（`max_depth`）也会影响性能。
- **CSV编码**: 脚本会尝试多种常见中文编码。如果您的CSV文件使用非常特殊的编码，可能需要手动在 `graph_builder.py` 的 `pd.read_csv()` 部分指定。
- **累积持股比例**: `advanced_analysis.py` 中的股权穿透分析计算的是沿单一路径的累积持股比例。对于一个实体通过多条路径被间接持股/控制的复杂情况，总有效持股比例的计算可能需要更复杂的算法，当前版本为分别列出各路径。
- **关联方分析**: 当前为初步共同投资分析，更复杂的关联关系（如一致行动人、共同高管等）识别需要更多数据和算法。

## 未来可能的改进

- 增加更复杂的权重计算和边属性利用（例如 `amount`）。
- 实现更精确的总有效持股比例合并算法。
- 提供交互式可视化选项 (例如使用 Pyvis 或 Dash/Streamlit)。
- 优化超大图的处理性能。
- 增加更多针对性的风控分析模块和模式识别。 