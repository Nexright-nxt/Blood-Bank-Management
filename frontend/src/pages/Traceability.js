import React, { useState, useEffect } from 'react';
import { bloodUnitAPI, custodyAPI } from '../lib/api';
import { toast } from 'sonner';
import { Search, ArrowRight, CheckCircle, Clock, Package } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';

const stages = [
  { value: 'collection', label: 'Collection' },
  { value: 'lab', label: 'Laboratory' },
  { value: 'processing', label: 'Processing' },
  { value: 'storage', label: 'Storage' },
  { value: 'issue', label: 'Issue' },
];

const locations = [
  'Collection Room',
  'Laboratory',
  'Processing Unit',
  'Storage - PRC',
  'Storage - Plasma',
  'Storage - Platelets',
  'Distribution Center',
  'Issue Counter',
];

export default function Traceability() {
  const [units, setUnits] = useState([]);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [traceability, setTraceability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showHandoverDialog, setShowHandoverDialog] = useState(false);
  const [handoverForm, setHandoverForm] = useState({
    stage: '',
    from_location: '',
    to_location: '',
    giver_id: '',
    receiver_id: '',
    notes: '',
  });

  useEffect(() => {
    fetchUnits();
  }, []);

  const fetchUnits = async () => {
    try {
      const response = await bloodUnitAPI.getAll();
      setUnits(response.data);
    } catch (error) {
      toast.error('Failed to fetch blood units');
    } finally {
      setLoading(false);
    }
  };

  const fetchTraceability = async (unitId) => {
    try {
      const response = await bloodUnitAPI.getTraceability(unitId);
      setTraceability(response.data);
      setSelectedUnit(response.data.unit);
    } catch (error) {
      toast.error('Failed to fetch traceability');
    }
  };

  const handleSearch = () => {
    if (!searchTerm.trim()) {
      fetchUnits();
      return;
    }
    const filtered = units.filter(u => 
      u.unit_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.bag_barcode?.includes(searchTerm)
    );
    setUnits(filtered);
  };

  const handleHandoverSubmit = async () => {
    if (!selectedUnit) return;

    try {
      await custodyAPI.create({
        unit_id: selectedUnit.id,
        ...handoverForm,
      });
      toast.success('Handover recorded successfully');
      setShowHandoverDialog(false);
      fetchTraceability(selectedUnit.id);
      setHandoverForm({
        stage: '',
        from_location: '',
        to_location: '',
        giver_id: '',
        receiver_id: '',
        notes: '',
      });
    } catch (error) {
      toast.error('Failed to record handover');
    }
  };

  const handleConfirmCustody = async (custodyId) => {
    try {
      await custodyAPI.confirm(custodyId);
      toast.success('Custody confirmed');
      if (selectedUnit) {
        fetchTraceability(selectedUnit.id);
      }
    } catch (error) {
      toast.error('Failed to confirm custody');
    }
  };

  const statusColors = {
    collected: 'bg-blue-100 text-blue-700',
    lab: 'bg-purple-100 text-purple-700',
    processing: 'bg-amber-100 text-amber-700',
    quarantine: 'bg-red-100 text-red-700',
    ready_to_use: 'bg-emerald-100 text-emerald-700',
    reserved: 'bg-cyan-100 text-cyan-700',
    issued: 'bg-slate-100 text-slate-700',
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="traceability-page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Traceability & Chain of Custody</h1>
        <p className="page-subtitle">Track blood units and manage handover records</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Units List */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Blood Units</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Search by Unit ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  data-testid="unit-search"
                />
                <Button variant="outline" onClick={handleSearch}>
                  <Search className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="max-h-96 overflow-y-auto space-y-2">
                {loading ? (
                  <div className="flex justify-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600"></div>
                  </div>
                ) : units.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">No units found</p>
                ) : (
                  units.map((unit) => (
                    <div
                      key={unit.id}
                      onClick={() => fetchTraceability(unit.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedUnit?.id === unit.id
                          ? 'border-teal-500 bg-teal-50'
                          : 'border-slate-200 hover:border-teal-300'
                      }`}
                      data-testid={`unit-${unit.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm font-medium">{unit.unit_id}</span>
                        <Badge className={statusColors[unit.status]}>
                          {unit.status?.replace('_', ' ')}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                        {unit.confirmed_blood_group || unit.blood_group ? (
                          <span className="blood-group-badge text-xs">
                            {unit.confirmed_blood_group || unit.blood_group}
                          </span>
                        ) : null}
                        <span>{unit.current_location}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Traceability Details */}
        <div className="lg:col-span-2 space-y-4">
          {!selectedUnit ? (
            <Card>
              <CardContent className="py-12 text-center text-slate-500">
                <Package className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p>Select a blood unit to view its traceability</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Unit Details */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="font-mono">{selectedUnit.unit_id}</CardTitle>
                    <CardDescription>Blood Unit Details</CardDescription>
                  </div>
                  <Button 
                    onClick={() => setShowHandoverDialog(true)}
                    className="bg-teal-600 hover:bg-teal-700"
                    data-testid="record-handover-btn"
                  >
                    Record Handover
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-slate-500">Blood Group</p>
                      {selectedUnit.confirmed_blood_group || selectedUnit.blood_group ? (
                        <span className="blood-group-badge">
                          {selectedUnit.confirmed_blood_group || selectedUnit.blood_group}
                        </span>
                      ) : (
                        <span className="text-slate-400">Pending</span>
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Status</p>
                      <Badge className={statusColors[selectedUnit.status]}>
                        {selectedUnit.status?.replace('_', ' ')}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Location</p>
                      <p className="font-medium">{selectedUnit.current_location}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Collection Date</p>
                      <p className="font-medium">{selectedUnit.collection_date}</p>
                    </div>
                  </div>
                  
                  {selectedUnit.bag_barcode && (
                    <div className="mt-4 p-4 bg-white border rounded-lg flex justify-center">
                      <img 
                        src={`data:image/png;base64,${selectedUnit.bag_barcode}`}
                        alt="Barcode"
                        className="h-16"
                      />
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Chain of Custody Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle>Chain of Custody</CardTitle>
                  <CardDescription>Complete handover history</CardDescription>
                </CardHeader>
                <CardContent>
                  {!traceability?.chain_of_custody?.length ? (
                    <p className="text-center text-slate-500 py-4">No custody records yet</p>
                  ) : (
                    <div className="space-y-4">
                      {traceability.chain_of_custody.map((custody, idx) => (
                        <div 
                          key={custody.id}
                          className="flex items-start gap-4 p-4 bg-slate-50 rounded-lg"
                        >
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            custody.confirmed ? 'bg-emerald-100' : 'bg-amber-100'
                          }`}>
                            {custody.confirmed ? (
                              <CheckCircle className="w-5 h-5 text-emerald-600" />
                            ) : (
                              <Clock className="w-5 h-5 text-amber-600" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <p className="font-medium capitalize">{custody.stage}</p>
                              <span className="text-xs text-slate-500">
                                {new Date(custody.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-slate-600 mt-1">
                              <span>{custody.from_location}</span>
                              <ArrowRight className="w-4 h-4" />
                              <span>{custody.to_location}</span>
                            </div>
                            {custody.notes && (
                              <p className="text-sm text-slate-500 mt-1">{custody.notes}</p>
                            )}
                            {!custody.confirmed && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="mt-2"
                                onClick={() => handleConfirmCustody(custody.id)}
                              >
                                Confirm Receipt
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Lab Tests */}
              {traceability?.lab_tests?.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Lab Tests</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Blood Group</TableHead>
                          <TableHead>HIV</TableHead>
                          <TableHead>HBsAg</TableHead>
                          <TableHead>HCV</TableHead>
                          <TableHead>Syphilis</TableHead>
                          <TableHead>Overall</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {traceability.lab_tests.map((test) => (
                          <TableRow key={test.id}>
                            <TableCell>{test.test_date}</TableCell>
                            <TableCell>
                              {test.confirmed_blood_group && (
                                <span className="blood-group-badge">{test.confirmed_blood_group}</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Badge variant={test.hiv_result === 'non_reactive' ? 'default' : 'destructive'}>
                                {test.hiv_result || '-'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={test.hbsag_result === 'non_reactive' ? 'default' : 'destructive'}>
                                {test.hbsag_result || '-'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={test.hcv_result === 'non_reactive' ? 'default' : 'destructive'}>
                                {test.hcv_result || '-'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={test.syphilis_result === 'non_reactive' ? 'default' : 'destructive'}>
                                {test.syphilis_result || '-'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={test.overall_status === 'non_reactive' ? 'default' : 'destructive'}>
                                {test.overall_status || 'Pending'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>

      {/* Handover Dialog */}
      <Dialog open={showHandoverDialog} onOpenChange={setShowHandoverDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Record Handover</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Stage</Label>
              <Select 
                value={handoverForm.stage} 
                onValueChange={(v) => setHandoverForm({ ...handoverForm, stage: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select stage" />
                </SelectTrigger>
                <SelectContent>
                  {stages.map(s => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>From Location</Label>
                <Select 
                  value={handoverForm.from_location} 
                  onValueChange={(v) => setHandoverForm({ ...handoverForm, from_location: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="From" />
                  </SelectTrigger>
                  <SelectContent>
                    {locations.map(l => (
                      <SelectItem key={l} value={l}>{l}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>To Location</Label>
                <Select 
                  value={handoverForm.to_location} 
                  onValueChange={(v) => setHandoverForm({ ...handoverForm, to_location: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="To" />
                  </SelectTrigger>
                  <SelectContent>
                    {locations.map(l => (
                      <SelectItem key={l} value={l}>{l}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Giver ID</Label>
                <Input
                  value={handoverForm.giver_id}
                  onChange={(e) => setHandoverForm({ ...handoverForm, giver_id: e.target.value })}
                  placeholder="Staff ID"
                />
              </div>
              <div className="space-y-2">
                <Label>Receiver ID</Label>
                <Input
                  value={handoverForm.receiver_id}
                  onChange={(e) => setHandoverForm({ ...handoverForm, receiver_id: e.target.value })}
                  placeholder="Staff ID"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={handoverForm.notes}
                onChange={(e) => setHandoverForm({ ...handoverForm, notes: e.target.value })}
                placeholder="Any additional notes..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHandoverDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleHandoverSubmit}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={!handoverForm.stage || !handoverForm.from_location || !handoverForm.to_location}
            >
              Record Handover
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
