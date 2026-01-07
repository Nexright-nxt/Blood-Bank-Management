import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  History, RefreshCw, Filter, Download, Eye, Search,
  User, Clock, Activity, AlertTriangle, Shield, ChevronLeft,
  ChevronRight, Calendar, FileText, Building2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const ACTION_COLORS = {
  create: 'bg-green-100 text-green-700',
  update: 'bg-blue-100 text-blue-700',
  delete: 'bg-red-100 text-red-700',
  login: 'bg-teal-100 text-teal-700',
  logout: 'bg-slate-100 text-slate-700',
  login_failed: 'bg-red-100 text-red-700',
  approve: 'bg-emerald-100 text-emerald-700',
  reject: 'bg-orange-100 text-orange-700',
  transfer: 'bg-indigo-100 text-indigo-700',
  switch_context: 'bg-purple-100 text-purple-700',
  account_locked: 'bg-red-100 text-red-700',
  permission_denied: 'bg-amber-100 text-amber-700'
};

export default function AuditLogs() {
  const { user, isSystemAdmin, isSuperAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [securityEvents, setSecurityEvents] = useState(null);
  const [actionTypes, setActionTypes] = useState([]);
  const [moduleTypes, setModuleTypes] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;
  
  // Filters
  const [filters, setFilters] = useState({
    action: '',
    module: '',
    user_id: '',
    start_date: '',
    end_date: '',
    search: ''
  });

  useEffect(() => {
    fetchData();
    fetchFilterOptions();
  }, []);

  useEffect(() => {
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filters]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, securityRes] = await Promise.all([
        api.get('/audit-logs/summary', { params: { days: 7 } }),
        api.get('/audit-logs/security-events', { params: { days: 7 } })
      ]);
      setSummary(summaryRes.data);
      setSecurityEvents(securityRes.data);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const params = {
        page,
        page_size: pageSize,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v && v !== 'all')
        )
      };
      
      const res = await api.get('/audit-logs', { params });
      setLogs(res.data.logs);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);
    } catch (error) {
      toast.error('Failed to fetch audit logs');
    }
  };

  const fetchFilterOptions = async () => {
    try {
      const [actionsRes, modulesRes] = await Promise.all([
        api.get('/audit-logs/actions/list'),
        api.get('/audit-logs/modules/list')
      ]);
      setActionTypes(actionsRes.data);
      setModuleTypes(modulesRes.data);
    } catch (error) {
      console.error('Failed to fetch filter options:', error);
    }
  };

  const handleExport = async () => {
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v && v !== 'all')
      );
      
      const res = await api.get('/audit-logs/export/csv', { 
        params,
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Export started');
    } catch (error) {
      toast.error('Failed to export audit logs');
    }
  };

  const viewLogDetail = async (log) => {
    try {
      const res = await api.get(`/audit-logs/${log.id}`);
      setSelectedLog(res.data);
      setShowDetailDialog(true);
    } catch (error) {
      toast.error('Failed to fetch log details');
    }
  };

  const resetFilters = () => {
    setFilters({
      action: '',
      module: '',
      user_id: '',
      start_date: '',
      end_date: '',
      search: ''
    });
    setPage(1);
  };

  const getActionBadge = (action) => {
    const color = ACTION_COLORS[action] || 'bg-slate-100 text-slate-700';
    return <Badge className={color}>{action?.replace('_', ' ')}</Badge>;
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString()
    };
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <History className="w-8 h-8 text-teal-600" />
            Audit Logs
          </h1>
          <p className="page-subtitle">Track all system activities and changes</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Logs (7d)</p>
                  <p className="text-2xl font-bold">{summary.total_logs}</p>
                </div>
                <Activity className="w-8 h-8 text-teal-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Creates</p>
                  <p className="text-2xl font-bold text-green-600">
                    {summary.actions_breakdown?.create || 0}
                  </p>
                </div>
                <FileText className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Updates</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {summary.actions_breakdown?.update || 0}
                  </p>
                </div>
                <FileText className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Logins</p>
                  <p className="text-2xl font-bold text-teal-600">
                    {summary.actions_breakdown?.login || 0}
                  </p>
                </div>
                <User className="w-8 h-8 text-teal-500" />
              </div>
            </CardContent>
          </Card>
          <Card className={securityEvents?.total_events > 0 ? 'border-red-200 bg-red-50' : ''}>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Security Events</p>
                  <p className={`text-2xl font-bold ${securityEvents?.total_events > 0 ? 'text-red-600' : ''}`}>
                    {securityEvents?.total_events || 0}
                  </p>
                </div>
                <Shield className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium">Filters:</span>
            </div>
            
            <div className="w-40">
              <Select value={filters.action} onValueChange={(v) => setFilters({ ...filters, action: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="All Actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  {actionTypes.map(a => (
                    <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-40">
              <Select value={filters.module} onValueChange={(v) => setFilters({ ...filters, module: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="All Modules" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Modules</SelectItem>
                  {moduleTypes.map(m => (
                    <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-40">
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                placeholder="Start Date"
              />
            </div>
            
            <div className="w-40">
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                placeholder="End Date"
              />
            </div>
            
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  className="pl-10"
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  placeholder="Search by description, user, record ID..."
                />
              </div>
            </div>
            
            <Button variant="ghost" onClick={resetFilters}>
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Logs</CardTitle>
          <CardDescription>
            Showing {logs.length} of {total} logs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Module</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map(log => {
                const ts = formatTimestamp(log.timestamp);
                return (
                  <TableRow key={log.id}>
                    <TableCell>
                      <div className="text-sm">{ts.date}</div>
                      <div className="text-xs text-slate-500">{ts.time}</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <div>
                          <div className="font-medium">{log.user_name || 'Unknown'}</div>
                          <div className="text-xs text-slate-500">{log.user_type}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {log.org_name && (
                        <div className="flex items-center gap-1">
                          <Building2 className="w-3 h-3 text-slate-400" />
                          <span className="text-sm">{log.org_name}</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{getActionBadge(log.action)}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{log.module}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="max-w-xs truncate">{log.description}</div>
                      {log.record_id && (
                        <div className="text-xs text-slate-500 font-mono">
                          {log.record_id.slice(0, 12)}...
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-xs font-mono">{log.ip_address}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={() => viewLogDetail(log)}>
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
              {logs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-slate-500">
                    <History className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                    No audit logs found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-slate-500">
                Page {page} of {totalPages}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Audit Log Details</DialogTitle>
            <DialogDescription>Complete audit trail entry</DialogDescription>
          </DialogHeader>
          
          {selectedLog && (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-sm text-slate-500">Timestamp</p>
                  <p className="font-medium">{new Date(selectedLog.timestamp).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Action</p>
                  {getActionBadge(selectedLog.action)}
                </div>
                <div>
                  <p className="text-sm text-slate-500">Module</p>
                  <Badge variant="outline">{selectedLog.module}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Record ID</p>
                  <p className="font-mono text-sm">{selectedLog.record_id || '-'}</p>
                </div>
              </div>
              
              {/* User Info */}
              <div className="p-4 border rounded-lg">
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <User className="w-4 h-4" />
                  User Information
                </h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500">Name: </span>
                    <span>{selectedLog.user_name}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Email: </span>
                    <span>{selectedLog.user_email}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Type: </span>
                    <span>{selectedLog.user_type}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">IP: </span>
                    <span className="font-mono">{selectedLog.ip_address}</span>
                  </div>
                </div>
                {selectedLog.context_info && (
                  <div className="mt-2 p-2 bg-purple-50 rounded text-sm text-purple-700">
                    {selectedLog.context_info}
                  </div>
                )}
              </div>
              
              {/* Description */}
              <div>
                <p className="text-sm text-slate-500 mb-1">Description</p>
                <p>{selectedLog.description}</p>
              </div>
              
              {/* Old vs New Values */}
              {(selectedLog.old_values || selectedLog.new_values) && (
                <div className="grid grid-cols-2 gap-4">
                  {selectedLog.old_values && (
                    <div>
                      <p className="text-sm font-medium text-red-600 mb-2">Previous Values</p>
                      <pre className="p-3 bg-red-50 rounded-lg text-xs overflow-x-auto">
                        {JSON.stringify(selectedLog.old_values, null, 2)}
                      </pre>
                    </div>
                  )}
                  {selectedLog.new_values && (
                    <div>
                      <p className="text-sm font-medium text-green-600 mb-2">New Values</p>
                      <pre className="p-3 bg-green-50 rounded-lg text-xs overflow-x-auto">
                        {JSON.stringify(selectedLog.new_values, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
              
              {/* Organization Info */}
              {selectedLog.org_info && (
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Building2 className="w-4 h-4" />
                    Organization
                  </h4>
                  <p>{selectedLog.org_info.org_name} ({selectedLog.org_info.org_type})</p>
                </div>
              )}
              
              {/* Request Info */}
              <div className="text-xs text-slate-500 pt-2 border-t">
                <p>Request: {selectedLog.request_method} {selectedLog.request_path}</p>
                <p className="truncate">User Agent: {selectedLog.user_agent}</p>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
