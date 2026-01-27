import React, { useState, useEffect } from 'react';
import { 
  Shield, Plus, Edit, Trash2, Copy, Users, Check, X, 
  ChevronDown, ChevronUp, Search, AlertCircle 
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import api from '../lib/api';

const MODULE_LABELS = {
  dashboard: 'Dashboard',
  donors: 'Donors',
  donations: 'Donations',
  screening: 'Screening',
  laboratory: 'Laboratory',
  processing: 'Processing',
  qc_validation: 'QC Validation',
  inventory: 'Inventory',
  requests: 'Blood Requests',
  distribution: 'Distribution',
  logistics: 'Logistics',
  returns: 'Returns',
  discards: 'Discards',
  reports: 'Reports',
  users: 'User Management',
  organizations: 'Organizations',
  roles: 'Roles',
  configuration: 'Configuration',
  audit_logs: 'Audit Logs',
  storage: 'Storage',
  alerts: 'Alerts',
};

const ACTION_LABELS = {
  view: 'View',
  create: 'Create',
  edit: 'Edit',
  delete: 'Delete',
  verify: 'Verify',
  approve: 'Approve',
  reject: 'Reject',
  fulfill: 'Fulfill',
  move: 'Move',
  reserve: 'Reserve',
  transfer: 'Transfer',
  dispatch: 'Dispatch',
  deliver: 'Deliver',
  export: 'Export',
  manage: 'Manage',
};

export default function RolesManagement() {
  const [roles, setRoles] = useState([]);
  const [availableModules, setAvailableModules] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: {}
  });
  
  // Expanded modules for permission editing
  const [expandedModules, setExpandedModules] = useState({});

  useEffect(() => {
    loadRoles();
    loadAvailableModules();
  }, []);

  const loadRoles = async () => {
    try {
      const response = await api.get('/roles');
      setRoles(response.data);
    } catch (error) {
      toast.error('Failed to load roles');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableModules = async () => {
    try {
      const response = await api.get('/roles/available-modules');
      setAvailableModules(response.data.modules || {});
    } catch (error) {
      console.error('Failed to load modules:', error);
    }
  };

  const handleCreateRole = async () => {
    try {
      await api.post('/roles', formData);
      toast.success('Role created successfully');
      setShowCreateDialog(false);
      resetForm();
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create role');
    }
  };

  const handleUpdateRole = async () => {
    try {
      await api.put(`/roles/${selectedRole.id}`, formData);
      toast.success('Role updated successfully');
      setShowEditDialog(false);
      resetForm();
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleDeleteRole = async () => {
    try {
      await api.delete(`/roles/${selectedRole.id}`);
      toast.success('Role deleted successfully');
      setShowDeleteDialog(false);
      setSelectedRole(null);
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete role');
    }
  };

  const handleDuplicateRole = async (role) => {
    try {
      await api.post(`/roles/${role.id}/duplicate`);
      toast.success('Role duplicated successfully');
      loadRoles();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to duplicate role');
    }
  };

  const resetForm = () => {
    setFormData({ name: '', description: '', permissions: {} });
    setExpandedModules({});
    setSelectedRole(null);
  };

  const openEditDialog = (role) => {
    setSelectedRole(role);
    setFormData({
      name: role.name,
      description: role.description || '',
      permissions: { ...role.permissions }
    });
    setShowEditDialog(true);
  };

  const openViewDialog = (role) => {
    setSelectedRole(role);
    setShowViewDialog(true);
  };

  const toggleModuleExpansion = (module) => {
    setExpandedModules(prev => ({
      ...prev,
      [module]: !prev[module]
    }));
  };

  const togglePermission = (module, action) => {
    setFormData(prev => {
      const modulePerms = prev.permissions[module] || [];
      const hasAction = modulePerms.includes(action);
      
      let newModulePerms;
      if (hasAction) {
        newModulePerms = modulePerms.filter(a => a !== action);
      } else {
        newModulePerms = [...modulePerms, action];
      }
      
      const newPermissions = { ...prev.permissions };
      if (newModulePerms.length === 0) {
        delete newPermissions[module];
      } else {
        newPermissions[module] = newModulePerms;
      }
      
      return { ...prev, permissions: newPermissions };
    });
  };

  const toggleAllModuleActions = (module, actions) => {
    setFormData(prev => {
      const modulePerms = prev.permissions[module] || [];
      const allSelected = actions.every(a => modulePerms.includes(a));
      
      const newPermissions = { ...prev.permissions };
      if (allSelected) {
        delete newPermissions[module];
      } else {
        newPermissions[module] = [...actions];
      }
      
      return { ...prev, permissions: newPermissions };
    });
  };

  const filteredRoles = roles.filter(role => 
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const systemRoles = filteredRoles.filter(r => r.is_system_role);
  const customRoles = filteredRoles.filter(r => !r.is_system_role);

  const PermissionEditor = ({ permissions, readOnly = false }) => (
    <div className="space-y-2 max-h-[400px] overflow-y-auto">
      {Object.entries(availableModules).map(([module, actions]) => {
        const modulePerms = permissions[module] || [];
        const isExpanded = expandedModules[module] || readOnly;
        const hasAnyPermission = modulePerms.length > 0;
        
        return (
          <div key={module} className="border rounded-lg overflow-hidden">
            <div 
              className={`flex items-center justify-between p-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 ${
                hasAnyPermission ? 'bg-teal-50 dark:bg-teal-900/20' : ''
              }`}
              onClick={() => !readOnly && toggleModuleExpansion(module)}
            >
              <div className="flex items-center gap-2">
                {!readOnly && (
                  isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                )}
                <span className="font-medium">{MODULE_LABELS[module] || module}</span>
                {hasAnyPermission && (
                  <Badge variant="secondary" className="text-xs">
                    {modulePerms.length}/{actions.length}
                  </Badge>
                )}
              </div>
              {!readOnly && (
                <Checkbox
                  checked={actions.every(a => modulePerms.includes(a))}
                  onCheckedChange={() => toggleAllModuleActions(module, actions)}
                  onClick={(e) => e.stopPropagation()}
                />
              )}
            </div>
            
            {isExpanded && (
              <div className="p-3 pt-0 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {actions.map(action => (
                  <label 
                    key={action} 
                    className={`flex items-center gap-2 p-2 rounded ${
                      readOnly ? '' : 'cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700'
                    }`}
                  >
                    {readOnly ? (
                      modulePerms.includes(action) ? (
                        <Check className="w-4 h-4 text-green-500" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300" />
                      )
                    ) : (
                      <Checkbox
                        checked={modulePerms.includes(action)}
                        onCheckedChange={() => togglePermission(module, action)}
                      />
                    )}
                    <span className="text-sm">{ACTION_LABELS[action] || action}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-teal-600" />
            Roles & Permissions
          </h1>
          <p className="text-sm text-slate-500 mt-1">Manage user roles and access permissions</p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)} className="w-full sm:w-auto">
          <Plus className="w-4 h-4 mr-2" />
          Create Role
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="Search roles..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* System Roles */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600" />
            System Roles
            <Badge variant="secondary">{systemRoles.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-slate-500">
                  <th className="pb-3 font-medium">Role Name</th>
                  <th className="pb-3 font-medium hidden sm:table-cell">Description</th>
                  <th className="pb-3 font-medium text-center">Users</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {systemRoles.map(role => (
                  <tr key={role.id} className="border-b last:border-0">
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{role.name}</span>
                        <Badge variant="outline" className="text-xs">System</Badge>
                      </div>
                    </td>
                    <td className="py-3 text-sm text-slate-500 hidden sm:table-cell">
                      {role.description}
                    </td>
                    <td className="py-3 text-center">
                      <Badge variant="secondary">
                        <Users className="w-3 h-3 mr-1" />
                        {role.users_count}
                      </Badge>
                    </td>
                    <td className="py-3 text-right">
                      <Button variant="ghost" size="sm" onClick={() => openViewDialog(role)}>
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Custom Roles */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Edit className="w-5 h-5 text-teal-600" />
            Custom Roles
            <Badge variant="secondary">{customRoles.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {customRoles.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No custom roles created yet</p>
              <Button variant="outline" className="mt-4" onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Role
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-slate-500">
                    <th className="pb-3 font-medium">Role Name</th>
                    <th className="pb-3 font-medium hidden sm:table-cell">Description</th>
                    <th className="pb-3 font-medium text-center">Users</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {customRoles.map(role => (
                    <tr key={role.id} className="border-b last:border-0">
                      <td className="py-3">
                        <span className="font-medium">{role.name}</span>
                      </td>
                      <td className="py-3 text-sm text-slate-500 hidden sm:table-cell">
                        {role.description || '-'}
                      </td>
                      <td className="py-3 text-center">
                        <Badge variant="secondary">
                          <Users className="w-3 h-3 mr-1" />
                          {role.users_count}
                        </Badge>
                      </td>
                      <td className="py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => openViewDialog(role)}>
                            View
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => openEditDialog(role)}>
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDuplicateRole(role)}>
                            <Copy className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-500 hover:text-red-700"
                            onClick={() => {
                              setSelectedRole(role);
                              setShowDeleteDialog(true);
                            }}
                            disabled={role.users_count > 0}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Role Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Custom Role</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Role Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter role name"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter role description"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Permissions</label>
              <PermissionEditor permissions={formData.permissions} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCreateDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button onClick={handleCreateRole} disabled={!formData.name}>
              Create Role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Role Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Role: {selectedRole?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Role Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter role name"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter role description"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Permissions</label>
              <PermissionEditor permissions={formData.permissions} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowEditDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button onClick={handleUpdateRole} disabled={!formData.name}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Role Dialog */}
      <Dialog open={showViewDialog} onOpenChange={setShowViewDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedRole?.name}
              {selectedRole?.is_system_role && (
                <Badge variant="outline">System Role</Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          {selectedRole && (
            <div className="space-y-4">
              {selectedRole.description && (
                <p className="text-sm text-slate-500">{selectedRole.description}</p>
              )}
              <div>
                <label className="text-sm font-medium mb-2 block">Permissions</label>
                <PermissionEditor permissions={selectedRole.permissions} readOnly />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowViewDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Role</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the role "{selectedRole?.name}"? This action cannot be undone.
              {selectedRole?.users_count > 0 && (
                <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded flex items-center gap-2 text-amber-700 dark:text-amber-400">
                  <AlertCircle className="w-4 h-4" />
                  <span>This role has {selectedRole.users_count} user(s) assigned. Reassign them first.</span>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteRole}
              className="bg-red-600 hover:bg-red-700"
              disabled={selectedRole?.users_count > 0}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
