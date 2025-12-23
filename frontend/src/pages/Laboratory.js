import React, { useState, useEffect } from 'react';
import { bloodUnitAPI, labTestAPI } from '../lib/api';
import { toast } from 'sonner';
import { FlaskConical, Search, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const testMethods = ['ELISA', 'CLIA', 'NAT'];
const screeningResults = [
  { value: 'non_reactive', label: 'Non-Reactive' },
  { value: 'gray', label: 'Gray Zone' },
  { value: 'reactive', label: 'Reactive' },
];

export default function Laboratory() {
  const [units, setUnits] = useState([]);
  const [labTests, setLabTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [showTestDialog, setShowTestDialog] = useState(false);

  const [testForm, setTestForm] = useState({
    confirmed_blood_group: '',
    verified_by_1: '',
    verified_by_2: '',
    hiv_result: '',
    hbsag_result: '',
    hcv_result: '',
    syphilis_result: '',
    test_method: 'ELISA',
    test_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [unitsRes, testsRes] = await Promise.all([
        bloodUnitAPI.getAll({ status: 'collected' }),
        labTestAPI.getAll()
      ]);
      setUnits(unitsRes.data);
      setLabTests(testsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitTest = async () => {
    if (!selectedUnit) return;

    try {
      const response = await labTestAPI.create({
        unit_id: selectedUnit.id,
        ...testForm,
        confirmed_blood_group: testForm.confirmed_blood_group || undefined,
        verified_by_1: testForm.verified_by_1 || undefined,
        verified_by_2: testForm.verified_by_2 || undefined,
        hiv_result: testForm.hiv_result || undefined,
        hbsag_result: testForm.hbsag_result || undefined,
        hcv_result: testForm.hcv_result || undefined,
        syphilis_result: testForm.syphilis_result || undefined,
      });
      
      toast.success(`Test recorded. Overall status: ${response.data.overall_status}`);
      setShowTestDialog(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit test');
    }
  };

  const resetForm = () => {
    setTestForm({
      confirmed_blood_group: '',
      verified_by_1: '',
      verified_by_2: '',
      hiv_result: '',
      hbsag_result: '',
      hcv_result: '',
      syphilis_result: '',
      test_method: 'ELISA',
      test_date: new Date().toISOString().split('T')[0],
    });
    setSelectedUnit(null);
  };

  const getResultBadge = (result) => {
    if (!result) return <span className="text-slate-400">-</span>;
    const colors = {
      non_reactive: 'bg-emerald-100 text-emerald-700',
      gray: 'bg-amber-100 text-amber-700',
      reactive: 'bg-red-100 text-red-700',
    };
    return (
      <Badge className={colors[result]}>
        {result === 'non_reactive' ? 'NR' : result === 'gray' ? 'Gray' : 'R'}
      </Badge>
    );
  };

  const filteredUnits = units.filter(u => 
    !searchTerm || 
    u.unit_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in" data-testid="laboratory-page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Laboratory Testing</h1>
        <p className="page-subtitle">Blood group confirmation and infectious disease screening</p>
      </div>

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">Pending Tests</TabsTrigger>
          <TabsTrigger value="completed">Completed Tests</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="mt-4 space-y-4">
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

          {/* Units awaiting testing */}
          <Card>
            <CardHeader>
              <CardTitle>Units Awaiting Testing</CardTitle>
              <CardDescription>Blood units that need laboratory testing</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : filteredUnits.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No units awaiting testing
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Unit ID</TableHead>
                      <TableHead>Prelim. Blood Group</TableHead>
                      <TableHead>Collection Date</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUnits.map((unit) => (
                      <TableRow key={unit.id} className="data-table-row">
                        <TableCell className="font-mono">{unit.unit_id}</TableCell>
                        <TableCell>
                          {unit.blood_group ? (
                            <span className="blood-group-badge">{unit.blood_group}</span>
                          ) : (
                            <span className="text-slate-400">Unknown</span>
                          )}
                        </TableCell>
                        <TableCell>{unit.collection_date}</TableCell>
                        <TableCell>{unit.current_location}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedUnit(unit);
                              if (unit.blood_group) {
                                setTestForm(prev => ({ ...prev, confirmed_blood_group: unit.blood_group }));
                              }
                              setShowTestDialog(true);
                            }}
                            className="bg-teal-600 hover:bg-teal-700"
                            data-testid={`test-unit-${unit.id}`}
                          >
                            <FlaskConical className="w-4 h-4 mr-1" />
                            Enter Results
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

        <TabsContent value="completed" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Completed Tests</CardTitle>
              <CardDescription>Recent laboratory test results</CardDescription>
            </CardHeader>
            <CardContent>
              {labTests.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No completed tests
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Unit ID</TableHead>
                      <TableHead>Test Date</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead>HIV</TableHead>
                      <TableHead>HBsAg</TableHead>
                      <TableHead>HCV</TableHead>
                      <TableHead>Syphilis</TableHead>
                      <TableHead>Overall</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {labTests.map((test) => (
                      <TableRow key={test.id} className="data-table-row">
                        <TableCell className="font-mono">{test.unit_id?.slice(0, 20)}...</TableCell>
                        <TableCell>{test.test_date}</TableCell>
                        <TableCell>
                          {test.confirmed_blood_group && (
                            <span className="blood-group-badge">{test.confirmed_blood_group}</span>
                          )}
                        </TableCell>
                        <TableCell>{getResultBadge(test.hiv_result)}</TableCell>
                        <TableCell>{getResultBadge(test.hbsag_result)}</TableCell>
                        <TableCell>{getResultBadge(test.hcv_result)}</TableCell>
                        <TableCell>{getResultBadge(test.syphilis_result)}</TableCell>
                        <TableCell>
                          <Badge className={
                            test.overall_status === 'non_reactive' ? 'bg-emerald-100 text-emerald-700' :
                            test.overall_status === 'reactive' ? 'bg-red-100 text-red-700' :
                            'bg-amber-100 text-amber-700'
                          }>
                            {test.overall_status}
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

      {/* Test Entry Dialog */}
      <Dialog open={showTestDialog} onOpenChange={(open) => { setShowTestDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-teal-600" />
              Enter Lab Results - {selectedUnit?.unit_id}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Blood Group Confirmation */}
            <div className="space-y-4 p-4 bg-slate-50 rounded-lg">
              <h3 className="font-medium">Blood Group Confirmation (Double Verification)</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Confirmed Blood Group</Label>
                  <Select 
                    value={testForm.confirmed_blood_group}
                    onValueChange={(v) => setTestForm({ ...testForm, confirmed_blood_group: v })}
                  >
                    <SelectTrigger>
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
                  <Label>Verified By (1st)</Label>
                  <Input
                    value={testForm.verified_by_1}
                    onChange={(e) => setTestForm({ ...testForm, verified_by_1: e.target.value })}
                    placeholder="Staff ID"
                    data-testid="input-verified-1"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Verified By (2nd)</Label>
                  <Input
                    value={testForm.verified_by_2}
                    onChange={(e) => setTestForm({ ...testForm, verified_by_2: e.target.value })}
                    placeholder="Staff ID"
                    data-testid="input-verified-2"
                  />
                </div>
              </div>
            </div>

            {/* Infectious Disease Screening */}
            <div className="space-y-4 p-4 bg-slate-50 rounded-lg">
              <h3 className="font-medium">Infectious Disease Screening</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>HIV Result</Label>
                  <Select 
                    value={testForm.hiv_result}
                    onValueChange={(v) => setTestForm({ ...testForm, hiv_result: v })}
                  >
                    <SelectTrigger data-testid="select-hiv">
                      <SelectValue placeholder="Select result" />
                    </SelectTrigger>
                    <SelectContent>
                      {screeningResults.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>HBsAg Result</Label>
                  <Select 
                    value={testForm.hbsag_result}
                    onValueChange={(v) => setTestForm({ ...testForm, hbsag_result: v })}
                  >
                    <SelectTrigger data-testid="select-hbsag">
                      <SelectValue placeholder="Select result" />
                    </SelectTrigger>
                    <SelectContent>
                      {screeningResults.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>HCV Result</Label>
                  <Select 
                    value={testForm.hcv_result}
                    onValueChange={(v) => setTestForm({ ...testForm, hcv_result: v })}
                  >
                    <SelectTrigger data-testid="select-hcv">
                      <SelectValue placeholder="Select result" />
                    </SelectTrigger>
                    <SelectContent>
                      {screeningResults.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Syphilis Result</Label>
                  <Select 
                    value={testForm.syphilis_result}
                    onValueChange={(v) => setTestForm({ ...testForm, syphilis_result: v })}
                  >
                    <SelectTrigger data-testid="select-syphilis">
                      <SelectValue placeholder="Select result" />
                    </SelectTrigger>
                    <SelectContent>
                      {screeningResults.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Test Method */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Test Method</Label>
                <Select 
                  value={testForm.test_method}
                  onValueChange={(v) => setTestForm({ ...testForm, test_method: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {testMethods.map(m => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Test Date</Label>
                <Input
                  type="date"
                  value={testForm.test_date}
                  onChange={(e) => setTestForm({ ...testForm, test_date: e.target.value })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowTestDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmitTest}
              className="bg-teal-600 hover:bg-teal-700"
              data-testid="submit-test-btn"
            >
              Submit Results
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
