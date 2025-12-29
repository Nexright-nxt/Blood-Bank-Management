import React, { useState, useEffect } from 'react';
import { userAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Users, Plus, Edit, Trash2, Shield, Key, Settings, Check, X, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Switch } from '../components/ui/switch';
import { Checkbox } from '../components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '../components/ui/alert-dialog';

const defaultRoles = [
  { value: 'admin', label: 'Administrator', color: 'bg-purple-100 text-purple-700' },
  { value: 'registration', label: 'Registration Staff', color: 'bg-blue-100 text-blue-700' },
  { value: 'phlebotomist', label: 'Phlebotomist', color: 'bg-red-100 text-red-700' },
  { value: 'lab_tech', label: 'Lab Technician', color: 'bg-amber-100 text-amber-700' },
  { value: 'processing', label: 'Processing Tech', color: 'bg-cyan-100 text-cyan-700' },
  { value: 'qc_manager', label: 'QC Manager', color: 'bg-emerald-100 text-emerald-700' },
  { value: 'inventory', label: 'Inventory Manager', color: 'bg-orange-100 text-orange-700' },
  { value: 'distribution', label: 'Distribution Staff', color: 'bg-pink-100 text-pink-700' },
];

const moduleCategories = {
  'Core': ['dashboard'],
  'Registration': ['donors', 'donor_requests', 'screening'],
  'Collection': ['collection'],
  'Laboratory': ['traceability', 'pre_lab_qc', 'laboratory'],
  'Processing': ['processing'],
  'Quality Control': ['qc_validation'],
  'Inventory': ['inventory', 'storage'],
  'Distribution': ['requests', 'distribution', 'logistics'],
  'Disposition': ['returns', 'discards'],
  'Analytics': ['reports'],
  'System': ['alerts'],
  'Admin': ['users'],
};

const moduleLabels = {
  dashboard: 'Dashboard',
  donors: 'Donor Management',
  donor_requests: 'Donor Requests',
  screening: 'Screening',
  collection: 'Collection',
  traceability: 'Traceability',
  pre_lab_qc: 'Pre-Lab QC',
  laboratory: 'Laboratory Testing',
  processing: 'Component Processing',
  qc_validation: 'QC Validation',
  inventory: 'Inventory',
  storage: 'Storage Management',
  requests: 'Blood Requests',
  distribution: 'Distribution',
  logistics: 'Logistics',
  returns: 'Returns',
  discards: 'Discards',
  reports: 'Reports',
  alerts: 'Alerts',
  users: 'User Management',
};

