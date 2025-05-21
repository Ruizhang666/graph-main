// 创建Vue应用
const app = new Vue({
    el: '#app',
    data() {
        return {
            // 图统计信息
            graphStats: null,
            // 搜索相关
            searchQuery: '',
            searchResults: [],
            searchError: null,
            // 当前选中公司
            currentCompany: null,
            // 投资方详情相关
            investorsWithDetails: [],
            loadingInvestorDetails: false,
            selectedInvestor: null,
            // 当前活动标签页
            activeTab: 'overview',
            // 股权穿透分析
            generatingAnalysis: false,
            equityAnalysisResult: {
                upstream: null,
                downstream: null
            },
            // 扁平化的投资方和被投资方列表
            flattenUpstreamInvestors: [],
            flattenDownstreamInvestees: []
        }
    },
    created() {
        // 加载图统计信息
        this.loadGraphStats();
    },
    methods: {
        // 加载图统计信息
        loadGraphStats() {
            axios.get('/api/graph/stats')
                .then(response => {
                    this.graphStats = response.data;
                })
                .catch(error => {
                    console.error('加载图统计信息失败:', error);
                    this.$message.error('加载图统计信息失败');
                });
        },
        
        // 搜索公司
        searchCompany() {
            if (!this.searchQuery.trim()) {
                this.$message.warning('请输入公司名称');
                return;
            }
            
            this.searchResults = [];
            this.searchError = null;
            
            axios.get('/api/search', { params: { q: this.searchQuery } })
                .then(response => {
                    if (response.data.id) {
                        // 精确匹配
                        this.selectCompanyById(response.data.id);
                    } else if (response.data.partial_matches) {
                        // 部分匹配
                        this.searchResults = response.data.partial_matches;
                    } else {
                        this.searchError = '未找到匹配的公司';
                    }
                })
                .catch(error => {
                    console.error('搜索失败:', error);
                    this.searchError = error.response?.data?.error || '搜索失败';
                });
        },
        
        // 选择搜索结果中的公司
        selectCompany(row) {
            this.selectCompanyById(row.id);
        },
        
        // 选择关联公司
        selectRelatedCompany(row) {
            console.log('选择关联公司', row);
            // 检查row是否有id属性
            if (!row.id) {
                console.error('投资方数据缺少ID', row);
                // 尝试使用name作为备选方案进行搜索
                if (row.name) {
                    this.searchQuery = row.name;
                    this.searchCompany();
                    return;
                }
                this.$message.error('无法获取投资方ID，无法显示其关系');
                return;
            }
            this.selectCompanyById(row.id);
        },
        
        // 根据ID选择公司
        selectCompanyById(id) {
            axios.get(`/api/node/${id}`)
                .then(response => {
                    this.currentCompany = response.data;
                    this.searchResults = [];
                    this.searchError = null;
                    this.selectedInvestor = null; // 重置选中的投资方
                    
                    // 处理投资方数据
                    if (this.currentCompany.investors && this.currentCompany.investors.length > 0) {
                        this.processInvestorsData();
                    }
                    
                    // 切换到投资方详情标签页
                    this.activeTab = 'investor_details';
                })
                .catch(error => {
                    console.error('获取公司信息失败:', error);
                    this.$message.error('获取公司信息失败');
                });
        },
        
        // 处理投资方数据
        processInvestorsData() {
            if (!this.currentCompany || !this.currentCompany.investors) return;
            this.loadingInvestorDetails = true;
            this.investorsWithDetails = [];
            // 调试输出整个currentCompany和投资方数据结构
            console.log('当前公司完整数据:', JSON.stringify(this.currentCompany));
            console.log('投资方列表:', this.currentCompany.investors);
            // 处理每个投资方的指标数据
            this.investorsWithDetails = this.currentCompany.investors.map(investor => {
                const pagerank = investor.pagerank !== undefined && investor.pagerank !== null
                    ? investor.pagerank
                    : (investor.metrics && investor.metrics.pagerank !== undefined ? investor.metrics.pagerank : null);
                return {
                    ...investor,
                    pagerank: pagerank,
                    degree_centrality: investor.metrics && investor.metrics.degree_centrality !== undefined ? investor.metrics.degree_centrality : null,
                    betweenness_centrality: investor.metrics && investor.metrics.betweenness_centrality !== undefined ? investor.metrics.betweenness_centrality : null,
                    indegree: investor.metrics && investor.metrics.in_degree !== undefined ? investor.metrics.in_degree : 0,
                    outdegree: investor.metrics && investor.metrics.out_degree !== undefined ? investor.metrics.out_degree : 0
                };
            });
            if (this.investorsWithDetails.length > 0) {
                this.selectInvestorDetails(this.investorsWithDetails[0]);
            }
            this.loadingInvestorDetails = false;
        },
        
        // 从节点数据中提取投资方画像指标
        extractInvestorMetrics(nodeData) {
            return {
                pagerank: nodeData.pagerank !== undefined && nodeData.pagerank !== null
                    ? nodeData.pagerank
                    : (nodeData.metrics && nodeData.metrics.pagerank !== undefined ? nodeData.metrics.pagerank : null),
                indegree: nodeData.investors ? nodeData.investors.length : 0,
                outdegree: nodeData.investees ? nodeData.investees.length : 0,
                degree_centrality: nodeData.metrics && nodeData.metrics.degree_centrality !== undefined ? nodeData.metrics.degree_centrality : null,
                betweenness_centrality: nodeData.metrics && nodeData.metrics.betweenness_centrality !== undefined ? nodeData.metrics.betweenness_centrality : null,
                level: nodeData.level || '',
                type: nodeData.type || '',
                investees: nodeData.investees || []
            };
        },
        
        // 从图统计数据中获取节点度量值（PageRank等）
        getNodeMetric(nodeId, metricType) {
            if (!this.graphStats) return null;
            
            let metricList = null;
            
            switch (metricType) {
                case 'pagerank':
                    metricList = this.graphStats.top_pagerank;
                    break;
                case 'degree_centrality':
                    metricList = this.graphStats.top_degree_centrality;
                    break;
                default:
                    return null;
            }
            
            if (!metricList) return null;
            
            // 在度量列表中查找节点
            for (const item of metricList) {
                if (item.id === nodeId) {
                    return item.score;
                }
            }
            
            return null;
        },
        
        // 选择投资方详情
        selectInvestorDetails(investor) {
            this.selectedInvestor = investor;
            
            // 滚动到详情卡片
            this.$nextTick(() => {
                const detailsCard = document.getElementById('investor-details-card');
                if (detailsCard) {
                    detailsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        },
        
        // 为投资方表格添加行类名
        getRowClassName({row}) {
            // 如果当前行是选中的投资方，返回自定义类名
            if (this.selectedInvestor && row.id === this.selectedInvestor.id) {
                return 'investor-selected';
            }
            return '';
        },
        
        // 查看投资方的全部关系
        viewInvestorRelations(investor) {
            console.log('查看投资方关系', investor);
            
            // 如果没有ID，尝试直接使用name进行查询
            if (!investor.id && investor.name) {
                this.searchQuery = investor.name;
                this.searchCompany();
                return;
            }
            
            // 否则通过API直接获取投资方信息
            axios.get(`/api/node/${investor.id}`)
                .catch(error => {
                    console.error('获取投资方信息失败:', error);
                    this.$message.error('获取投资方信息失败');
                    
                    // 如果API失败，尝试使用搜索功能
                    if (investor.name) {
                        this.searchQuery = investor.name;
                        this.searchCompany();
                    }
                });
        },
        
        // 生成股权穿透分析
        generateEquityAnalysis() {
            if (!this.currentCompany) return;
            
            this.generatingAnalysis = true;
            this.equityAnalysisResult = {
                upstream: null,
                downstream: null
            };
            
            axios.get(`/api/equity_analysis/${this.currentCompany.id}`)
                .then(response => {
                    this.equityAnalysisResult = response.data; // 包含 upstream, downstream, 和新增的 direct_upstream_shareholders_flat
                    this.generatingAnalysis = false;
                    
                    // 处理扁平化的上游和下游数据，如果需要用于其他地方
                    this.flattenUpstreamInvestors = this.flattenInvestors(this.equityAnalysisResult.upstream || []);
                    this.flattenDownstreamInvestees = this.flattenInvestees(this.equityAnalysisResult.downstream || []);

                    // 新增：填充直接上游股东验证表格
                    const validationTableBody = document.getElementById('direct-shareholders-table-body');
                    if (validationTableBody) {
                        validationTableBody.innerHTML = ''; // 清空旧数据
                        const shareholders = response.data.direct_upstream_shareholders_flat;
                        if (shareholders && shareholders.length > 0) {
                            shareholders.forEach(shareholder => {
                                const row = validationTableBody.insertRow();
                                row.insertCell().textContent = shareholder.name || 'N/A';
                                row.insertCell().textContent = shareholder.type || 'N/A';
                                row.insertCell().textContent = shareholder.percent || 'N/A';
                            });
                        } else {
                            validationTableBody.innerHTML = '<tr><td colspan="3">未找到直接上游股东数据 (来自API)。</td></tr>';
                        }
                    } else {
                        console.warn("未能找到ID为 'direct-shareholders-table-body' 的元素来显示验证数据。");
                    }

                })
                .catch(error => {
                    console.error('生成股权穿透分析失败:', error);
                    this.$message.error('生成股权穿透分析失败');
                    this.generatingAnalysis = false;
                });
        },
        
        // 扁平化投资方树结构
        flattenInvestors(investors) {
            let result = [];
            const processNode = (node, level) => {
                if (!node) return;
                
                result.push(node);
            };

            if (investors && Array.isArray(investors)) {
                investors.forEach(investorNode => {
                    result.push(investorNode);
                });
            }
            return result;
        },
        
        // 扁平化被投资企业树结构
        flattenInvestees(investees) {
            let result = [];
            if (investees && Array.isArray(investees)) {
                investees.forEach(investeeNode => {
                    result.push(investeeNode);
                });
            }
            return result;
        },
        
        // 处理上游股权结构
        processUpstreamEquity() {
            // 构建当前公司为根节点
            const rootNode = {
                id: this.currentCompany.id,
                name: this.currentCompany.name,
                type: this.currentCompany.type,
                children: []
            };
            
            // 添加投资方作为子节点
            if (this.currentCompany.investors) {
                this.currentCompany.investors.forEach(investor => {
                    rootNode.children.push({
                        id: investor.id,
                        name: investor.name,
                        type: investor.type,
                        percent: investor.percent,
                        pagerank: investor.pagerank,
                        children: [] // 可以根据需要递归构建更深层次的股权结构
                    });
                });
            }
            
            return [rootNode];
        },
        
        // 处理下游股权结构
        processDownstreamEquity() {
            // 构建当前公司为根节点
            const rootNode = {
                id: this.currentCompany.id,
                name: this.currentCompany.name,
                type: this.currentCompany.type,
                children: []
            };
            
            // 添加被投资企业作为子节点
            if (this.currentCompany.investees) {
                this.currentCompany.investees.forEach(investee => {
                    rootNode.children.push({
                        id: investee.id,
                        name: investee.name,
                        type: investee.type,
                        percent: investee.percent,
                        pagerank: investee.pagerank,
                        children: [] // 可以根据需要递归构建更深层次的股权结构
                    });
                });
            }
            
            return [rootNode];
        },
        
        // 设置节点为中心企业
        viewAsCenter(nodeId) {
            if (!nodeId) {
                this.$message.warning('节点ID无效，无法设为中心企业');
                return;
            }
            
            console.log('设置节点为中心企业:', nodeId);
            this.selectCompanyById(nodeId);
            this.activeTab = 'equity_analysis'; // 保持在股权穿透分析标签页
            
            // 自动生成新中心企业的股权分析
            this.$nextTick(() => {
                this.generateEquityAnalysis();
            });
        }
    }
});
