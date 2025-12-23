import React, { useState, useEffect } from 'react';
import { discardAPI } from '../lib/api';
import { toast } from 'sonner';
import { Trash2, Plus, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const discardReasons = [
  { value: 'expired', label: 'Expired' },
  { value: 'failed_qc', label: 'Failed QC' },
  { value: 'rejected_return', label: 'Rejected Return' },
  { value: 'reactive', label: 'Reactive Test' },
  { value: 'damaged', label: 'Damaged' },
  { value: 'other', label: 'Other' },
];

const COLORS = ['#ef4444', '#f59e0b', '#6366f1', '#ec4899', '#8b5cf6', '#64748b'];

export default function Discards() {
  const [discards, setDiscards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingDiscard, setPendingDiscard] = useState(null);

  const [form, setForm] = useState({
    component_id: '',
    reason: '',
    reason_details: '',
    discard_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchDiscards();
  }, []);

  const fetchDiscards = async () => {
    try {
      const response = await discardAPI.getAll();
      setDiscards(response.data);
    } catch (error) {
      toast.error('Failed to fetch discards');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDiscard = async () => {
    setPendingDiscard(form);
    setShowNewDialog(false);
    setShowConfirmDialog(true);
  };

  const confirmDiscard = async () => {
    try {
      const response = await discardAPI.create(pendingDiscard);
      toast.success(`Discard logged: ${response.data.discard_id}`);
      setShowConfirmDialog(false);
      resetForm();
      fetchDiscards();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to log discard');
    }
  };

  const handleMarkDestroyed = async (discardId) => {
    try {
      await discardAPI.markDestroyed(discardId);
      toast.success('Marked as destroyed');
      fetchDiscards();
    } catch (error) {
      toast.error('Failed to mark as destroyed');
    }
  };

  const resetForm = () => {
    setForm({
      component_id: '',
      reason: '',
      reason_details: '',
      discard_date: new Date().toISOString().split('T')[0],
    });
    setPendingDiscard(null);
  };

  const chartData = discardReasons.map(r => ({
    name: r.label,
    value: discards.filter(d => d.reason === r.value).length
  })).filter(d => d.value > 0);

  const reasonColors = {
    expired: 'bg-red-100 text-red-700',
    failed_qc: 'bg-amber-100 text-amber-700',
    rejected_return: 'bg-purple-100 text-purple-700',
    reactive: 'bg-pink-100 text-pink-700',
    damaged: 'bg-violet-100 text-violet-700',
    other: 'bg-slate-100 text-slate-700',
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="discards-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Discard Management</h1>
          <p className="page-subtitle">Track and manage discarded blood products</p>
        </div>
        <Button 
          onClick={() => setShowNewDialog(true)}
          className="bg-red-600 hover:bg-red-700"
          data-testid="new-discard-btn"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Log Discard
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Total Discards</p>
            <p className="text-2xl font-bold">{discards.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Expired</p>
            <p className="text-2xl font-bold text-red-600">
              {discards.filter(d => d.reason === 'expired').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Reactive</p>
            <p className="text-2xl font-bold text-pink-600">
              {discards.filter(d => d.reason === 'reactive').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Pending Destruction</p>
            <p className="text-2xl font-bold text-amber-600">
              {discards.filter(d => !d.destruction_date).length}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Discard Reasons</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-slate-500">
                No data available
              </div>
            ) : (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={60}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Discard Log</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
              </div>
            ) : discards.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                No discards logged
              </div>
            ) : (
              <Table className="table-dense">
                <TableHeader>
                  <TableRow>
                    <TableHead>Discard ID</TableHead>
                    <TableHead>Component</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Destroyed</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {discards.map((disc) => (
                    <TableRow key={disc.id} className="data-table-row">
                      <TableCell className="font-mono">{disc.discard_id}</TableCell>
                      <TableCell className="font-mono text-xs">{disc.component_id?.slice(0, 15)}...</TableCell>
                      <TableCell>
                        <Badge className={reasonColors[disc.reason]}>
                          {discardReasons.find(r => r.value === disc.reason)?.label || disc.reason}
                        </Badge>
                      </TableCell>
                      <TableCell>{disc.discard_date}</TableCell>
                      <TableCell>
                        {disc.destruction_date ? (
                          <span className="text-emerald-600">{disc.destruction_date}</span>
                        ) : (
                          <span className="text-amber-600">Pending</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {!disc.destruction_date && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMarkDestroyed(disc.id)}
                          >
                            Mark Destroyed
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
      </div>

      {/* New Discard Dialog */}
      <Dialog open={showNewDialog} onOpenChange={(open) => { setShowNewDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-red-600" />
              Log Discard
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
                <Label>Reason *</Label>
                <Select 
                  value={form.reason}
                  onValueChange={(v) => setForm({ ...form, reason: v })}
                >
                  <SelectTrigger data-testid="select-reason">
                    <SelectValue placeholder="Select reason" />
                  </SelectTrigger>
                  <SelectContent>
                    {discardReasons.map(r => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Discard Date *</Label>
                <Input
                  type="date"
                  value={form.discard_date}
                  onChange={(e) => setForm({ ...form, discard_date: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Additional Details</Label>
              <Textarea
                value={form.reason_details}
                onChange={(e) => setForm({ ...form, reason_details: e.target.value })}
                placeholder="Enter additional details..."
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowNewDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateDiscard}
              className="bg-red-600 hover:bg-red-700"
              disabled={!form.component_id || !form.reason}
              data-testid="submit-discard-btn"
            >
              Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Confirm Discard
            </DialogTitle>
            <DialogDescription>
              This action cannot be undone. The item will be permanently marked for discard.
            </DialogDescription>
          </DialogHeader>
          
          {pendingDiscard && (
            <div className="py-4 px-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm"><strong>Item:</strong> {pendingDiscard.component_id}</p>
              <p className="text-sm"><strong>Reason:</strong> {discardReasons.find(r => r.value === pendingDiscard.reason)?.label}</p>
              <p className="text-sm"><strong>Date:</strong> {pendingDiscard.discard_date}</p>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowConfirmDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={confirmDiscard}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-discard-btn"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Confirm Discard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
