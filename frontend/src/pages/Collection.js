import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { donorAPI, screeningAPI, donationAPI, labelAPI, donationSessionAPI } from '../lib/api';
import { toast } from 'sonner';
import { 
  Search, Droplet, Clock, CheckCircle, AlertTriangle, Printer, 
  RefreshCw, Users, Activity, ChevronRight, Beaker, Heart, XCircle,
  Filter, UserX, Calendar, Ban
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import LabelPrintDialog from '../components/LabelPrintDialog';

// Status badge styles
const STATUS_BADGES = {
  eligible: { bg: 'bg-emerald-100 text-emerald-700', icon: CheckCircle, label: 'Eligible' },
  deactivated: { bg: 'bg-slate-100 text-slate-500', icon: Ban, label: 'Deactivated' },
  deferred: { bg: 'bg-red-100 text-red-700', icon: XCircle, label: 'Deferred' },
  not_eligible: { bg: 'bg-amber-100 text-amber-700', icon: Clock, label: 'Not Eligible' },
  age_restriction: { bg: 'bg-orange-100 text-orange-700', icon: UserX, label: 'Age Restriction' },
  in_progress: { bg: 'bg-blue-100 text-blue-700', icon: Activity, label: 'In Progress' },
};

export default function Collection() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  
  // Lists
  const [allDonors, setAllDonors] = useState([]);
  const [todayDonations, setTodayDonations] = useState([]);
  const [todaySummary, setTodaySummary] = useState(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterBloodGroup, setFilterBloodGroup] = useState('all');
  
  // Selected donor for collection
  const [donor, setDonor] = useState(null);
  const [screening, setScreening] = useState(null);
  const [activeDonation, setActiveDonation] = useState(null);
  const [showCollectionForm, setShowCollectionForm] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [completionResult, setCompletionResult] = useState(null);
  const [showLabelDialog, setShowLabelDialog] = useState(false);
  const [labelData, setLabelData] = useState(null);

  const [startForm, setStartForm] = useState({
    donation_type: 'whole_blood',
  });

  const [completeForm, setCompleteForm] = useState({
    volume: '',
    adverse_reaction: false,
    adverse_reaction_details: '',
  });

  useEffect(() => {
    fetchData();
    const donorId = searchParams.get('donor');
    const screeningId = searchParams.get('screening');
    if (donorId && screeningId) {
      fetchDonorAndStartCollection(donorId, screeningId);
    }
  }, [searchParams]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [donorsRes, donationsRes, summaryRes] = await Promise.all([
        donorAPI.getDonorsWithStatus({ is_active: 'all' }),
        donationAPI.getTodayDonations(),
        donationAPI.getTodaySummary(),
      ]);
      setAllDonors(donorsRes.data || []);
      setTodayDonations(donationsRes.data || []);
      setTodaySummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to fetch collection data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDonorAndStartCollection = async (donorId, screeningId) => {
    try {
      const [donorRes, screeningRes] = await Promise.all([
        donorAPI.getById(donorId),
        screeningAPI.getById(screeningId)
      ]);
      setDonor(donorRes.data);
      setScreening(screeningRes.data);
      setShowCollectionForm(true);
    } catch (error) {
      toast.error('Failed to fetch donor data');
    }
  };

  const handleSelectDonor = async (donorData) => {
    if (donorData.eligibility_status !== 'eligible') {
      toast.error(`Cannot start collection: ${donorData.eligibility_reason || 'Not eligible'}`);
      return;
    }
    
    try {
      // Get latest eligible screening
      const screeningsRes = await screeningAPI.getAll({ donor_id: donorData.id });
      const eligibleScreening = screeningsRes.data.find(s => s.eligibility_status === 'eligible');
      
      if (!eligibleScreening) {
        toast.error('No eligible screening found. Please complete screening first.');
        return;
      }
      
      setDonor(donorData);
      setScreening(eligibleScreening);
      setShowCollectionForm(true);
    } catch (error) {
      toast.error('Failed to fetch screening data');
    }
  };

  const handleStartCollection = async () => {
    if (!donor || !screening) {
      toast.error('Donor and screening are required');
      return;
    }

    setLoading(true);
    try {
      const response = await donationAPI.create({
        donor_id: donor.id,
        screening_id: screening.id,
        donation_type: startForm.donation_type,
        collection_start_time: new Date().toISOString(),
      });
      
      setActiveDonation(response.data);
      toast.success(`Collection started! Donation ID: ${response.data.donation_id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start collection');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteCollection = async () => {
    if (!activeDonation) return;

    setLoading(true);
    try {
      const response = await donationAPI.complete(activeDonation.id, {
        volume: parseFloat(completeForm.volume),
        adverse_reaction: completeForm.adverse_reaction,
        adverse_reaction_details: completeForm.adverse_reaction_details || undefined,
      });
      
      setCompletionResult(response.data);
      setShowCompleteDialog(true);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete collection');
    } finally {
      setLoading(false);
    }
  };

  const handlePrintLabel = async () => {
    if (!completionResult?.unit_id) return;
    try {
      const response = await labelAPI.getBloodUnitLabel(completionResult.unit_id);
      setLabelData(response.data);
      setShowLabelDialog(true);
    } catch (error) {
      toast.error('Failed to fetch label data');
    }
  };

  const handleCloseForm = () => {
    setShowCollectionForm(false);
    setDonor(null);
    setScreening(null);
    setActiveDonation(null);
    setStartForm({ donation_type: 'whole_blood' });
    setCompleteForm({ volume: '', adverse_reaction: false, adverse_reaction_details: '' });
  };

  // Filter donors
  const filteredDonors = allDonors.filter(d => {
    // Search filter
    if (searchTerm && 
        !d.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !d.donor_id?.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !d.phone?.includes(searchTerm)) {
      return false;
    }
    
    // Status filter
    if (filterStatus === 'eligible' && d.eligibility_status !== 'eligible') return false;
    if (filterStatus === 'not_eligible' && d.eligibility_status === 'eligible') return false;
    
    // Blood group filter
    if (filterBloodGroup !== 'all' && d.blood_group !== filterBloodGroup) return false;
    
    return true;
  });

  // Count by status
  const statusCounts = {
    total: allDonors.length,
    eligible: allDonors.filter(d => d.eligibility_status === 'eligible').length,
    not_eligible: allDonors.filter(d => d.eligibility_status !== 'eligible').length,
  };

  const renderStatusBadge = (status, reason) => {
    const config = STATUS_BADGES[status] || STATUS_BADGES.not_eligible;
    const Icon = config.icon;
    
    return (
      <div className="flex flex-col">
        <Badge className={config.bg}>
          <Icon className="w-3 h-3 mr-1" />
          {config.label}
        </Badge>
        {reason && <span className="text-xs text-slate-500 mt-1 max-w-[200px] truncate">{reason}</span>}
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="collection-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Blood Collection</h1>
          <p className="page-subtitle">Manage blood donation collection process</p>
        </div>
        <Button variant="outline" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Today's Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-teal-50 to-teal-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-teal-600">Total Donors</p>
                <p className="text-2xl font-bold text-teal-700">{statusCounts.total}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-teal-200 flex items-center justify-center">
                <Users className="w-6 h-6 text-teal-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Eligible</p>
                <p className="text-2xl font-bold text-emerald-700">{statusCounts.eligible}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-emerald-200 flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Today's Collections</p>
                <p className="text-2xl font-bold text-blue-700">{todaySummary?.total || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-blue-200 flex items-center justify-center">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600">In Progress</p>
                <p className="text-2xl font-bold text-amber-700">{todaySummary?.in_progress || 0}</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-amber-200 flex items-center justify-center">
                <Clock className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-50 to-red-100">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600">Total Volume</p>
                <p className="text-2xl font-bold text-red-700">{todaySummary?.total_volume || 0} mL</p>
              </div>
              <div className="w-12 h-12 rounded-full bg-red-200 flex items-center justify-center">
                <Droplet className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search by donor ID, name, or phone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[150px]">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="eligible">Eligible Only</SelectItem>
              <SelectItem value="not_eligible">Not Eligible</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterBloodGroup} onValueChange={setFilterBloodGroup}>
            <SelectTrigger className="w-[130px]">
              <Droplet className="w-4 h-4 mr-2" />
              <SelectValue placeholder="Blood" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Blood</SelectItem>
              {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                <SelectItem key={bg} value={bg}>{bg}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="all" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            All Donors ({filteredDonors.length})
          </TabsTrigger>
          <TabsTrigger value="today" className="flex items-center gap-2">
            <Beaker className="w-4 h-4" />
            Today ({todayDonations.length})
          </TabsTrigger>
        </TabsList>

        {/* All Donors Tab */}
        <TabsContent value="all" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>All Donors with Eligibility Status</CardTitle>
              <CardDescription>
                View all donors and their current eligibility for blood donation
              </CardDescription>
            </CardHeader>
            <CardContent>
              {filteredDonors.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Users className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No donors match your filters</p>
                </div>
              ) : (
                <ScrollArea className="h-[450px]">
                  <Table className="table-dense">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Donor ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Age</TableHead>
                        <TableHead>Blood Group</TableHead>
                        <TableHead>Phone</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Eligible Date</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredDonors.map((d) => (
                        <TableRow key={d.id} className={d.eligibility_status === 'eligible' ? 'bg-emerald-50/30' : ''}>
                          <TableCell className="font-mono text-sm">{d.donor_id}</TableCell>
                          <TableCell className="font-medium">{d.full_name}</TableCell>
                          <TableCell>
                            <span className={`text-sm ${d.age < 18 || d.age > 65 ? 'text-red-600 font-medium' : ''}`}>
                              {d.age} yrs
                            </span>
                          </TableCell>
                          <TableCell>
                            {d.blood_group ? (
                              <span className="blood-group-badge">{d.blood_group}</span>
                            ) : (
                              <span className="text-slate-400">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-sm text-slate-600">{d.phone || '-'}</TableCell>
                          <TableCell>
                            {renderStatusBadge(d.eligibility_status, d.eligibility_reason)}
                          </TableCell>
                          <TableCell className="text-sm">
                            {d.eligible_date || '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            {d.eligibility_status === 'eligible' ? (
                              <Button 
                                size="sm" 
                                onClick={() => handleSelectDonor(d)}
                                className="bg-teal-600 hover:bg-teal-700"
                              >
                                Select
                                <ChevronRight className="w-4 h-4 ml-1" />
                              </Button>
                            ) : (
                              <Button size="sm" variant="ghost" disabled>
                                Not Available
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Today's Collections Tab */}
        <TabsContent value="today" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Today's Collections</CardTitle>
              <CardDescription>
                Donations collected on {new Date().toLocaleDateString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {todayDonations.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Droplet className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No collections today yet</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <Table className="table-dense">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Time</TableHead>
                        <TableHead>Donation ID</TableHead>
                        <TableHead>Donor</TableHead>
                        <TableHead>Blood Group</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Volume</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {todayDonations.map((d) => (
                        <TableRow key={d.id}>
                          <TableCell className="text-sm text-slate-600">
                            {d.collection_start_time ? new Date(d.collection_start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                          </TableCell>
                          <TableCell className="font-mono text-sm">{d.donation_id}</TableCell>
                          <TableCell className="font-medium">{d.donor_name || '-'}</TableCell>
                          <TableCell>
                            {d.blood_group ? (
                              <span className="blood-group-badge">{d.blood_group}</span>
                            ) : (
                              <span className="text-slate-400">-</span>
                            )}
                          </TableCell>
                          <TableCell className="capitalize text-sm">{d.donation_type?.replace('_', ' ') || '-'}</TableCell>
                          <TableCell className="text-sm">
                            {d.volume_collected ? `${d.volume_collected} mL` : '-'}
                          </TableCell>
                          <TableCell>
                            <Badge className={
                              d.status === 'completed' 
                                ? 'bg-emerald-100 text-emerald-700' 
                                : 'bg-amber-100 text-amber-700'
                            }>
                              {d.status === 'completed' ? (
                                <><CheckCircle className="w-3 h-3 mr-1" /> Completed</>
                              ) : (
                                <><Clock className="w-3 h-3 mr-1" /> In Progress</>
                              )}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            {d.status === 'completed' && (
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => navigate(`/traceability?unit=${d.donation_id}`)}
                              >
                                View Unit
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Collection Form Dialog */}
      <Dialog open={showCollectionForm} onOpenChange={setShowCollectionForm}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Droplet className="w-5 h-5 text-red-600" />
              Blood Collection
            </DialogTitle>
          </DialogHeader>
          
          {/* Selected Donor Info */}
          {donor && screening && (
            <Card className="border-l-4 border-l-emerald-500">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <p className="font-semibold">{donor.full_name}</p>
                      <p className="text-sm text-slate-500 font-mono">{donor.donor_id}</p>
                    </div>
                    {(donor.blood_group || screening.preliminary_blood_group) && (
                      <span className="blood-group-badge ml-4">{donor.blood_group || screening.preliminary_blood_group}</span>
                    )}
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-slate-500">Hemoglobin</p>
                    <p className="font-semibold text-emerald-600">{screening.hemoglobin} g/dL</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Start Collection Form */}
          {donor && screening && !activeDonation && (
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Donation Type</Label>
                <Select 
                  value={startForm.donation_type} 
                  onValueChange={(v) => setStartForm({ ...startForm, donation_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="whole_blood">Whole Blood</SelectItem>
                    <SelectItem value="apheresis_platelets">Apheresis Platelets</SelectItem>
                    <SelectItem value="apheresis_plasma">Apheresis Plasma</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={handleCloseForm}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleStartCollection}
                  className="bg-red-600 hover:bg-red-700"
                  disabled={loading}
                >
                  {loading && <RefreshCw className="w-4 h-4 mr-2 animate-spin" />}
                  <Droplet className="w-4 h-4 mr-2" />
                  Start Collection
                </Button>
              </DialogFooter>
            </div>
          )}

          {/* Active Collection - Complete Form */}
          {activeDonation && (
            <div className="space-y-4 mt-4">
              <Card className="bg-amber-50 border-amber-200">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 text-amber-700">
                    <Clock className="w-5 h-5 animate-pulse" />
                    <span className="font-medium">Collection in Progress</span>
                    <span className="ml-auto font-mono">{activeDonation.donation_id}</span>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-2">
                <Label htmlFor="volume">Volume Collected (mL) *</Label>
                <Input
                  id="volume"
                  type="number"
                  value={completeForm.volume}
                  onChange={(e) => setCompleteForm({ ...completeForm, volume: e.target.value })}
                  placeholder="450"
                  required
                />
                <p className="text-xs text-slate-500">Standard whole blood donation: 450 mL</p>
              </div>

              <div className="pt-4 border-t">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="adverse"
                    checked={completeForm.adverse_reaction}
                    onCheckedChange={(checked) => setCompleteForm({ ...completeForm, adverse_reaction: checked })}
                  />
                  <div className="grid gap-1.5 leading-none">
                    <label htmlFor="adverse" className="text-sm font-medium cursor-pointer">
                      Adverse Reaction Occurred
                    </label>
                    <p className="text-sm text-slate-500">
                      Check if the donor experienced any adverse reaction during donation
                    </p>
                  </div>
                </div>
              </div>

              {completeForm.adverse_reaction && (
                <div className="space-y-2">
                  <Label htmlFor="reaction_details">Reaction Details</Label>
                  <Textarea
                    id="reaction_details"
                    value={completeForm.adverse_reaction_details}
                    onChange={(e) => setCompleteForm({ ...completeForm, adverse_reaction_details: e.target.value })}
                    placeholder="Describe the adverse reaction..."
                    rows={3}
                  />
                </div>
              )}

              <DialogFooter className="mt-4">
                <Button variant="outline" onClick={handleCloseForm}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleCompleteCollection}
                  className="bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading || !completeForm.volume}
                >
                  {loading && <RefreshCw className="w-4 h-4 mr-2 animate-spin" />}
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Complete Collection
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Completion Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              Collection Completed
            </DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <p className="text-slate-600">
              Blood collection has been completed successfully!
            </p>
            <div className="bg-slate-50 p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Unit ID:</span>
                <span className="font-mono font-bold">{completionResult?.unit_id}</span>
              </div>
            </div>
          </div>
          <DialogFooter className="flex gap-2 sm:gap-2">
            <Button variant="outline" onClick={() => navigate('/traceability')}>
              View Traceability
            </Button>
            <Button 
              variant="outline"
              onClick={handlePrintLabel}
              className="border-teal-600 text-teal-600 hover:bg-teal-50"
            >
              <Printer className="w-4 h-4 mr-1" />
              Print Label
            </Button>
            <Button 
              onClick={() => {
                setShowCompleteDialog(false);
                handleCloseForm();
              }}
              className="bg-teal-600 hover:bg-teal-700"
            >
              New Collection
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Label Print Dialog */}
      <LabelPrintDialog 
        open={showLabelDialog}
        onOpenChange={setShowLabelDialog}
        labelData={labelData}
        title="Print Blood Pack Label"
      />
    </div>
  );
}