export default function UserManagement() {
  const { user: currentUser, register } = useAuth();
  const [users, setUsers] = useState([]);
  const [customRoles, setCustomRoles] = useState([]);
  const [defaultPermissions, setDefaultPermissions] = useState({});
  const [loading, setLoading] = useState(true);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingUserPermissions, setEditingUserPermissions] = useState(null);

  const [userForm, setUserForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'registration',
    is_active: true,
  });

  const [roleForm, setRoleForm] = useState({
    name: '',
    display_name: '',
    description: '',
    permissions: [],
  });

  const [selectedPermissions, setSelectedPermissions] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [usersRes, rolesRes] = await Promise.all([
        userAPI.getAll(),
        userAPI.getRoles()
      ]);
      setUsers(usersRes.data);
      setCustomRoles(rolesRes.data.custom_roles || []);
      setDefaultPermissions(rolesRes.data.default_permissions || {});
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const allRoles = [
    ...defaultRoles,
    ...customRoles.map(r => ({
      value: r.name,
      label: r.display_name,
      color: 'bg-indigo-100 text-indigo-700',
      isCustom: true,
      permissions: r.permissions
    }))
  ];

  const handleCreateUser = async () => {
    try {
      await register(userForm);
      toast.success('User created successfully');
      setShowUserDialog(false);
      resetUserForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    try {
      const updates = { ...userForm };
      if (!updates.password) delete updates.password;
      
      await userAPI.update(editingUser.id, updates);
      toast.success('User updated successfully');
      setShowUserDialog(false);
      resetUserForm();
      fetchData();
    } catch (error) {
      toast.error('Failed to update user');
    }
  };

  const handleDeleteUser = async (userId) => {
    try {
      await userAPI.delete(userId);
      toast.success('User deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete user');
    }
  };

  const handleToggleActive = async (user) => {
    try {
      await userAPI.update(user.id, { is_active: !user.is_active });
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update user status');
    }
  };

  const handleCreateRole = async () => {
    if (!roleForm.name || !roleForm.display_name || roleForm.permissions.length === 0) {
      toast.error('Please fill all required fields and select at least one permission');
      return;
    }

    try {
      await userAPI.createRole(roleForm);
      toast.success('Custom role created successfully');
      setShowRoleDialog(false);
      resetRoleForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create role');
    }
  };

  const handleDeleteRole = async (roleId) => {
    try {
      await userAPI.deleteRole(roleId);
      toast.success('Role deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete role');
    }
  };

  const handleUpdateUserPermissions = async () => {
    if (!editingUserPermissions) return;

    try {
      await userAPI.updatePermissions(editingUserPermissions.id, selectedPermissions);
      toast.success('User permissions updated');
      setShowPermissionDialog(false);
      setEditingUserPermissions(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to update permissions');
    }
  };

  const openEditDialog = (user) => {
    setEditingUser(user);
    setUserForm({
      full_name: user.full_name,
      email: user.email,
      password: '',
      role: user.role,
      is_active: user.is_active,
    });
    setShowUserDialog(true);
  };

  const openPermissionDialog = (user) => {
    setEditingUserPermissions(user);
    setSelectedPermissions(user.custom_permissions || []);
    setShowPermissionDialog(true);
  };

  const resetUserForm = () => {
    setUserForm({
      full_name: '',
      email: '',
      password: '',
      role: 'registration',
      is_active: true,
    });
    setEditingUser(null);
  };

  const resetRoleForm = () => {
    setRoleForm({
      name: '',
      display_name: '',
      description: '',
      permissions: [],
    });
  };

  const toggleRolePermission = (permission) => {
    setRoleForm(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permission)
        ? prev.permissions.filter(p => p !== permission)
        : [...prev.permissions, permission]
    }));
  };

  const toggleUserPermission = (permission) => {
    setSelectedPermissions(prev => 
      prev.includes(permission)
        ? prev.filter(p => p !== permission)
        : [...prev, permission]
    );
  };

  const getRoleConfig = (role) => allRoles.find(r => r.value === role) || defaultRoles[1];

  const getRolePermissions = (role) => {
    if (role === 'admin') return ['*'];
    const customRole = customRoles.find(r => r.name === role);
    if (customRole) return customRole.permissions;
    return defaultPermissions[role] || [];
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="user-management-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="page-subtitle">Manage users, roles, and permissions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="roles">Roles & Permissions</TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4 mt-4">
          <div className="flex justify-between items-center">
            <div className="flex flex-wrap gap-2">
              {defaultRoles.slice(0, 4).map(role => (
                <Badge key={role.value} className={role.color}>
                  {role.label}
                </Badge>
              ))}
              <Badge className="bg-slate-100 text-slate-600">+{defaultRoles.length - 4} more</Badge>
            </div>
            <Button 
              onClick={() => { resetUserForm(); setShowUserDialog(true); }}
              className="bg-teal-600 hover:bg-teal-700"
              data-testid="add-user-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Users</CardTitle>
              <CardDescription>All registered users and their access roles</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No users found
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Custom Permissions</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => {
                      const roleConfig = getRoleConfig(user.role);
                      const hasCustomPermissions = user.custom_permissions && user.custom_permissions.length > 0;
                      return (
                        <TableRow key={user.id} className="data-table-row">
                          <TableCell className="font-medium">{user.full_name}</TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>
                            <Badge className={roleConfig.color}>
                              {roleConfig.label}
                              {roleConfig.isCustom && <span className="ml-1 text-xs">(Custom)</span>}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {hasCustomPermissions ? (
                              <Badge variant="outline" className="text-xs">
                                {user.custom_permissions.length} custom
                              </Badge>
                            ) : (
                              <span className="text-slate-400 text-sm">Default</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge className={user.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => openEditDialog(user)}
                                disabled={user.id === currentUser?.id}
                                title="Edit User"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => openPermissionDialog(user)}
                                disabled={user.role === 'admin'}
                                title="Manage Permissions"
                              >
                                <Key className="w-4 h-4 text-indigo-600" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleToggleActive(user)}
                                disabled={user.id === currentUser?.id}
                                title={user.is_active ? 'Deactivate' : 'Activate'}
                              >
                                <Shield className={`w-4 h-4 ${user.is_active ? 'text-emerald-600' : 'text-slate-400'}`} />
                              </Button>
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                    disabled={user.id === currentUser?.id}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>Delete User</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Are you sure you want to delete {user.full_name}? This action cannot be undone.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => handleDeleteUser(user.id)}
                                      className="bg-red-600 hover:bg-red-700"
                                    >
                                      Delete
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Roles & Permissions Tab */}
        <TabsContent value="roles" className="space-y-4 mt-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-500">
              Create custom roles with specific module permissions
            </p>
            <Button 
              onClick={() => { resetRoleForm(); setShowRoleDialog(true); }}
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="create-role-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Custom Role
            </Button>
          </div>

          {/* Default Roles */}
          <Card>
            <CardHeader>
              <CardTitle>Default Roles</CardTitle>
              <CardDescription>System-defined roles with predefined permissions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {defaultRoles.map(role => (
                  <div key={role.value} className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className={role.color}>{role.label}</Badge>
                    </div>
                    <div className="text-xs text-slate-500">
                      {role.value === 'admin' ? (
                        <span className="text-purple-600 font-medium">Full Access</span>
                      ) : (
                        <span>
                          {(defaultPermissions[role.value] || []).length} modules
                        </span>
                      )}
                    </div>
                    {role.value !== 'admin' && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {(defaultPermissions[role.value] || []).slice(0, 3).map(perm => (
                          <Badge key={perm} variant="outline" className="text-xs">
                            {moduleLabels[perm] || perm}
                          </Badge>
                        ))}
                        {(defaultPermissions[role.value] || []).length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{(defaultPermissions[role.value] || []).length - 3}
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Custom Roles */}
          <Card>
            <CardHeader>
              <CardTitle>Custom Roles</CardTitle>
              <CardDescription>Admin-created roles with custom permissions</CardDescription>
            </CardHeader>
            <CardContent>
              {customRoles.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Settings className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No custom roles created yet</p>
                  <p className="text-sm">Click "Create Custom Role" to add one</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Role Name</TableHead>
                      <TableHead>Display Name</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Permissions</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {customRoles.map((role) => (
                      <TableRow key={role.id} className="data-table-row">
                        <TableCell className="font-mono text-sm">{role.name}</TableCell>
                        <TableCell>
                          <Badge className="bg-indigo-100 text-indigo-700">
                            {role.display_name}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 max-w-48 truncate">
                          {role.description || '-'}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {role.permissions.slice(0, 2).map(perm => (
                              <Badge key={perm} variant="outline" className="text-xs">
                                {moduleLabels[perm] || perm}
                              </Badge>
                            ))}
                            {role.permissions.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{role.permissions.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete Custom Role</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete the "{role.display_name}" role? 
                                  Users with this role will need to be reassigned.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDeleteRole(role.id)}
                                  className="bg-red-600 hover:bg-red-700"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add/Edit User Dialog */}
      <Dialog open={showUserDialog} onOpenChange={(open) => { setShowUserDialog(open); if (!open) resetUserForm(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-teal-600" />
              {editingUser ? 'Edit User' : 'Add New User'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Full Name *</Label>
              <Input
                value={userForm.full_name}
                onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                placeholder="Enter full name"
                data-testid="input-full-name"
              />
            </div>

            <div className="space-y-2">
              <Label>Email *</Label>
              <Input
                type="email"
                value={userForm.email}
                onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                placeholder="Enter email"
                disabled={!!editingUser}
                data-testid="input-email"
              />
            </div>

            <div className="space-y-2">
              <Label>{editingUser ? 'New Password (leave blank to keep current)' : 'Password *'}</Label>
              <Input
                type="password"
                value={userForm.password}
                onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                placeholder={editingUser ? 'Enter new password' : 'Enter password'}
                data-testid="input-password"
              />
            </div>

            <div className="space-y-2">
              <Label>Role *</Label>
              <Select 
                value={userForm.role}
                onValueChange={(v) => setUserForm({ ...userForm, role: v })}
              >
                <SelectTrigger data-testid="select-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {allRoles.map(role => (
                    <SelectItem key={role.value} value={role.value}>
                      <div className="flex items-center gap-2">
                        {role.label}
                        {role.isCustom && <Badge className="text-xs">Custom</Badge>}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {editingUser && (
              <div className="flex items-center justify-between py-2">
                <Label>Active Status</Label>
                <Switch
                  checked={userForm.is_active}
                  onCheckedChange={(checked) => setUserForm({ ...userForm, is_active: checked })}
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowUserDialog(false); resetUserForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={editingUser ? handleUpdateUser : handleCreateUser}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={!userForm.full_name || !userForm.email || (!editingUser && !userForm.password)}
              data-testid="submit-user-btn"
            >
              {editingUser ? 'Update User' : 'Create User'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Custom Role Dialog */}
      <Dialog open={showRoleDialog} onOpenChange={(open) => { setShowRoleDialog(open); if (!open) resetRoleForm(); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-indigo-600" />
              Create Custom Role
            </DialogTitle>
            <DialogDescription>
              Define a new role with specific module permissions
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Role Name (ID) *</Label>
                <Input
                  value={roleForm.name}
                  onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                  placeholder="e.g., senior_tech"
                  data-testid="input-role-name"
                />
                <p className="text-xs text-slate-500">Lowercase, no spaces</p>
              </div>
              <div className="space-y-2">
                <Label>Display Name *</Label>
                <Input
                  value={roleForm.display_name}
                  onChange={(e) => setRoleForm({ ...roleForm, display_name: e.target.value })}
                  placeholder="e.g., Senior Technician"
                  data-testid="input-role-display-name"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={roleForm.description}
                onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                placeholder="Describe what this role is for..."
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label>Module Permissions *</Label>
              <p className="text-sm text-slate-500 mb-3">Select modules this role can access</p>
              
              <div className="border rounded-lg p-4 space-y-4 max-h-64 overflow-y-auto">
                {Object.entries(moduleCategories).map(([category, modules]) => (
                  <div key={category}>
                    <p className="font-medium text-sm text-slate-700 mb-2">{category}</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {modules.map(mod => (
                        <div
                          key={mod}
                          className={`flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors ${
                            roleForm.permissions.includes(mod)
                              ? 'bg-indigo-50 border border-indigo-200'
                              : 'hover:bg-slate-50'
                          }`}
                          onClick={() => toggleRolePermission(mod)}
                        >
                          <Checkbox
                            checked={roleForm.permissions.includes(mod)}
                            onCheckedChange={() => toggleRolePermission(mod)}
                          />
                          <span className="text-sm">{moduleLabels[mod]}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {roleForm.permissions.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  <span className="text-sm text-slate-500">Selected:</span>
                  {roleForm.permissions.map(p => (
                    <Badge key={p} className="bg-indigo-100 text-indigo-700">
                      {moduleLabels[p]}
                      <button 
                        type="button"
                        onClick={() => toggleRolePermission(p)}
                        className="ml-1 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRoleDialog(false); resetRoleForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateRole}
              className="bg-indigo-600 hover:bg-indigo-700"
              disabled={!roleForm.name || !roleForm.display_name || roleForm.permissions.length === 0}
              data-testid="create-role-submit-btn"
            >
              Create Role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Permissions Dialog */}
      <Dialog open={showPermissionDialog} onOpenChange={setShowPermissionDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="w-5 h-5 text-indigo-600" />
              Manage User Permissions
            </DialogTitle>
            <DialogDescription>
              Override default role permissions for {editingUserPermissions?.full_name}
            </DialogDescription>
          </DialogHeader>
          
          {editingUserPermissions && (
            <div className="space-y-4 py-4">
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{editingUserPermissions.full_name}</p>
                    <p className="text-sm text-slate-500">Base Role: {getRoleConfig(editingUserPermissions.role).label}</p>
                  </div>
                  <Badge className={getRoleConfig(editingUserPermissions.role).color}>
                    {getRoleConfig(editingUserPermissions.role).label}
                  </Badge>
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  Default permissions: {getRolePermissions(editingUserPermissions.role).join(', ') || 'None'}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Custom Permissions Override</Label>
                <p className="text-sm text-slate-500 mb-3">
                  Add or remove specific permissions for this user (overrides role defaults)
                </p>
                
                <div className="border rounded-lg p-4 space-y-4 max-h-64 overflow-y-auto">
                  {Object.entries(moduleCategories).map(([category, modules]) => (
                    <div key={category}>
                      <p className="font-medium text-sm text-slate-700 mb-2">{category}</p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {modules.map(mod => (
                          <div
                            key={mod}
                            className={`flex items-center space-x-2 p-2 rounded cursor-pointer transition-colors ${
                              selectedPermissions.includes(mod)
                                ? 'bg-indigo-50 border border-indigo-200'
                                : 'hover:bg-slate-50'
                            }`}
                            onClick={() => toggleUserPermission(mod)}
                          >
                            <Checkbox
                              checked={selectedPermissions.includes(mod)}
                              onCheckedChange={() => toggleUserPermission(mod)}
                            />
                            <span className="text-sm">{moduleLabels[mod]}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowPermissionDialog(false); setEditingUserPermissions(null); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpdateUserPermissions}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Save Permissions
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
