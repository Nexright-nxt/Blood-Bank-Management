import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  Users, CheckCircle, XCircle, Clock, Building2, Mail, Phone, MapPin,
  Search, Filter, RefreshCw, Eye, AlertTriangle, UserCheck, UserX
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const REQUESTOR_TYPES = {
  hospital: { label: 'Hospital', color: 'bg-blue-100 text-blue-700' },
  clinic: { label: 'Clinic', color: 'bg-green-100 text-green-700' },
  emergency_service: { label: 'Emergency Service', color: 'bg-red-100 text-red-700' },
  research_lab: { label: 'Research Lab', color: 'bg-purple-100 text-purple-700' },
  other: { label: 'Other', color: 'bg-slate-100 text-slate-700' }
};

const STATUS_STYLES = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
  suspended: { label: 'Suspended', color: 'bg-orange-100 text-orange-700', icon: AlertTriangle }
};

export default function RequestorManagement() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [requestors, setRequestors] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [stats, setStats] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  
  // Dialog states
  const [selectedRequestor, setSelectedRequestor] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [approvalAction, setApprovalAction] = useState('');
  const [approvalData, setApprovalData] = useState({
    associated_org_id: '',
    rejection_reason: ''
  });

  const api = axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}` }
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [requestorsRes, statsRes, orgsRes] = await Promise.all([
        api.get('/requestors'),
        api.get('/requestors/stats'),
        api.get('/organizations')
      ]);
      setRequestors(requestorsRes.data);
      setStats(statsRes.data);
      setOrganizations(orgsRes.data);
    } catch (error) {
      toast.error('Failed to load requestors');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReject = async () => {
    if (!selectedRequestor) return;
    
    if (approvalAction === 'approve' && !approvalData.associated_org_id) {
      toast.error('Please select an organization to associate');
      return;
    }
    if (approvalAction === 'reject' && !approvalData.rejection_reason) {
      toast.error('Please provide a rejection reason');
      return;
    }

    try {
      await api.put(`/requestors/${selectedRequestor.id}/approve`, {
        action: approvalAction,
        associated_org_id: approvalData.associated_org_id || undefined,
        rejection_reason: approvalData.rejection_reason || undefined
      });
      toast.success(approvalAction === 'approve' ? 'Requestor approved successfully' : 'Requestor rejected');
      setShowApprovalDialog(false);
      setSelectedRequestor(null);
      setApprovalData({ associated_org_id: '', rejection_reason: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Action failed');
    }
  };

  const handleSuspend = async (requestor) => {
    const reason = prompt('Enter suspension reason:');
    if (!reason) return;

    try {
      await api.put(`/requestors/${requestor.id}/suspend?reason=${encodeURIComponent(reason)}`);
      toast.success('Requestor suspended');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to suspend');
    }
  };

  const handleReactivate = async (requestor) => {
    try {
      await api.put(`/requestors/${requestor.id}/reactivate`);
      toast.success('Requestor reactivated');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reactivate');
    }
  };

  const openApprovalDialog = (requestor, action) => {
    setSelectedRequestor(requestor);
    setApprovalAction(action);
    setShowApprovalDialog(true);
  };

  const filteredRequestors = requestors.filter(r => {
    const matchesSearch = !searchTerm || 
      r.organization_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.contact_person?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || r.status === filterStatus;
    const matchesType = filterType === 'all' || r.requestor_type === filterType;
    return matchesSearch && matchesStatus && matchesType;
  });

  const pendingRequestors = requestors.filter(r => r.status === 'pending');

  return (
    <div className="p-6 space-y-6" data-testid="requestor-management">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Requestor Management</h1>
          <p className="text-slate-600">Manage external blood requestor registrations</p>
        </div>
        <Button variant="outline" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Pending</p>
                <p className="text-xl font-bold text-slate-800">{stats.pending || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Approved</p>
                <p className="text-xl font-bold text-slate-800">{stats.approved || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <XCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Rejected</p>
                <p className="text-xl font-bold text-slate-800">{stats.rejected || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-100 rounded-lg">
                <Users className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-xl font-bold text-slate-800">{stats.total || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approval Alert */}
      {pendingRequestors.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <span className="font-medium text-yellow-800">
                {pendingRequestors.length} requestor(s) awaiting approval
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search by name, email, contact..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
            data-testid="search-input"
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40" data-testid="status-filter">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {Object.entries(REQUESTOR_TYPES).map(([value, { label }]) => (
              <SelectItem key={value} value={value}>{label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Requestors Table */}
      <Card>
        <CardHeader>
          <CardTitle>Requestors</CardTitle>
          <CardDescription>
            {filteredRequestors.length} requestor(s) found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Organization</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registered</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRequestors.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                    No requestors found
                  </TableCell>
                </TableRow>
              ) : (
                filteredRequestors.map((requestor) => {
                  const statusConfig = STATUS_STYLES[requestor.status] || STATUS_STYLES.pending;
                  const typeConfig = REQUESTOR_TYPES[requestor.requestor_type] || REQUESTOR_TYPES.other;
                  
                  return (
                    <TableRow key={requestor.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{requestor.organization_name}</p>
                          <p className="text-sm text-slate-500">{requestor.city}, {requestor.state}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <p>{requestor.contact_person}</p>
                          <p className="text-slate-500">{requestor.email}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={typeConfig.color}>{typeConfig.label}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusConfig.color}>
                          <statusConfig.icon className="w-3 h-3 mr-1" />
                          {statusConfig.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-slate-500">
                        {new Date(requestor.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedRequestor(requestor);
                              setShowDetailDialog(true);
                            }}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {requestor.status === 'pending' && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-green-600"
                                onClick={() => openApprovalDialog(requestor, 'approve')}
                                data-testid={`approve-btn-${requestor.id}`}
                              >
                                <UserCheck className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-600"
                                onClick={() => openApprovalDialog(requestor, 'reject')}
                                data-testid={`reject-btn-${requestor.id}`}
                              >
                                <UserX className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                          {requestor.status === 'approved' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-orange-600"
                              onClick={() => handleSuspend(requestor)}
                            >
                              <AlertTriangle className="w-4 h-4" />
                            </Button>
                          )}
                          {requestor.status === 'suspended' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-green-600"
                              onClick={() => handleReactivate(requestor)}
                            >
                              <CheckCircle className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Requestor Details</DialogTitle>
          </DialogHeader>
          {selectedRequestor && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-500">Organization</Label>
                  <p className="font-medium">{selectedRequestor.organization_name}</p>
                </div>
                <div>
                  <Label className="text-slate-500">Type</Label>
                  <Badge className={REQUESTOR_TYPES[selectedRequestor.requestor_type]?.color}>
                    {REQUESTOR_TYPES[selectedRequestor.requestor_type]?.label}
                  </Badge>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-500">Contact Person</Label>
                  <p className="font-medium">{selectedRequestor.contact_person}</p>
                </div>
                <div>
                  <Label className="text-slate-500">Phone</Label>
                  <p className="font-medium">{selectedRequestor.phone}</p>
                </div>
              </div>
              <div>
                <Label className="text-slate-500">Email</Label>
                <p className="font-medium">{selectedRequestor.email}</p>
              </div>
              <div>
                <Label className="text-slate-500">Address</Label>
                <p className="font-medium">{selectedRequestor.address}</p>
                <p className="text-sm text-slate-500">
                  {selectedRequestor.city}, {selectedRequestor.state} - {selectedRequestor.pincode}
                </p>
              </div>
              {selectedRequestor.license_number && (
                <div>
                  <Label className="text-slate-500">License Number</Label>
                  <p className="font-medium">{selectedRequestor.license_number}</p>
                </div>
              )}
              {selectedRequestor.registration_number && (
                <div>
                  <Label className="text-slate-500">Registration Number</Label>
                  <p className="font-medium">{selectedRequestor.registration_number}</p>
                </div>
              )}
              {selectedRequestor.notes && (
                <div>
                  <Label className="text-slate-500">Notes</Label>
                  <p className="text-sm">{selectedRequestor.notes}</p>
                </div>
              )}
              {selectedRequestor.rejection_reason && (
                <div className="bg-red-50 p-3 rounded-lg">
                  <Label className="text-red-600">Rejection Reason</Label>
                  <p className="text-sm">{selectedRequestor.rejection_reason}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Approval Dialog */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalAction === 'approve' ? 'Approve Requestor' : 'Reject Requestor'}
            </DialogTitle>
            <DialogDescription>
              {approvalAction === 'approve' 
                ? 'Select an organization to associate this requestor with.'
                : 'Provide a reason for rejection.'}
            </DialogDescription>
          </DialogHeader>
          {selectedRequestor && (
            <div className="space-y-4">
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="font-medium">{selectedRequestor.organization_name}</p>
                <p className="text-sm text-slate-500">{selectedRequestor.email}</p>
              </div>
              
              {approvalAction === 'approve' ? (
                <div>
                  <Label>Associated Organization *</Label>
                  <Select
                    value={approvalData.associated_org_id}
                    onValueChange={(v) => setApprovalData({ ...approvalData, associated_org_id: v })}
                  >
                    <SelectTrigger data-testid="org-select">
                      <SelectValue placeholder="Select organization" />
                    </SelectTrigger>
                    <SelectContent>
                      {organizations.map((org) => (
                        <SelectItem key={org.id} value={org.id}>
                          {org.org_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-slate-500 mt-1">
                    The requestor will be able to request blood from this organization.
                  </p>
                </div>
              ) : (
                <div>
                  <Label>Rejection Reason *</Label>
                  <Textarea
                    value={approvalData.rejection_reason}
                    onChange={(e) => setApprovalData({ ...approvalData, rejection_reason: e.target.value })}
                    placeholder="Explain why the registration is being rejected..."
                    data-testid="rejection-reason"
                  />
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApprovalDialog(false)}>Cancel</Button>
            <Button
              className={approvalAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              onClick={handleApproveReject}
              data-testid="confirm-action-btn"
            >
              {approvalAction === 'approve' ? 'Approve' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
