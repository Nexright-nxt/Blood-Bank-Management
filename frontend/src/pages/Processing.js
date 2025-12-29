import React, { useState, useEffect } from 'react';
import { bloodUnitAPI, componentAPI } from '../lib/api';
import { toast } from 'sonner';
import { Layers, Plus, Search, CheckSquare, Square, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';

const componentTypes = [
  { value: 'prc', label: 'Packed Red Cells (PRC)', expiry: 42, temp: '2-6°C' },
  { value: 'plasma', label: 'Plasma', expiry: 365, temp: '≤ -25°C' },
  { value: 'ffp', label: 'Fresh Frozen Plasma (FFP)', expiry: 365, temp: '≤ -25°C' },
  { value: 'platelets', label: 'Platelets', expiry: 5, temp: '20-24°C' },
  { value: 'cryoprecipitate', label: 'Cryoprecipitate', expiry: 365, temp: '≤ -25°C' },
];

const storageLocations = [
  'Storage - PRC',
  'Storage - Plasma',
  'Storage - Platelets',
  'Freezer A',
  'Freezer B',
  'Refrigerator 1',
  'Refrigerator 2',
];

export default function Processing() {
  const [units, setUnits] = useState([]);
  const [components, setComponents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [selectedUnits, setSelectedUnits] = useState([]);
  const [showProcessDialog, setShowProcessDialog] = useState(false);
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [batchProcessing, setBatchProcessing] = useState(false);

  const [processForm, setProcessForm] = useState({
    component_type: '',
    volume: '',
    storage_location: '',
    batch_id: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [unitsRes, componentsRes] = await Promise.all([
        bloodUnitAPI.getAll({ status: 'lab' }),
        componentAPI.getAll()
      ]);
      setUnits(unitsRes.data);
      setComponents(componentsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateComponent = async () => {
    if (!selectedUnit) return;

    try {
      const componentType = componentTypes.find(c => c.value === processForm.component_type);
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + (componentType?.expiry || 35));

      const response = await componentAPI.create({
        parent_unit_id: selectedUnit.id,
        component_type: processForm.component_type,
        volume: parseFloat(processForm.volume),
        storage_location: processForm.storage_location || undefined,
        batch_id: processForm.batch_id || undefined,
        expiry_date: expiryDate.toISOString().split('T')[0],
      });
      
      toast.success(`Component created: ${response.data.component_id}`);
      setShowProcessDialog(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create component');
    }
  };

  const resetForm = () => {
    setProcessForm({
      component_type: '',
      volume: '',
      storage_location: '',
      batch_id: '',
    });
    setSelectedUnit(null);
  };

  const toggleSelectUnit = (unit) => {
    setSelectedUnits(prev => {
      const isSelected = prev.some(u => u.id === unit.id);
      if (isSelected) {
        return prev.filter(u => u.id !== unit.id);
      }
      return [...prev, unit];
    });
  };

  const toggleSelectAll = () => {
    if (selectedUnits.length === filteredUnits.length) {
      setSelectedUnits([]);
    } else {
      setSelectedUnits([...filteredUnits]);
    }
  };

  const handleBatchProcess = async () => {
    if (selectedUnits.length === 0 || !processForm.component_type || !processForm.volume) {
      toast.error('Please select units and fill required fields');
      return;
    }

    setBatchProcessing(true);
    const componentType = componentTypes.find(c => c.value === processForm.component_type);
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + (componentType?.expiry || 35));

    let successCount = 0;
    let failCount = 0;

    for (const unit of selectedUnits) {
      try {
        await componentAPI.create({
          parent_unit_id: unit.id,
          component_type: processForm.component_type,
          volume: parseFloat(processForm.volume),
          storage_location: processForm.storage_location || undefined,
          batch_id: processForm.batch_id || undefined,
          expiry_date: expiryDate.toISOString().split('T')[0],
        });
        successCount++;
      } catch (error) {
        failCount++;
      }
    }

    setBatchProcessing(false);
    
    if (successCount > 0) {
      toast.success(`Created ${successCount} components successfully`);
    }
    if (failCount > 0) {
      toast.error(`Failed to create ${failCount} components`);
    }
    
    setShowBatchDialog(false);
    setSelectedUnits([]);
    fetchData();
    resetForm();
  };

  const filteredUnits = units.filter(u => 
    !searchTerm || 
    u.unit_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const statusColors = {
    processing: 'bg-amber-100 text-amber-700',
    ready_to_use: 'bg-emerald-100 text-emerald-700',
    quarantine: 'bg-red-100 text-red-700',
    reserved: 'bg-cyan-100 text-cyan-700',
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="processing-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Component Processing</h1>
          <p className="page-subtitle">Process blood units into components</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {selectedUnits.length > 0 && (
            <Button 
              className="bg-teal-600 hover:bg-teal-700"
              onClick={() => setShowBatchDialog(true)}
            >
              <Layers className="w-4 h-4 mr-2" />
              Batch Process ({selectedUnits.length})
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="process">
        <TabsList>
          <TabsTrigger value="process">Process Units</TabsTrigger>
          <TabsTrigger value="components">Components</TabsTrigger>
        </TabsList>

        <TabsContent value="process" className="mt-4 space-y-4">
          {/* Search */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="Search by Unit ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                    data-testid="search-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Units ready for processing */}
          <Card>
            <CardHeader>
              <CardTitle>Units Ready for Processing</CardTitle>
              <CardDescription>Blood units that have passed lab testing</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : filteredUnits.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No units ready for processing
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <Checkbox
                          checked={selectedUnits.length === filteredUnits.length && filteredUnits.length > 0}
                          onCheckedChange={toggleSelectAll}
                          data-testid="select-all-checkbox"
                        />
                      </TableHead>
                      <TableHead>Unit ID</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead>Volume</TableHead>
                      <TableHead>Collection Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUnits.map((unit) => {
                      const isSelected = selectedUnits.some(u => u.id === unit.id);
                      return (
                        <TableRow 
                          key={unit.id} 
                          className={`data-table-row ${isSelected ? 'bg-teal-50 dark:bg-teal-900/20' : ''}`}
                        >
                          <TableCell>
                            <Checkbox
                              checked={isSelected}
                              onCheckedChange={() => toggleSelectUnit(unit)}
                              data-testid={`select-unit-${unit.id}`}
                            />
                          </TableCell>
                          <TableCell className="font-mono">{unit.unit_id}</TableCell>
                          <TableCell>
                            {unit.confirmed_blood_group ? (
                              <span className="blood-group-badge">{unit.confirmed_blood_group}</span>
                            ) : unit.blood_group ? (
                              <span className="blood-group-badge">{unit.blood_group}</span>
                            ) : (
                              <span className="text-slate-400">-</span>
                            )}
                          </TableCell>
                          <TableCell>{unit.volume} mL</TableCell>
                          <TableCell>{unit.collection_date}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              size="sm"
                              onClick={() => {
                                setSelectedUnit(unit);
                                setShowProcessDialog(true);
                              }}
                              className="bg-teal-600 hover:bg-teal-700"
                              data-testid={`process-unit-${unit.id}`}
                            >
                              <Layers className="w-4 h-4 mr-1" />
                              Process
                            </Button>
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

        <TabsContent value="components" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Blood Components</CardTitle>
              <CardDescription>All processed components</CardDescription>
            </CardHeader>
            <CardContent>
              {components.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No components processed yet
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Component ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead>Volume</TableHead>
                      <TableHead>Storage</TableHead>
                      <TableHead>Expiry</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {components.map((comp) => (
                      <TableRow key={comp.id} className="data-table-row">
                        <TableCell className="font-mono">{comp.component_id}</TableCell>
                        <TableCell className="capitalize">{comp.component_type?.replace('_', ' ')}</TableCell>
                        <TableCell>
                          {comp.blood_group && (
                            <span className="blood-group-badge">{comp.blood_group}</span>
                          )}
                        </TableCell>
                        <TableCell>{comp.volume} mL</TableCell>
                        <TableCell className="text-sm">{comp.storage_location || '-'}</TableCell>
                        <TableCell>{comp.expiry_date}</TableCell>
                        <TableCell>
                          <Badge className={statusColors[comp.status]}>
                            {comp.status?.replace('_', ' ')}
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

      {/* Process Dialog */}
      <Dialog open={showProcessDialog} onOpenChange={(open) => { setShowProcessDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-teal-600" />
              Create Component
            </DialogTitle>
          </DialogHeader>
          
          {selectedUnit && (
            <div className="py-2 px-3 bg-slate-50 rounded-lg mb-4">
              <p className="text-sm text-slate-500">Parent Unit</p>
              <p className="font-mono font-medium">{selectedUnit.unit_id}</p>
              {selectedUnit.confirmed_blood_group && (
                <span className="blood-group-badge mt-1">{selectedUnit.confirmed_blood_group}</span>
              )}
            </div>
          )}
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Component Type *</Label>
              <Select 
                value={processForm.component_type}
                onValueChange={(v) => setProcessForm({ ...processForm, component_type: v })}
              >
                <SelectTrigger data-testid="select-component-type">
                  <SelectValue placeholder="Select component type" />
                </SelectTrigger>
                <SelectContent>
                  {componentTypes.map(c => (
                    <SelectItem key={c.value} value={c.value}>
                      <div>
                        <p>{c.label}</p>
                        <p className="text-xs text-slate-500">{c.temp} | {c.expiry} days shelf life</p>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="volume">Volume (mL) *</Label>
              <Input
                id="volume"
                type="number"
                value={processForm.volume}
                onChange={(e) => setProcessForm({ ...processForm, volume: e.target.value })}
                placeholder="e.g., 250"
                data-testid="input-volume"
              />
            </div>

            <div className="space-y-2">
              <Label>Storage Location</Label>
              <Select 
                value={processForm.storage_location}
                onValueChange={(v) => setProcessForm({ ...processForm, storage_location: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select storage location" />
                </SelectTrigger>
                <SelectContent>
                  {storageLocations.map(loc => (
                    <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="batch">Batch ID (Optional)</Label>
              <Input
                id="batch"
                value={processForm.batch_id}
                onChange={(e) => setProcessForm({ ...processForm, batch_id: e.target.value })}
                placeholder="Enter batch ID"
              />
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => { setShowProcessDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateComponent}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={!processForm.component_type || !processForm.volume}
              data-testid="create-component-btn"
            >
              <Plus className="w-4 h-4 mr-1" />
              Create Component
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
