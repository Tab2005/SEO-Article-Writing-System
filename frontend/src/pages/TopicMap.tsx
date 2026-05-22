import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
    GitFork, Plus, Save, Archive, 
    BookOpen, AlertTriangle, FileText, 
    Upload, ChevronRight, ChevronDown, Edit3
} from 'lucide-react'
import { planningService, TopicNode, ContentItem } from '../services/planning.service'
import { useProjectStore } from '../store/projectStore'

function TopicMapPage() {
    const navigate = useNavigate()
    const { currentProject } = useProjectStore()
    const [nodes, setNodes] = useState<TopicNode[]>([])
    const [flatNodes, setFlatNodes] = useState<TopicNode[]>([])
    const [unmappedItems, setUnmappedItems] = useState<ContentItem[]>([])
    const [mappedItemsForSelected, setMappedItemsForSelected] = useState<ContentItem[]>([])
    const [gaps, setGaps] = useState<any[]>([])
    
    const [loading, setLoading] = useState(true)
    const [selectedNode, setSelectedNode] = useState<TopicNode | null>(null)
    const [isEditing, setIsEditing] = useState(false)
    const [showImportModal, setShowImportModal] = useState(false)
    const [showAddChildModal, setShowAddChildModal] = useState(false)
    const [showAddRootModal, setShowAddRootModal] = useState(false)

    // Form inputs for editing/creating
    const [nodeName, setNodeName] = useState('')
    const [nodeRole, setNodeRole] = useState<'pillar' | 'supporting' | 'bridge' | 'comparison' | 'decision' | 'faq'>('supporting')
    const [nodeDesc, setNodeDesc] = useState('')
    const [nodeStage, setNodeStage] = useState<'awareness' | 'consideration' | 'decision' | ''>('awareness')
    const [nodePriority, setNodePriority] = useState<'high' | 'medium' | 'low'>('medium')
    const [nodeSort, setNodeSort] = useState(0)
    const [nodeParentId, setNodeParentId] = useState<string>('')

    // Form inputs for bulk import
    const [importText, setImportText] = useState('')
    const [importing, setImporting] = useState(false)

    // Form inputs for adding child
    const [childName, setChildName] = useState('')
    const [childRole, setChildRole] = useState<'supporting' | 'bridge' | 'comparison' | 'decision' | 'faq'>('supporting')
    const [childDesc, setChildDesc] = useState('')
    const [childStage, setChildStage] = useState<'awareness' | 'consideration' | 'decision'>('awareness')
    const [childPriority, setChildPriority] = useState<'high' | 'medium' | 'low'>('medium')

    // Form inputs for adding root
    const [rootName, setRootName] = useState('')
    const [rootDesc, setRootDesc] = useState('')
    const [rootStage, setRootStage] = useState<'awareness' | 'consideration' | 'decision'>('awareness')
    const [rootPriority, setRootPriority] = useState<'high' | 'medium' | 'low'>('medium')

    // Tree expanded state
    const [expandedNodeIds, setExpandedNodeIds] = useState<Record<string, boolean>>({})

    useEffect(() => {
        if (!currentProject) return
        loadTopicMapData()
    }, [currentProject])

    const loadTopicMapData = async () => {
        try {
            setLoading(true)
            const projectId = currentProject!.id
            
            // 1. Get Tree
            const tree = await planningService.getTopicNodes(projectId, true)
            setNodes(tree)
            
            // 2. Get Flat List
            const flat = await planningService.getTopicNodes(projectId, false)
            setFlatNodes(flat)

            // 3. Get Gaps
            const gapList = await planningService.getTopicMapGaps(projectId)
            setGaps(gapList)

            // 4. Get Content Items
            if (currentProject?.mode === 'existing_site') {
                const unmapped = await planningService.getContentItems(projectId, false)
                setUnmappedItems(unmapped)
            }

            // Keep selected node references updated
            if (selectedNode) {
                const updatedSelected = flat.find(n => n.id === selectedNode.id)
                if (updatedSelected) {
                    setSelectedNode(updatedSelected)
                    loadContentItemsForNode(updatedSelected.id)
                } else {
                    setSelectedNode(null)
                    setMappedItemsForSelected([])
                }
            }
        } catch (err) {
            console.error('Failed to load topic map data:', err)
        } finally {
            setLoading(false)
        }
    }

    const loadContentItemsForNode = async (nodeId: string) => {
        if (!currentProject || currentProject.mode !== 'existing_site') return
        try {
            const allItems = await planningService.getContentItems(currentProject.id)
            const filtered = allItems.filter(item => item.mapped_topic_id === nodeId)
            setMappedItemsForSelected(filtered)
        } catch (err) {
            console.error('Failed to load mapped content items:', err)
        }
    }

    const handleSelectNode = (node: TopicNode) => {
        setSelectedNode(node)
        setIsEditing(false)
        
        // Populate inputs for editing
        setNodeName(node.name)
        setNodeRole(node.topic_role)
        setNodeDesc(node.description || '')
        setNodeStage(node.journey_stage || '')
        setNodePriority(node.priority)
        setNodeSort(node.sort_order)
        setNodeParentId(node.parent_id || '')

        loadContentItemsForNode(node.id)
    }

    const toggleExpand = (nodeId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        setExpandedNodeIds(prev => ({
            ...prev,
            [nodeId]: !prev[nodeId]
        }))
    }

    const handleSaveEdit = async () => {
        if (!currentProject || !selectedNode) return
        try {
            const updatePayload: Partial<TopicNode> = {
                name: nodeName,
                topic_role: nodeRole,
                description: nodeDesc || undefined,
                journey_stage: nodeStage ? (nodeStage as any) : null,
                priority: nodePriority,
                sort_order: nodeSort
            }
            // Update basic details
            await planningService.updateTopicNode(currentProject.id, selectedNode.id, updatePayload)
            
            // Parent move checks
            if (nodeParentId !== (selectedNode.parent_id || '')) {
                const targetParent = nodeParentId === '' ? null : nodeParentId
                await planningService.moveTopicNode(currentProject.id, selectedNode.id, targetParent)
            }

            setIsEditing(false)
            setUnmappedItems([])
            await loadTopicMapData()
            alert('主題節點已成功更新！')
        } catch (err: any) {
            console.error('Failed to update node:', err)
            alert(err.response?.data?.detail || '更新失敗。請檢查是否造成主題循環依賴！')
        }
    }

    const handleArchiveNode = async (nodeId: string) => {
        if (!currentProject) return
        if (!confirm('您確定要封存此主題節點嗎？封存後它將不再參與評估計算。')) return
        try {
            await planningService.archiveTopicNode(currentProject.id, nodeId)
            setSelectedNode(null)
            await loadTopicMapData()
        } catch (err) {
            console.error('Failed to archive node:', err)
            alert('封存失敗。')
        }
    }

    const handleAddRoot = async () => {
        if (!currentProject || !rootName.trim()) return
        try {
            await planningService.createTopicNode(currentProject.id, {
                name: rootName,
                topic_role: 'pillar',
                description: rootDesc || undefined,
                journey_stage: rootStage || undefined,
                priority: rootPriority,
                status: 'active'
            })
            setShowAddRootModal(false)
            setRootName('')
            setRootDesc('')
            setRootStage('awareness')
            setRootPriority('medium')
            await loadTopicMapData()
        } catch (err) {
            console.error('Failed to create root node:', err)
            alert('新增核心主題失敗。')
        }
    }

    const handleAddChild = async () => {
        if (!currentProject || !selectedNode || !childName.trim()) return
        try {
            await planningService.createTopicNode(currentProject.id, {
                name: childName,
                topic_role: childRole,
                description: childDesc || undefined,
                journey_stage: childStage || undefined,
                priority: childPriority,
                parent_id: selectedNode.id,
                status: 'active'
            })
            setShowAddChildModal(false)
            setChildName('')
            setChildDesc('')
            setChildRole('supporting')
            setChildStage('awareness')
            setChildPriority('medium')
            
            // Expand parent so child is visible
            setExpandedNodeIds(prev => ({
                ...prev,
                [selectedNode.id]: true
            }))

            await loadTopicMapData()
        } catch (err) {
            console.error('Failed to create child node:', err)
            alert('新增子主題失敗。')
        }
    }

    const handleBulkImport = async () => {
        if (!currentProject || !importText.trim()) return
        try {
            setImporting(true)
            const lines = importText.split('\n')
            const items = lines.map(line => {
                const parts = line.split(',')
                const title = parts[0]?.trim()
                const url = parts[1]?.trim()
                return {
                    title,
                    url: url || undefined,
                    content_type: 'article'
                }
            }).filter(item => item.title !== '')

            await planningService.importContentItems(currentProject.id, items)
            setShowImportModal(false)
            setImportText('')
            await loadTopicMapData()
            alert(`已成功匯入 ${items.length} 篇舊文章！`)
        } catch (err) {
            console.error('Failed to import items:', err)
            alert('匯入失敗，請檢查輸入格式。')
        } finally {
            setImporting(false)
        }
    }

    const handleMapContentItem = async (itemId: string, nodeId: string | null) => {
        if (!currentProject) return
        try {
            await planningService.mapContentItem(currentProject.id, itemId, nodeId)
            await loadTopicMapData()
        } catch (err) {
            console.error('Failed to map content item:', err)
            alert('映射失敗。')
        }
    }

    // Render tree nodes recursively
    const renderTreeNode = (node: TopicNode, depth = 0) => {
        const hasChildren = node.children && node.children.length > 0
        const isExpanded = expandedNodeIds[node.id] || false
        const isSelected = selectedNode?.id === node.id

        return (
            <div key={node.id} className="select-none">
                <div
                    onClick={() => handleSelectNode(node)}
                    style={{ paddingLeft: `${depth * 16 + 8}px` }}
                    className={`flex items-center justify-between py-2.5 pr-4 rounded-lg cursor-pointer transition-colors ${
                        isSelected 
                            ? 'bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-400 font-semibold' 
                            : 'hover:bg-gray-50 dark:hover:bg-slate-800 text-gray-700 dark:text-gray-300'
                    }`}
                >
                    <div className="flex items-center gap-1.5 min-w-0">
                        {hasChildren ? (
                            <button
                                onClick={(e) => toggleExpand(node.id, e)}
                                className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                            >
                                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </button>
                        ) : (
                            <div className="w-6" />
                        )}
                        <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                            node.topic_role === 'pillar'
                                ? 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-400'
                                : 'bg-gray-100 dark:bg-slate-700 text-gray-500'
                        }`}>
                            {node.topic_role === 'pillar' ? 'Pillar' : node.topic_role.toUpperCase()}
                        </span>
                        <span className="truncate text-sm">{node.name}</span>
                    </div>
                </div>

                {hasChildren && isExpanded && (
                    <div className="mt-0.5">
                        {node.children!.map(child => renderTreeNode(child, depth + 1))}
                    </div>
                )}
            </div>
        )
    }

    if (!currentProject) {
        return (
            <div className="card text-center py-16">
                <GitFork className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">未選定專案</h3>
                <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6 text-sm">
                    請先至專案管理頁面選擇或建立一個專案，再編輯主題地圖。
                </p>
                <button onClick={() => navigate('/projects')} className="btn-primary">
                    前往專案管理
                </button>
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        主題地圖 (Topic Map)
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        目前專案：<span className="font-semibold text-primary-600 dark:text-primary-400">{currentProject.name}</span>
                        <span className="ml-3 text-xs text-gray-400">
                            模式：{currentProject.mode === 'new_site' ? '新站模式' : '舊站優化'}
                        </span>
                    </p>
                </div>
                <div className="flex gap-3">
                    {currentProject.mode === 'existing_site' && (
                        <button
                            onClick={() => setShowImportModal(true)}
                            className="btn-secondary flex items-center justify-center gap-2"
                        >
                            <Upload className="w-5 h-5" />
                            匯入舊文章
                        </button>
                    )}
                    <button
                        onClick={() => setShowAddRootModal(true)}
                        className="btn-primary flex items-center justify-center gap-2"
                    >
                        <Plus className="w-5 h-5" />
                        新增核心主題 (Pillar)
                    </button>
                </div>
            </div>

            {/* Gap Analysis Box */}
            {gaps.length > 0 && (
                <div className="card border-amber-200 dark:border-amber-900/30 bg-amber-50/50 dark:bg-amber-950/10 space-y-3">
                    <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                        <AlertTriangle className="w-5 h-5" />
                        <h3 className="font-semibold text-sm">主題地圖缺口與警示分析 ({gaps.length})</h3>
                    </div>
                    <ul className="space-y-2">
                        {gaps.map((gap, index) => (
                            <li key={index} className="text-sm text-gray-600 dark:text-gray-300">
                                <strong>{gap.title}</strong>：{gap.description}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {loading ? (
                <div className="text-center py-12 text-gray-500">載入中...</div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    {/* Left: Tree Directory */}
                    <div className="lg:col-span-2 card space-y-4 flex flex-col h-[700px]">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 border-b border-gray-100 dark:border-slate-700 pb-3 flex items-center gap-2 text-sm">
                            <BookOpen className="w-4 h-4 text-primary-600" />
                            主題架構樹
                        </h3>
                        <div className="flex-1 overflow-y-auto space-y-1 pr-2">
                            {nodes.length > 0 ? (
                                nodes.map(node => renderTreeNode(node))
                            ) : (
                                <div className="text-center py-12 text-gray-400 text-sm">
                                    此地圖中尚無主題節點。請點選上方「新增核心主題」開始規劃。
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right: Selected Node details / actions */}
                    <div className="lg:col-span-3 space-y-6">
                        {selectedNode ? (
                            <div className="card space-y-6">
                                {/* Title and Header */}
                                <div className="flex justify-between items-start border-b border-gray-100 dark:border-slate-700 pb-4">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs px-2 py-0.5 rounded bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-400 font-medium">
                                                {selectedNode.topic_role.toUpperCase()}
                                            </span>
                                            <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                                                selectedNode.priority === 'high' 
                                                    ? 'bg-red-50 text-red-600' 
                                                    : selectedNode.priority === 'low' 
                                                    ? 'bg-gray-100 text-gray-500' 
                                                    : 'bg-blue-50 text-blue-600'
                                            }`}>
                                                優先級：{selectedNode.priority.toUpperCase()}
                                            </span>
                                        </div>
                                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mt-2">
                                            {selectedNode.name}
                                        </h2>
                                    </div>
                                    <div className="flex gap-2">
                                        {!isEditing && (
                                            <button
                                                onClick={() => setIsEditing(true)}
                                                className="text-xs px-3 py-1.5 border border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center gap-1 font-medium transition-colors"
                                            >
                                                <Edit3 className="w-3.5 h-3.5" /> 編輯主題
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleArchiveNode(selectedNode.id)}
                                            className="text-xs px-3 py-1.5 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 rounded hover:bg-red-100 flex items-center gap-1 font-medium transition-colors"
                                        >
                                            <Archive className="w-3.5 h-3.5" /> 封存主題
                                        </button>
                                    </div>
                                </div>

                                {/* Form / Detail View */}
                                <div className="space-y-4">
                                    {isEditing ? (
                                        <div className="space-y-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">主題名稱</label>
                                                    <input
                                                        type="text"
                                                        value={nodeName}
                                                        onChange={(e) => setNodeName(e.target.value)}
                                                        className="input text-sm"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">主題角色</label>
                                                    <select
                                                        value={nodeRole}
                                                        onChange={(e) => setNodeRole(e.target.value as any)}
                                                        className="input text-sm"
                                                    >
                                                        <option value="pillar">核心主題 (Pillar)</option>
                                                        <option value="supporting">支持副主題 (Supporting)</option>
                                                        <option value="bridge">橋接內容 (Bridge)</option>
                                                        <option value="comparison">對比評測 (Comparison)</option>
                                                        <option value="decision">決策購買 (Decision)</option>
                                                        <option value="faq">常見問答 (FAQ)</option>
                                                    </select>
                                                </div>
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述說明</label>
                                                <textarea
                                                    value={nodeDesc}
                                                    onChange={(e) => setNodeDesc(e.target.value)}
                                                    className="input text-sm"
                                                    rows={3}
                                                />
                                            </div>

                                            <div className="grid grid-cols-3 gap-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">漏斗階段</label>
                                                    <select
                                                        value={nodeStage}
                                                        onChange={(e) => setNodeStage(e.target.value as any)}
                                                        className="input text-sm"
                                                    >
                                                        <option value="">未定義</option>
                                                        <option value="awareness">認知階段 (Awareness)</option>
                                                        <option value="consideration">考慮階段 (Consideration)</option>
                                                        <option value="decision">決策階段 (Decision)</option>
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">優先級</label>
                                                    <select
                                                        value={nodePriority}
                                                        onChange={(e) => setNodePriority(e.target.value as any)}
                                                        className="input text-sm"
                                                    >
                                                        <option value="high">High</option>
                                                        <option value="medium">Medium</option>
                                                        <option value="low">Low</option>
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">排序權重值</label>
                                                    <input
                                                        type="number"
                                                        value={nodeSort}
                                                        onChange={(e) => setNodeSort(Number(e.target.value))}
                                                        className="input text-sm"
                                                    />
                                                </div>
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">移至新父主題 (防循環)</label>
                                                <select
                                                    value={nodeParentId}
                                                    onChange={(e) => setNodeParentId(e.target.value)}
                                                    className="input text-sm"
                                                >
                                                    <option value="">[無父級節點 - 成為頂層根主題]</option>
                                                    {flatNodes
                                                        .filter(n => n.id !== selectedNode.id && n.status !== 'archived')
                                                        .map(n => (
                                                            <option key={n.id} value={n.id}>{n.name} ({n.topic_role.toUpperCase()})</option>
                                                        ))}
                                                </select>
                                            </div>

                                            <div className="flex justify-end gap-2 pt-2">
                                                <button
                                                    onClick={() => setIsEditing(false)}
                                                    className="btn-secondary text-sm px-4 py-2"
                                                >
                                                    取消
                                                </button>
                                                <button
                                                    onClick={handleSaveEdit}
                                                    className="btn-primary text-sm px-4 py-2 flex items-center gap-1.5"
                                                >
                                                    <Save className="w-4 h-4" /> 儲存變更
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="space-y-4 text-sm">
                                            {selectedNode.description && (
                                                <div className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
                                                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-1 text-xs">主題描述</h4>
                                                    <p className="text-gray-600 dark:text-gray-300">{selectedNode.description}</p>
                                                </div>
                                            )}

                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                                                <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg">
                                                    <span className="block text-xs text-gray-400">漏斗階段</span>
                                                    <span className="block font-semibold text-gray-700 mt-1">
                                                        {selectedNode.journey_stage ? selectedNode.journey_stage.toUpperCase() : '未填'}
                                                    </span>
                                                </div>
                                                <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg">
                                                    <span className="block text-xs text-gray-400">排序權重值</span>
                                                    <span className="block font-semibold text-gray-700 mt-1">{selectedNode.sort_order}</span>
                                                </div>
                                                <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg">
                                                    <span className="block text-xs text-gray-400">子主題數</span>
                                                    <span className="block font-semibold text-gray-700 mt-1">
                                                        {selectedNode.children?.length || 0}
                                                    </span>
                                                </div>
                                                <div className="border border-gray-100 dark:border-slate-700 p-3 rounded-lg">
                                                    <span className="block text-xs text-gray-400">狀態</span>
                                                    <span className="block font-semibold text-gray-700 mt-1">{selectedNode.status.toUpperCase()}</span>
                                                </div>
                                            </div>

                                            <div className="flex gap-3 pt-2">
                                                <button
                                                    onClick={() => setShowAddChildModal(true)}
                                                    className="btn-primary text-sm px-4 py-2.5 flex items-center gap-1.5"
                                                >
                                                    <Plus className="w-4 h-4" /> 新增子主題節點
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Content library mappings (Only for existing_site mode) */}
                                {currentProject.mode === 'existing_site' && (
                                    <div className="border-t border-gray-100 dark:border-slate-700 pt-6 space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2 text-sm">
                                                <FileText className="w-4 h-4 text-primary-600" />
                                                已映射的既有舊文章 ({mappedItemsForSelected.length})
                                            </h3>
                                        </div>

                                        {mappedItemsForSelected.length > 0 ? (
                                            <div className="space-y-2 max-h-[220px] overflow-y-auto pr-2">
                                                {mappedItemsForSelected.map(item => (
                                                    <div key={item.id} className="flex justify-between items-center p-3 bg-gray-50 dark:bg-slate-800 rounded-lg text-xs">
                                                        <div className="min-w-0 flex-1">
                                                            <p className="font-semibold text-gray-700 dark:text-gray-300 truncate">{item.title}</p>
                                                            {item.url && (
                                                                <a href={item.url} target="_blank" rel="noreferrer" className="text-primary-500 hover:underline block truncate mt-0.5">
                                                                    {item.url}
                                                                </a>
                                                            )}
                                                        </div>
                                                        <button
                                                            onClick={() => handleMapContentItem(item.id, null)}
                                                            className="text-red-500 hover:text-red-700 ml-4 font-medium"
                                                        >
                                                            解除映射
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-gray-400 text-xs italic">此主題目前沒有關聯的既有舊文章。</p>
                                        )}

                                        {/* Unmapped content selection mapping */}
                                        {unmappedItems.length > 0 && (
                                            <div className="bg-primary-50/30 dark:bg-primary-950/10 p-4 rounded-xl border border-primary-100 dark:border-primary-950/20 space-y-3">
                                                <h4 className="font-semibold text-gray-800 dark:text-gray-300 text-xs flex items-center gap-1.5">
                                                    快速映射未分類的文章到此主題：
                                                </h4>
                                                <div className="flex gap-2">
                                                    <select
                                                        id="unmapped-select"
                                                        className="input text-xs py-2 flex-1"
                                                        defaultValue=""
                                                        onChange={async (e) => {
                                                            const val = e.target.value
                                                            if (val) {
                                                                await handleMapContentItem(val, selectedNode.id)
                                                                e.target.value = "" // Reset select
                                                            }
                                                        }}
                                                    >
                                                        <option value="" disabled>-- 選擇要映射的未分類文章 --</option>
                                                        {unmappedItems.map(item => (
                                                            <option key={item.id} value={item.id}>{item.title}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="card text-center py-24 text-gray-400">
                                <GitFork className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                                <p className="text-sm">請選擇左側主題架構樹中的任何一個節點以查看其詳細資訊與關聯文章。</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Bulk Import Modal */}
            {showImportModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-xl">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">大量匯入既有舊文章</h2>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                            請在下方貼上既有的文章數據。每行一篇，格式為：<code>文章標題,網址</code>。
                        </p>
                        <textarea
                            value={importText}
                            onChange={(e) => setImportText(e.target.value)}
                            className="input text-xs font-mono"
                            rows={8}
                            placeholder="例如：&#10;Shopify 店面優化指南, https://example.com/shopify-tips&#10;電商 SEO 機制完整分析, https://example.com/ecommerce-seo"
                        />
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowImportModal(false)}
                                className="btn-secondary"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleBulkImport}
                                disabled={importing || !importText.trim()}
                                className="btn-primary"
                            >
                                {importing ? '匯入中...' : '確認匯入'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Root Pillar Modal */}
            {showAddRootModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-xl">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">新增核心主題 (Pillar)</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">主題名稱 *</label>
                                <input
                                    type="text"
                                    value={rootName}
                                    onChange={(e) => setRootName(e.target.value)}
                                    className="input"
                                    placeholder="例如：電商 SEO 行銷"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述說明</label>
                                <textarea
                                    value={rootDesc}
                                    onChange={(e) => setRootDesc(e.target.value)}
                                    className="input text-sm"
                                    rows={2}
                                    placeholder="簡述此核心主題的規劃想法..."
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">優先級</label>
                                    <select
                                        value={rootPriority}
                                        onChange={(e) => setRootPriority(e.target.value as any)}
                                        className="input"
                                    >
                                        <option value="high">High</option>
                                        <option value="medium">Medium</option>
                                        <option value="low">Low</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">漏斗階段</label>
                                    <select
                                        value={rootStage}
                                        onChange={(e) => setRootStage(e.target.value as any)}
                                        className="input"
                                    >
                                        <option value="awareness">Awareness</option>
                                        <option value="consideration">Consideration</option>
                                        <option value="decision">Decision</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowAddRootModal(false)}
                                className="btn-secondary"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleAddRoot}
                                disabled={!rootName.trim()}
                                className="btn-primary"
                            >
                                確認新增
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Child Node Modal */}
            {showAddChildModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-md shadow-xl">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                            新增子主題節點
                        </h2>
                        <p className="text-xs text-gray-400 mb-4">
                            新增至：<strong>{selectedNode?.name}</strong>
                        </p>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">主題名稱 *</label>
                                <input
                                    type="text"
                                    value={childName}
                                    onChange={(e) => setChildName(e.target.value)}
                                    className="input"
                                    placeholder="例如：Shopify 速度優化技巧"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">主題角色 *</label>
                                    <select
                                        value={childRole}
                                        onChange={(e) => setChildRole(e.target.value as any)}
                                        className="input"
                                    >
                                        <option value="supporting">支持副主題 (Supporting)</option>
                                        <option value="bridge">橋接內容 (Bridge)</option>
                                        <option value="comparison">對比評測 (Comparison)</option>
                                        <option value="decision">決策購買 (Decision)</option>
                                        <option value="faq">常見問答 (FAQ)</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">優先級</label>
                                    <select
                                        value={childPriority}
                                        onChange={(e) => setChildPriority(e.target.value as any)}
                                        className="input"
                                    >
                                        <option value="high">High</option>
                                        <option value="medium">Medium</option>
                                        <option value="low">Low</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">漏斗階段</label>
                                <select
                                    value={childStage}
                                    onChange={(e) => setChildStage(e.target.value as any)}
                                    className="input"
                                >
                                    <option value="awareness">Awareness</option>
                                    <option value="consideration">Consideration</option>
                                    <option value="decision">Decision</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述說明</label>
                                <textarea
                                    value={childDesc}
                                    onChange={(e) => setChildDesc(e.target.value)}
                                    className="input text-sm"
                                    rows={2}
                                    placeholder="簡述此子主題的規劃想法..."
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowAddChildModal(false)}
                                className="btn-secondary"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleAddChild}
                                disabled={!childName.trim()}
                                className="btn-primary"
                            >
                                確認新增
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default TopicMapPage
