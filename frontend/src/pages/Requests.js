import React, { useState, useEffect } from 'react';
import { requestAPI, inventoryAPI } from '../lib/api';
import { toast } from 'sonner';
import { ClipboardList, Plus, Check, X, Search, Clock } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const productTypes = [
  { value: 'whole_blood', label: 'Whole Blood' },
  { value: 'prc', label: 'Packed Red Cells' },
  { value: 'plasma', label: 'Plasma' },
  { value: 'ffp', label: 'Fresh Frozen Plasma' },
  { value: 'platelets', label: 'Platelets' },
  { value: 'cryoprecipitate', label: 'Cryoprecipitate' },
];

export default function Requests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');

  const [form, setForm] = useState({
    request_type: 'internal',
    requester_name: '',
    requester_contact: '',
    hospital_name: '',
    patient_name: '',
    patient_id: '',
    blood_group: '',
    product_type: '',
    quantity: '',
    urgency: 'normal',
    requested_date: new Date().toISOString().split('T')[0],
    required_by_date: '',
    notes: '',
  });

  useEffect(() => {
    fetchRequests();
  }, [statusFilter]);

  const fetchRequests = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await requestAPI.getAll(params);
      setRequests(response.data);
    } catch (error) {
      toast.error('Failed to fetch requests');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRequest = async () => {
    try {
      const response = await requestAPI.create({
        ...form,
        quantity: parseInt(form.quantity),
      });
      toast.success(`Request created: ${response.data.request_id}`);
      setShowNewDialog(false);
      resetForm();
      fetchRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create request');
    }
  };

  const handleApprove = async (id) => {
    try {
      await requestAPI.approve(id);
      toast.success('Request approved');
      fetchRequests();
    } catch (error) {
      toast.error('Failed to approve request');
    }
  };

  const handleReject = async (id) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;
    
    try {
      await requestAPI.reject(id, reason);
      toast.success('Request rejected');
      fetchRequests();
    } catch (error) {
      toast.error('Failed to reject request');
    }
  };

  const resetForm = () => {
    setForm({
      request_type: 'internal',
      requester_name: '',
      requester_contact: '',
      hospital_name: '',
      patient_name: '',
      patient_id: '',
      blood_group: '',
      product_type: '',
      quantity: '',
      urgency: 'normal',
      requested_date: new Date().toISOString().split('T')[0],
      required_by_date: '',
      notes: '',
    });
  };

  const statusColors = {
    pending: 'bg-amber-100 text-amber-700',
    approved: 'bg-emerald-100 text-emerald-700',
    fulfilled: 'bg-blue-100 text-blue-700',
    rejected: 'bg-red-100 text-red-700',
  };

  const urgencyColors = {
    normal: 'bg-slate-100 text-slate-700',
    urgent: 'bg-orange-100 text-orange-700',
    emergency: 'bg-red-100 text-red-700',
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="requests-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Blood Requests</h1>
          <p className="page-subtitle">Manage internal and external blood requests</p>
        </div>
        <Button 
          onClick={() => setShowNewDialog(true)}
          className="bg-teal-600 hover:bg-teal-700"
          data-testid="new-request-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Request
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Total Requests</p>
            <p className="text-2xl font-bold">{requests.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat border-l-4 border-l-amber-500">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Pending</p>
            <p className="text-2xl font-bold text-amber-600">
              {requests.filter(r => r.status === 'pending').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat border-l-4 border-l-emerald-500">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Approved</p>
            <p className="text-2xl font-bold text-emerald-600">
              {requests.filter(r => r.status === 'approved').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat border-l-4 border-l-blue-500">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Fulfilled</p>
            <p className="text-2xl font-bold text-blue-600">
              {requests.filter(r => r.status === 'fulfilled').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48" data-testid="status-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="fulfilled">Fulfilled</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle>Blood Requests</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
            </div>
          ) : requests.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No requests found
            </div>
          ) : (
            <Table className="table-dense">
              <TableHeader>
                <TableRow>
                  <TableHead>Request ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Blood Group</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead>Urgency</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((req) => (
                  <TableRow key={req.id} className="data-table-row">
                    <TableCell className="font-mono">{req.request_id}</TableCell>
                    <TableCell className="capitalize">{req.request_type}</TableCell>
                    <TableCell>
                      <span className="blood-group-badge">{req.blood_group}</span>
                    </TableCell>
                    <TableCell className="capitalize">{req.product_type?.replace('_', ' ')}</TableCell>
                    <TableCell>{req.quantity}</TableCell>
                    <TableCell>
                      <Badge className={urgencyColors[req.urgency]}>
                        {req.urgency}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[req.status]}>
                        {req.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {req.status === 'pending' && (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-emerald-600 hover:bg-emerald-50"
                            onClick={() => handleApprove(req.id)}
                            data-testid={`approve-${req.id}`}
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => handleReject(req.id)}
                            data-testid={`reject-${req.id}`}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* New Request Dialog */}
      <Dialog open={showNewDialog} onOpenChange={(open) => { setShowNewDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-teal-600" />
              New Blood Request
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Request Type */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Request Type *</Label>
                <Select 
                  value={form.request_type}
                  onValueChange={(v) => setForm({ ...form, request_type: v })}
                >
                  <SelectTrigger data-testid="select-request-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="internal">Internal (Patient)</SelectItem>
                    <SelectItem value="external">External (Hospital)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Urgency *</Label>
                <Select 
                  value={form.urgency}
                  onValueChange={(v) => setForm({ ...form, urgency: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="emergency">Emergency</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Requester Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Requester Name *</Label>
                <Input
                  value={form.requester_name}
                  onChange={(e) => setForm({ ...form, requester_name: e.target.value })}
                  placeholder="Enter name"
                  data-testid="input-requester-name"
                />
              </div>
              <div className="space-y-2">
                <Label>Contact Number *</Label>
                <Input
                  value={form.requester_contact}
                  onChange={(e) => setForm({ ...form, requester_contact: e.target.value })}
                  placeholder="Enter contact"
                />
              </div>
            </div>

            {form.request_type === 'external' && (
              <div className="space-y-2">
                <Label>Hospital Name</Label>
                <Input
                  value={form.hospital_name}
                  onChange={(e) => setForm({ ...form, hospital_name: e.target.value })}
                  placeholder="Enter hospital name"
                />
              </div>
            )}

            {form.request_type === 'internal' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Patient Name</Label>
                  <Input
                    value={form.patient_name}
                    onChange={(e) => setForm({ ...form, patient_name: e.target.value })}
                    placeholder="Enter patient name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Patient ID</Label>
                  <Input
                    value={form.patient_id}
                    onChange={(e) => setForm({ ...form, patient_id: e.target.value })}
                    placeholder="Enter patient ID"
                  />
                </div>
              </div>
            )}

            {/* Blood Product Info */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Blood Group *</Label>
                <Select 
                  value={form.blood_group}
                  onValueChange={(v) => setForm({ ...form, blood_group: v })}
                >
                  <SelectTrigger data-testid="select-blood-group">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {bloodGroups.map(bg => (
                      <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Product Type *</Label>
                <Select 
                  value={form.product_type}
                  onValueChange={(v) => setForm({ ...form, product_type: v })}
                >
                  <SelectTrigger data-testid="select-product-type">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {productTypes.map(pt => (
                      <SelectItem key={pt.value} value={pt.value}>{pt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Quantity (Units) *</Label>
                <Input
                  type="number"
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                  placeholder="e.g., 2"
                  data-testid="input-quantity"
                />
              </div>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Request Date *</Label>
                <Input
                  type="date"
                  value={form.requested_date}
                  onChange={(e) => setForm({ ...form, requested_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Required By</Label>
                <Input
                  type="date"
                  value={form.required_by_date}
                  onChange={(e) => setForm({ ...form, required_by_date: e.target.value })}
                />
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Any additional notes..."
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowNewDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateRequest}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={!form.requester_name || !form.requester_contact || !form.blood_group || !form.product_type || !form.quantity}
              data-testid="submit-request-btn"
            >
              <Plus className="w-4 h-4 mr-1" />
              Create Request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
