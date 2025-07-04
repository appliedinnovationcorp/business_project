'use client';

import { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface WorkflowBuilderProps {
  workflow?: any;
  onSave: (workflowData: any) => void;
  onCancel: () => void;
}

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Start' },
    position: { x: 250, y: 25 },
  },
];

const initialEdges: Edge[] = [];

const nodeTypes = [
  { type: 'textract', label: 'Document Analysis', color: 'bg-blue-500' },
  { type: 'comprehend', label: 'Text Analysis', color: 'bg-green-500' },
  { type: 'rekognition', label: 'Image Analysis', color: 'bg-purple-500' },
  { type: 'lambda', label: 'Custom Function', color: 'bg-orange-500' },
  { type: 'condition', label: 'Condition', color: 'bg-yellow-500' },
  { type: 'output', label: 'Output', color: 'bg-red-500' },
];

export default function WorkflowBuilder({ workflow, onSave, onCancel }: WorkflowBuilderProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [selectedNodeType, setSelectedNodeType] = useState('');

  useEffect(() => {
    if (workflow) {
      setWorkflowName(workflow.name);
      setWorkflowDescription(workflow.description);
      if (workflow.nodes) setNodes(workflow.nodes);
      if (workflow.edges) setEdges(workflow.edges);
    }
  }, [workflow, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addNode = (type: string) => {
    const newNode: Node = {
      id: `${nodes.length + 1}`,
      type: type === 'output' ? 'output' : 'default',
      data: { 
        label: nodeTypes.find(nt => nt.type === type)?.label || type,
        nodeType: type
      },
      position: { x: Math.random() * 400, y: Math.random() * 400 },
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const handleSave = () => {
    if (!workflowName.trim()) {
      alert('Please enter a workflow name');
      return;
    }

    const workflowData = {
      name: workflowName,
      description: workflowDescription,
      nodes: nodes,
      edges: edges,
      status: 'draft'
    };

    onSave(workflowData);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-900">
                {workflow ? 'Edit Workflow' : 'Create Workflow'}
              </h1>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Workflow name"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="text"
                  placeholder="Description"
                  value={workflowDescription}
                  onChange={(e) => setWorkflowDescription(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={onCancel}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                Save Workflow
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-sm border-r">
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Add Components</h3>
            <div className="space-y-2">
              {nodeTypes.map((nodeType) => (
                <button
                  key={nodeType.type}
                  onClick={() => addNode(nodeType.type)}
                  className={`w-full text-left px-3 py-2 text-sm rounded-md text-white ${nodeType.color} hover:opacity-80`}
                >
                  {nodeType.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 border-t">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Instructions</h3>
            <div className="text-xs text-gray-600 space-y-2">
              <p>• Drag components from the sidebar</p>
              <p>• Connect nodes by dragging from output to input</p>
              <p>• Click nodes to configure them</p>
              <p>• Use the controls to zoom and pan</p>
            </div>
          </div>
        </div>

        {/* Main Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
