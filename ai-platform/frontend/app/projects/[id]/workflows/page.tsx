'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import WorkflowBuilder from '../../../../components/WorkflowBuilder';

interface Workflow {
  id: number;
  name: string;
  description: string;
  status: string;
  created_at: string;
  nodes: any[];
  edges: any[];
}

export default function WorkflowsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [showBuilder, setShowBuilder] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchWorkflows(token);
  }, [projectId, router]);

  const fetchWorkflows = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/workflows`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setWorkflows(data);
      } else {
        setError('Failed to load workflows');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = () => {
    setSelectedWorkflow(null);
    setShowBuilder(true);
  };

  const handleEditWorkflow = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setShowBuilder(true);
  };

  const handleSaveWorkflow = async (workflowData: any) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const url = selectedWorkflow 
        ? `${process.env.NEXT_PUBLIC_API_URL}/workflows/${selectedWorkflow.id}`
        : `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/workflows`;
      
      const method = selectedWorkflow ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(workflowData),
      });

      if (response.ok) {
        setShowBuilder(false);
        fetchWorkflows(token);
      } else {
        setError('Failed to save workflow');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleExecuteWorkflow = async (workflowId: number) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        alert('Workflow execution started!');
        fetchWorkflows(token);
      } else {
        setError('Failed to execute workflow');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (showBuilder) {
    return (
      <WorkflowBuilder
        workflow={selectedWorkflow}
        onSave={handleSaveWorkflow}
        onCancel={() => setShowBuilder(false)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-xl font-semibold text-gray-900">
                AI Platform
              </Link>
              <span className="mx-2 text-gray-400">/</span>
              <Link href={`/projects/${projectId}`} className="text-gray-600 hover:text-gray-900">
                Project
              </Link>
              <span className="mx-2 text-gray-400">/</span>
              <span className="text-gray-900">Workflows</span>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleCreateWorkflow}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Create Workflow
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Workflows</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Manage your AI automation workflows
            </p>
          </div>
          <ul className="divide-y divide-gray-200">
            {workflows.length === 0 ? (
              <li className="px-4 py-4 text-center text-gray-500">
                No workflows yet.{' '}
                <button
                  onClick={handleCreateWorkflow}
                  className="text-blue-600 hover:text-blue-500"
                >
                  Create your first workflow
                </button>
              </li>
            ) : (
              workflows.map((workflow) => (
                <li key={workflow.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                            <span className="text-purple-600 font-medium text-sm">
                              {workflow.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{workflow.name}</div>
                          <div className="text-sm text-gray-500">{workflow.description}</div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          workflow.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : workflow.status === 'running'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {workflow.status}
                        </span>
                        <button
                          onClick={() => handleEditWorkflow(workflow)}
                          className="text-blue-600 hover:text-blue-500 text-sm font-medium"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleExecuteWorkflow(workflow.id)}
                          className="text-green-600 hover:text-green-500 text-sm font-medium"
                        >
                          Execute
                        </button>
                        <div className="text-sm text-gray-500">
                          {new Date(workflow.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
