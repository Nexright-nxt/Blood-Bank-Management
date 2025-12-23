import React, { useState, useEffect } from 'react';
import { returnAPI } from '../lib/api';
import { toast } from 'sonner';
import { RotateCcw, Plus, Check, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';

export default function Returns() {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewDialog, setShowNewDialog] = useState(false);

  const [form, setForm] = useState({
    component_id: '',
    return_date: new Date().toISOString().split('T')[0],
    source: 'internal',
    reason: '',
  });

  useEffect(() => {
    fetchReturns();
  }, []);

  const fetchReturns = async () => {
    try {
      const response = await returnAPI.getAll();
      setReturns(response.data);
    } catch (error) {
      toast.error('Failed to fetch returns');
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
      fetchReturns();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create return');
    }
  };

  const handleProcessReturn = async (returnId, qcPass, decision) => {
    try {
      await returnAPI.process(returnId, { qc_pass: qcPass, decision });
      toast.success(`Return ${decision === 'accept' ? 'accepted' : 'rejected'}`);
      fetchReturns();
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
    });
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="returns-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Returns Management</h1>
          <p className="page-subtitle">Process returned blood products</p>
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Total Returns</p>
            <p className="text-2xl font-bold">{returns.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Pending QC</p>
            <p className="text-2xl font-bold text-amber-600">
              {returns.filter(r => r.decision === null).length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Accepted</p>
            <p className="text-2xl font-bold text-emerald-600">
              {returns.filter(r => r.decision === 'accept').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Returns Table */}
      <Card>
        <CardHeader>
          <CardTitle>Returned Items</CardTitle>
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
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {returns.map((ret) => (
                  <TableRow key={ret.id} className="data-table-row">
                    <TableCell className="font-mono">{ret.return_id}</TableCell>
                    <TableCell className="font-mono text-xs">{ret.component_id?.slice(0, 15)}...</TableCell>
                    <TableCell className="capitalize">{ret.source}</TableCell>
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
                    <TableCell className="text-right">
                      {ret.decision === null && (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-emerald-600 hover:bg-emerald-50"
                            onClick={() => handleProcessReturn(ret.id, true, 'accept')}
                            title="QC Pass - Accept"
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => handleProcessReturn(ret.id, false, 'reject')}
                            title="QC Fail - Reject"
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

      {/* New Return Dialog */}
      <Dialog open={showNewDialog} onOpenChange={(open) => { setShowNewDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-md">
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
                    <SelectItem value="external">External</SelectItem>
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
    </div>
  );
}
