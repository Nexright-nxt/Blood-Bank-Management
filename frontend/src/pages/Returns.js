import React, { useState, useEffect } from 'react';
import { returnAPI, storageAPI } from '../lib/api';
import { toast } from 'sonner';
import { RotateCcw, Plus, Check, X, Warehouse } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';

export default function Returns() {
  const [returns, setReturns] = useState([]);
  const [storageLocations, setStorageLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [showProcessDialog, setShowProcessDialog] = useState(false);
  const [selectedReturn, setSelectedReturn] = useState(null);

  const [form, setForm] = useState({
    component_id: '',
    return_date: new Date().toISOString().split('T')[0],
    source: 'internal',
    reason: '',
    hospital_name: '',
    contact_person: '',
    transport_conditions: '',
  });

  const [processForm, setProcessForm] = useState({
    qc_pass: null,
    decision: '',
    storage_location_id: '',
    qc_notes: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [returnsRes, storageRes] = await Promise.all([
        returnAPI.getAll(),
        storageAPI.getAll()
      ]);
      setReturns(returnsRes.data);
      setStorageLocations(storageRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReturn = async () => {
    try {
      const response = await returnAPI.create(form);
      toast.success(`Return created: ${response.data.return_id}`);
      setShowNewDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create return');
    }
  };

  const handleProcessReturn = async () => {
    if (processForm.qc_pass === null || !processForm.decision) {
      toast.error('Please complete QC evaluation');
      return;
    }

    try {
      await returnAPI.process(selectedReturn.id, processForm);
      toast.success(`Return ${processForm.decision === 'accept' ? 'accepted' : 'rejected'}`);
      setShowProcessDialog(false);
      setSelectedReturn(null);
      resetProcessForm();
      fetchData();
    } catch (error) {
      toast.error('Failed to process return');
    }
  };

  const resetForm = () => {
    setForm({
      component_id: '',
      return_date: new Date().toISOString().split('T')[0],
      source: 'internal',
      reason: '',
      hospital_name: '',
      contact_person: '',
      transport_conditions: '',
    });
  };

  const resetProcessForm = () => {
    setProcessForm({
      qc_pass: null,
      decision: '',
      storage_location_id: '',
      qc_notes: '',
    });
  };

  const openProcessDialog = (ret) => {
    setSelectedReturn(ret);
    setShowProcessDialog(true);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="returns-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Returns Management</h1>
          <p className="page-subtitle">Process returned blood products with QC and storage assignment</p>
        </div>
        <Button 
          onClick={() => setShowNewDialog(true)}
          className="bg-teal-600 hover:bg-teal-700"
          data-testid="new-return-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Log Return
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Total Returns</p>
            <p className="text-2xl font-bold">{returns.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat border-l-4 border-l-amber-500">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Pending QC</p>
            <p className="text-2xl font-bold text-amber-600">
              {returns.filter(r => r.decision === null).length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat border-l-4 border-l-emerald-500">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Accepted & Restocked</p>
            <p className="text-2xl font-bold text-emerald-600">
              {returns.filter(r => r.decision === 'accept').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat border-l-4 border-l-red-500">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Rejected</p>
            <p className="text-2xl font-bold text-red-600">
              {returns.filter(r => r.decision === 'reject').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Returns Table */}
      <Card>
        <CardHeader>
          <CardTitle>Returned Items</CardTitle>
          <CardDescription>Process returns with QC and assign to storage</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
            </div>
          ) : returns.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No returns logged
            </div>
          ) : (
            <Table className="table-dense">
              <TableHeader>
                <TableRow>
                  <TableHead>Return ID</TableHead>
                  <TableHead>Component</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Return Date</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>QC</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead>Storage</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {returns.map((ret) => (
                  <TableRow key={ret.id} className="data-table-row">
                    <TableCell className="font-mono">{ret.return_id}</TableCell>
                    <TableCell className="font-mono text-xs">{ret.component_id?.slice(0, 15)}...</TableCell>
                    <TableCell>
                      <div>
                        <span className="capitalize">{ret.source}</span>
                        {ret.hospital_name && (
                          <p className="text-xs text-slate-500">{ret.hospital_name}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{ret.return_date}</TableCell>
                    <TableCell className="max-w-32 truncate">{ret.reason}</TableCell>
                    <TableCell>
                      {ret.qc_pass !== null ? (
                        <Badge className={ret.qc_pass ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}>
                          {ret.qc_pass ? 'Pass' : 'Fail'}
                        </Badge>
                      ) : (
                        <span className="text-slate-400">Pending</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {ret.decision ? (
                        <Badge className={ret.decision === 'accept' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}>
                          {ret.decision === 'accept' ? 'Accepted' : 'Rejected'}
                        </Badge>
                      ) : (
                        <span className="text-slate-400">Pending</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {ret.storage_location_id ? (
                        <Badge variant="outline" className="text-xs">
                          <Warehouse className="w-3 h-3 mr-1" />
                          Assigned
                        </Badge>
                      ) : ret.decision === 'accept' ? (
                        <span className="text-amber-500 text-xs">Not assigned</span>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {ret.decision === null && (
                        <Button
                          size="sm"
                          onClick={() => openProcessDialog(ret)}
                          className="bg-teal-600 hover:bg-teal-700"
                        >
                          Process
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* New Return Dialog */}
      <Dialog open={showNewDialog} onOpenChange={(open) => { setShowNewDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-teal-600" />
              Log Return
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Component/Unit ID *</Label>
              <Input
                value={form.component_id}
                onChange={(e) => setForm({ ...form, component_id: e.target.value })}
                placeholder="Enter component or unit ID"
                data-testid="input-component-id"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Source *</Label>
                <Select 
                  value={form.source}
                  onValueChange={(v) => setForm({ ...form, source: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="internal">Internal</SelectItem>
                    <SelectItem value="external">External (Hospital)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Return Date *</Label>
                <Input
                  type="date"
                  value={form.return_date}
                  onChange={(e) => setForm({ ...form, return_date: e.target.value })}
                />
              </div>
            </div>

            {form.source === 'external' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Hospital Name</Label>
                  <Input
                    value={form.hospital_name}
                    onChange={(e) => setForm({ ...form, hospital_name: e.target.value })}
                    placeholder="Hospital name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Contact Person</Label>
                  <Input
                    value={form.contact_person}
                    onChange={(e) => setForm({ ...form, contact_person: e.target.value })}
                    placeholder="Contact name"
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label>Transport Conditions</Label>
              <Select 
                value={form.transport_conditions}
                onValueChange={(v) => setForm({ ...form, transport_conditions: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select condition" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cold_chain_maintained">Cold Chain Maintained</SelectItem>
                  <SelectItem value="cold_chain_broken">Cold Chain Broken</SelectItem>
                  <SelectItem value="unknown">Unknown</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Reason *</Label>
              <Textarea
                value={form.reason}
                onChange={(e) => setForm({ ...form, reason: e.target.value })}
                placeholder="Enter reason for return..."
                rows={3}
                data-testid="input-reason"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowNewDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateReturn}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={!form.component_id || !form.reason}
              data-testid="submit-return-btn"
            >
              Log Return
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Process Return Dialog */}
      <Dialog open={showProcessDialog} onOpenChange={(open) => { setShowProcessDialog(open); if (!open) { setSelectedReturn(null); resetProcessForm(); } }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-teal-600" />
              Process Return
            </DialogTitle>
            <DialogDescription>
              Perform QC evaluation and decide on the returned item
            </DialogDescription>
          </DialogHeader>
          
          {selectedReturn && (
            <div className="space-y-4 py-4">
              {/* Return Info */}
              <div className="p-3 bg-slate-50 rounded-lg">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-slate-500">Return ID:</span> {selectedReturn.return_id}</div>
                  <div><span className="text-slate-500">Source:</span> {selectedReturn.source}</div>
                  <div className="col-span-2"><span className="text-slate-500">Reason:</span> {selectedReturn.reason}</div>
                  {selectedReturn.transport_conditions && (
                    <div className="col-span-2">
                      <span className="text-slate-500">Transport:</span> {selectedReturn.transport_conditions.replace('_', ' ')}
                    </div>
                  )}
                </div>
              </div>

              {/* QC Evaluation */}
              <div className="space-y-2">
                <Label>QC Result *</Label>
                <div className="flex gap-4">
                  <Button
                    type="button"
                    variant={processForm.qc_pass === true ? 'default' : 'outline'}
                    className={processForm.qc_pass === true ? 'bg-emerald-600' : ''}
                    onClick={() => setProcessForm({ ...processForm, qc_pass: true, decision: 'accept' })}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Pass
                  </Button>
                  <Button
                    type="button"
                    variant={processForm.qc_pass === false ? 'default' : 'outline'}
                    className={processForm.qc_pass === false ? 'bg-red-600' : ''}
                    onClick={() => setProcessForm({ ...processForm, qc_pass: false, decision: 'reject' })}
                  >
                    <X className="w-4 h-4 mr-2" />
                    Fail
                  </Button>
                </div>
              </div>

              {/* Decision */}
              <div className="space-y-2">
                <Label>Decision *</Label>
                <Select 
                  value={processForm.decision}
                  onValueChange={(v) => setProcessForm({ ...processForm, decision: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select decision" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="accept">Accept - Return to Inventory</SelectItem>
                    <SelectItem value="reject">Reject - Send to Discard</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Storage Location (if accepting) */}
              {processForm.decision === 'accept' && (
                <div className="space-y-2">
                  <Label>Assign to Storage Location</Label>
                  <Select 
                    value={processForm.storage_location_id}
                    onValueChange={(v) => setProcessForm({ ...processForm, storage_location_id: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select storage location" />
                    </SelectTrigger>
                    <SelectContent>
                      {storageLocations.map(loc => (
                        <SelectItem key={loc.id} value={loc.id}>
                          {loc.storage_name} ({loc.storage_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* QC Notes */}
              <div className="space-y-2">
                <Label>QC Notes</Label>
                <Textarea
                  value={processForm.qc_notes}
                  onChange={(e) => setProcessForm({ ...processForm, qc_notes: e.target.value })}
                  placeholder="Enter QC evaluation notes..."
                  rows={2}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowProcessDialog(false); setSelectedReturn(null); resetProcessForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleProcessReturn}
              className={processForm.decision === 'accept' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'}
              disabled={processForm.qc_pass === null || !processForm.decision}
            >
              {processForm.decision === 'accept' ? 'Accept & Restock' : 'Reject & Discard'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
