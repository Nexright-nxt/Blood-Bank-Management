import React, { useState, useEffect } from 'react';
import { bloodUnitAPI, componentAPI, qcAPI, quarantineAPI } from '../lib/api';
import { toast } from 'sonner';
import { ShieldCheck, CheckCircle, AlertTriangle, XCircle, Search } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

export default function QCValidation() {
  const [pendingItems, setPendingItems] = useState([]);
  const [validations, setValidations] = useState([]);
  const [quarantineItems, setQuarantineItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showValidateDialog, setShowValidateDialog] = useState(false);
  const [showQuarantineDialog, setShowQuarantineDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  const [validateForm, setValidateForm] = useState({
    data_complete: false,
    screening_complete: false,
    custody_complete: false,
  });

  const [quarantineForm, setQuarantineForm] = useState({
    retest_result: '',
    disposition: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [unitsRes, componentsRes, validationsRes, quarantineRes] = await Promise.all([
        bloodUnitAPI.getAll({ status: 'processing' }),
        componentAPI.getAll({ status: 'processing' }),
        qcAPI.getAll(),
        quarantineAPI.getAll()
      ]);
      
      // Combine units and components for validation
      const pending = [
        ...unitsRes.data.map(u => ({ ...u, type: 'unit' })),
        ...componentsRes.data.map(c => ({ ...c, type: 'component' }))
      ];
      
      setPendingItems(pending);
      setValidations(validationsRes.data);
      setQuarantineItems(quarantineRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!selectedItem) return;

    try {
      const response = await qcAPI.create({
        unit_component_id: selectedItem.id,
        unit_type: selectedItem.type,
        ...validateForm,
      });
      
      const status = response.data.qc_status;
      if (status === 'approved') {
        toast.success('Item approved and released!');
      } else {
        toast.warning(`Item on hold: ${response.data.hold_reason || 'Missing validation checks'}`);
      }
      
      setShowValidateDialog(false);
      fetchData();
      resetValidateForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to validate');
    }
  };

  const handleResolveQuarantine = async () => {
    if (!selectedItem) return;

    try {
      await quarantineAPI.resolve(selectedItem.id, {
        retest_result: quarantineForm.retest_result,
        disposition: quarantineForm.disposition,
      });
      
      toast.success(`Item ${quarantineForm.disposition === 'release' ? 'released' : 'marked for discard'}`);
      setShowQuarantineDialog(false);
      fetchData();
      setQuarantineForm({ retest_result: '', disposition: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to resolve');
    }
  };

  const resetValidateForm = () => {
    setValidateForm({
      data_complete: false,
      screening_complete: false,
      custody_complete: false,
    });
    setSelectedItem(null);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="qc-validation-page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">QC Validation & Release</h1>
        <p className="page-subtitle">Quality control gate for blood products</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Pending Validation</p>
            <p className="text-2xl font-bold">{pendingItems.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Approved</p>
            <p className="text-2xl font-bold text-emerald-600">
              {validations.filter(v => v.status === 'approved').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">On Hold</p>
            <p className="text-2xl font-bold text-amber-600">
              {validations.filter(v => v.status === 'hold').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">In Quarantine</p>
            <p className="text-2xl font-bold text-red-600">
              {quarantineItems.length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="validate">
        <TabsList>
          <TabsTrigger value="validate">Pending Validation</TabsTrigger>
          <TabsTrigger value="quarantine">Quarantine</TabsTrigger>
          <TabsTrigger value="history">Validation History</TabsTrigger>
        </TabsList>

        <TabsContent value="validate" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Items Pending QC Validation</CardTitle>
              <CardDescription>Review and approve blood units and components</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : pendingItems.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No items pending validation
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingItems.map((item) => (
                      <TableRow key={item.id} className="data-table-row">
                        <TableCell className="font-mono">
                          {item.unit_id || item.component_id}
                        </TableCell>
                        <TableCell className="capitalize">{item.type}</TableCell>
                        <TableCell>
                          {(item.confirmed_blood_group || item.blood_group) && (
                            <span className="blood-group-badge">
                              {item.confirmed_blood_group || item.blood_group}
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-amber-100 text-amber-700">
                            {item.status?.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedItem(item);
                              setShowValidateDialog(true);
                            }}
                            className="bg-teal-600 hover:bg-teal-700"
                            data-testid={`validate-${item.id}`}
                          >
                            <ShieldCheck className="w-4 h-4 mr-1" />
                            Validate
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quarantine" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                Quarantine Management
              </CardTitle>
              <CardDescription>Items quarantined due to reactive or gray zone results</CardDescription>
            </CardHeader>
            <CardContent>
              {quarantineItems.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No items in quarantine
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item ID</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>Quarantine Date</TableHead>
                      <TableHead>Retest Result</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {quarantineItems.map((item) => (
                      <TableRow key={item.id} className="data-table-row">
                        <TableCell className="font-mono">{item.unit_component_id?.slice(0, 20)}...</TableCell>
                        <TableCell>{item.reason}</TableCell>
                        <TableCell>{item.quarantine_date}</TableCell>
                        <TableCell>
                          {item.retest_result ? (
                            <Badge className={
                              item.retest_result === 'non_reactive' ? 'bg-emerald-100 text-emerald-700' :
                              'bg-red-100 text-red-700'
                            }>
                              {item.retest_result}
                            </Badge>
                          ) : (
                            <span className="text-slate-400">Pending</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedItem(item);
                              setShowQuarantineDialog(true);
                            }}
                            data-testid={`resolve-${item.id}`}
                          >
                            Resolve
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Validation History</CardTitle>
            </CardHeader>
            <CardContent>
              {validations.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No validation history
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead>Screening</TableHead>
                      <TableHead>Custody</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {validations.map((v) => (
                      <TableRow key={v.id} className="data-table-row">
                        <TableCell className="font-mono">{v.unit_component_id?.slice(0, 20)}...</TableCell>
                        <TableCell className="capitalize">{v.unit_type}</TableCell>
                        <TableCell>
                          {v.data_complete ? (
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600" />
                          )}
                        </TableCell>
                        <TableCell>
                          {v.screening_complete ? (
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600" />
                          )}
                        </TableCell>
                        <TableCell>
                          {v.custody_complete ? (
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            v.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                            'bg-amber-100 text-amber-700'
                          }>
                            {v.status}
                          </Badge>
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

      {/* Validate Dialog */}
      <Dialog open={showValidateDialog} onOpenChange={(open) => { setShowValidateDialog(open); if (!open) resetValidateForm(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-teal-600" />
              QC Validation Checklist
            </DialogTitle>
          </DialogHeader>
          
          {selectedItem && (
            <div className="py-2 px-3 bg-slate-50 rounded-lg mb-4">
              <p className="text-sm text-slate-500">{selectedItem.type === 'unit' ? 'Unit' : 'Component'}</p>
              <p className="font-mono font-medium">{selectedItem.unit_id || selectedItem.component_id}</p>
            </div>
          )}
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
              <Checkbox
                id="data_complete"
                checked={validateForm.data_complete}
                onCheckedChange={(checked) => setValidateForm({ ...validateForm, data_complete: checked })}
              />
              <label htmlFor="data_complete" className="flex-1 cursor-pointer">
                <p className="font-medium">Data Complete</p>
                <p className="text-sm text-slate-500">All donor and collection information verified</p>
              </label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
              <Checkbox
                id="screening_complete"
                checked={validateForm.screening_complete}
                onCheckedChange={(checked) => setValidateForm({ ...validateForm, screening_complete: checked })}
              />
              <label htmlFor="screening_complete" className="flex-1 cursor-pointer">
                <p className="font-medium">Screening Complete</p>
                <p className="text-sm text-slate-500">All lab tests completed with non-reactive results</p>
              </label>
            </div>
            
            <div className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
              <Checkbox
                id="custody_complete"
                checked={validateForm.custody_complete}
                onCheckedChange={(checked) => setValidateForm({ ...validateForm, custody_complete: checked })}
              />
              <label htmlFor="custody_complete" className="flex-1 cursor-pointer">
                <p className="font-medium">Custody Complete</p>
                <p className="text-sm text-slate-500">Chain of custody verified and unbroken</p>
              </label>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => { setShowValidateDialog(false); resetValidateForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleValidate}
              className="bg-teal-600 hover:bg-teal-700"
              data-testid="submit-validation-btn"
            >
              <ShieldCheck className="w-4 h-4 mr-1" />
              Submit Validation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Quarantine Dialog */}
      <Dialog open={showQuarantineDialog} onOpenChange={setShowQuarantineDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              Resolve Quarantine
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Retest Result</Label>
              <Select 
                value={quarantineForm.retest_result}
                onValueChange={(v) => setQuarantineForm({ ...quarantineForm, retest_result: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select retest result" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="non_reactive">Non-Reactive</SelectItem>
                  <SelectItem value="gray">Gray Zone</SelectItem>
                  <SelectItem value="reactive">Reactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Disposition</Label>
              <Select 
                value={quarantineForm.disposition}
                onValueChange={(v) => setQuarantineForm({ ...quarantineForm, disposition: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select disposition" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="release">Release for Use</SelectItem>
                  <SelectItem value="discard">Mark for Discard</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowQuarantineDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleResolveQuarantine}
              className={quarantineForm.disposition === 'release' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'}
              disabled={!quarantineForm.retest_result || !quarantineForm.disposition}
            >
              {quarantineForm.disposition === 'release' ? 'Release' : 'Discard'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
