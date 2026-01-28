import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Droplet, MapPin, Search, Building2, Phone, Clock, 
  RefreshCw, Plus, ArrowLeftRight, Map, Navigation,
  AlertTriangle, Package, ExternalLink
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import BloodBankMap from '../components/BloodBankMap';
import MapPicker from '../components/MapPicker';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const COMPONENT_TYPES = [
  { value: 'whole_blood', label: 'Whole Blood' },
  { value: 'prc', label: 'Packed Red Cells' },
  { value: 'ffp', label: 'Fresh Frozen Plasma' },
  { value: 'platelets', label: 'Platelets' },
  { value: 'cryoprecipitate', label: 'Cryoprecipitate' }
];

export default function FindBlood() {
  const { user, token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [orgProfile, setOrgProfile] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [internalInventory, setInternalInventory] = useState({});
  const [showRequestDialog, setShowRequestDialog] = useState(false);
  const [selectedBloodBank, setSelectedBloodBank] = useState(null);
  const [viewMode, setViewMode] = useState('list');
  const [submitting, setSubmitting] = useState(false);

  const [searchParams, setSearchParams] = useState({
    blood_group: 'all',
    component_type: 'all',
    max_distance_km: 100
  });

  const [requestForm, setRequestForm] = useState({
    request_type: 'internal', // internal or external
    blood_group: '',
    component_type: 'whole_blood',
    units_required: 1,
    urgency: 'normal',
    patient_name: '',
    diagnosis: '',
    required_by_date: '',
    notes: '',
    target_org_id: null,
    target_org_name: '',
    delivery_latitude: null,
    delivery_longitude: null,
    delivery_address: ''
  });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Get organization profile for location
      const orgRes = await axios.get(`${API_URL}/organizations/current`, { headers });
      setOrgProfile(orgRes.data);

      // Get internal inventory
      try {
        const invRes = await axios.get(`${API_URL}/inventory/by-blood-group`, { headers });
        setInternalInventory(invRes.data || {});
      } catch (e) {
        console.log('Could not fetch internal inventory');
      }

      // Search for external blood banks if we have location
      if (orgRes.data?.latitude && orgRes.data?.longitude) {
        await searchBloodBanks(orgRes.data.latitude, orgRes.data.longitude);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const searchBloodBanks = async (lat, lng) => {
    try {
      const params = {
        latitude: lat || orgProfile?.latitude,
        longitude: lng || orgProfile?.longitude,
        max_distance_km: searchParams.max_distance_km
      };
      if (searchParams.blood_group !== 'all') {
        params.blood_group = searchParams.blood_group;
      }

      const res = await axios.post(`${API_URL}/blood-link/search`, params);
      // Filter out our own organization
      const filtered = (res.data.blood_banks || []).filter(
        bank => bank.org_id !== user?.org_id
      );
      setSearchResults(filtered);
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  const handleSearch = () => {
    if (orgProfile?.latitude && orgProfile?.longitude) {
      searchBloodBanks(orgProfile.latitude, orgProfile.longitude);
    } else {
      toast.error('Organization location not set. Please update your organization profile.');
    }
  };

  const openRequestDialog = (type, targetOrg = null) => {
    setRequestForm({
      ...requestForm,
      request_type: type,
      target_org_id: targetOrg?.org_id || null,
      target_org_name: targetOrg?.org_name || '',
      delivery_latitude: orgProfile?.latitude || null,
      delivery_longitude: orgProfile?.longitude || null,
      delivery_address: orgProfile?.address || ''
    });
    setSelectedBloodBank(targetOrg);
    setShowRequestDialog(true);
  };

  const handleCreateRequest = async () => {
    if (!requestForm.blood_group || !requestForm.patient_name || !requestForm.required_by_date) {
      toast.error('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      // Map frontend fields to backend BloodRequestCreate model
      const payload = {
        request_type: requestForm.request_type === 'internal' ? 'internal' : 'external',
        requester_name: user?.name || user?.full_name || orgProfile?.contact_person || 'Staff',
        requester_contact: orgProfile?.contact_phone || user?.phone || '',
        hospital_name: orgProfile?.org_name,
        hospital_address: orgProfile?.address,
        patient_name: requestForm.patient_name,
        patient_diagnosis: requestForm.diagnosis,
        blood_group: requestForm.blood_group,
        product_type: requestForm.component_type || 'whole_blood',
        quantity: parseInt(requestForm.units_required) || 1,
        urgency: requestForm.urgency,
        requested_date: new Date().toISOString().split('T')[0],
        required_by_date: requestForm.required_by_date,
        notes: requestForm.notes,
        // Additional fields for tracking
        target_org_id: requestForm.target_org_id,
        target_org_name: requestForm.target_org_name,
        delivery_latitude: requestForm.delivery_latitude,
        delivery_longitude: requestForm.delivery_longitude,
        delivery_address: requestForm.delivery_address,
        requesting_org_id: user?.org_id,
        requesting_org_name: orgProfile?.org_name
      };

      await axios.post(`${API_URL}/requests`, payload, { headers });
      toast.success('Blood request submitted successfully');
      setShowRequestDialog(false);
      resetRequestForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create request');
    } finally {
      setSubmitting(false);
    }
  };

  const resetRequestForm = () => {
    setRequestForm({
      request_type: 'internal',
      blood_group: '',
      component_type: 'whole_blood',
      units_required: 1,
      urgency: 'normal',
      patient_name: '',
      diagnosis: '',
      required_by_date: '',
      notes: '',
      target_org_id: null,
      target_org_name: '',
      delivery_latitude: orgProfile?.latitude || null,
      delivery_longitude: orgProfile?.longitude || null,
      delivery_address: orgProfile?.address || ''
    });
    setSelectedBloodBank(null);
  };

  const handleLocationChange = (location) => {
    setRequestForm(prev => ({
      ...prev,
      delivery_latitude: location.latitude,
      delivery_longitude: location.longitude
    }));
  };

  const getDirections = (bank) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${bank.latitude},${bank.longitude}`;
    window.open(url, '_blank');
  };

  return (
    <div className="p-6 space-y-6" data-testid="find-blood-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Droplet className="w-6 h-6 text-red-600" />
            Find Blood
          </h1>
          <p className="text-slate-600">
            Search for blood within your organization or from the Blood Link network
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            className="bg-red-600 hover:bg-red-700"
            onClick={() => openRequestDialog('internal')}
          >
            <Plus className="w-4 h-4 mr-2" />
            New Request
          </Button>
        </div>
      </div>

      {/* Tabs for Internal vs External */}
      <Tabs defaultValue="internal" className="w-full">
        <TabsList>
          <TabsTrigger value="internal">Internal Inventory</TabsTrigger>
          <TabsTrigger value="external">External Blood Banks</TabsTrigger>
        </TabsList>

        {/* Internal Inventory Tab */}
        <TabsContent value="internal" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-600" />
                Your Organization's Inventory
              </CardTitle>
              <CardDescription>
                Blood stock available within {orgProfile?.org_name || 'your organization'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {Object.keys(internalInventory).length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Package className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p>No inventory data available</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {BLOOD_GROUPS.map(bg => {
                    const data = internalInventory[bg] || {};
                    const total = data.total || 0;
                    return (
                      <Card key={bg} className={`${total > 0 ? 'border-green-200 bg-green-50' : 'border-slate-200'}`}>
                        <CardContent className="pt-4 text-center">
                          <p className="text-2xl font-bold text-slate-800">{bg}</p>
                          <p className={`text-lg font-semibold ${total > 0 ? 'text-green-600' : 'text-slate-400'}`}>
                            {total} units
                          </p>
                          {data.whole_blood > 0 && (
                            <p className="text-xs text-slate-500">WB: {data.whole_blood}</p>
                          )}
                          {data.components > 0 && (
                            <p className="text-xs text-slate-500">Comp: {data.components}</p>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
              <div className="mt-4 flex justify-end">
                <Button onClick={() => openRequestDialog('internal')}>
                  <ArrowLeftRight className="w-4 h-4 mr-2" />
                  Request from Internal Stock
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* External Blood Banks Tab */}
        <TabsContent value="external" className="space-y-4 mt-4">
          {/* Search Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5 text-red-600" />
                Search External Blood Banks
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4 items-end">
                <div>
                  <Label>Blood Group</Label>
                  <Select
                    value={searchParams.blood_group}
                    onValueChange={(v) => setSearchParams({ ...searchParams, blood_group: v })}
                  >
                    <SelectTrigger className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Groups</SelectItem>
                      {BLOOD_GROUPS.map(bg => (
                        <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Max Distance</Label>
                  <Select
                    value={String(searchParams.max_distance_km)}
                    onValueChange={(v) => setSearchParams({ ...searchParams, max_distance_km: parseInt(v) })}
                  >
                    <SelectTrigger className="w-[120px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="25">25 km</SelectItem>
                      <SelectItem value="50">50 km</SelectItem>
                      <SelectItem value="100">100 km</SelectItem>
                      <SelectItem value="200">200 km</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleSearch} disabled={loading}>
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
                <div className="ml-auto flex gap-2">
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                  >
                    List
                  </Button>
                  <Button
                    variant={viewMode === 'map' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('map')}
                  >
                    <Map className="w-4 h-4 mr-1" />
                    Map
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {viewMode === 'map' ? (
            <Card>
              <CardContent className="pt-4">
                <BloodBankMap
                  height="450px"
                  initialUserLocation={orgProfile?.latitude && orgProfile?.longitude 
                    ? [orgProfile.latitude, orgProfile.longitude] 
                    : null}
                  onBloodBankSelect={(bank) => openRequestDialog('external', bank)}
                />
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {searchResults.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Building2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-600">No external blood banks found</p>
                    <p className="text-sm text-slate-500 mt-1">
                      {!orgProfile?.latitude ? 'Set your organization location to search nearby' : 'Try adjusting search filters'}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                searchResults.map(bank => (
                  <Card key={bank.org_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-lg">{bank.org_name}</h3>
                            {bank.is_24x7 && (
                              <Badge className="bg-green-100 text-green-700">24/7</Badge>
                            )}
                            <Badge variant="outline">{bank.distance_km} km</Badge>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">
                            <MapPin className="w-3 h-3 inline mr-1" />
                            {bank.address}, {bank.city}, {bank.state}
                          </p>
                          <div className="flex items-center gap-4 mt-2">
                            <span className={`text-sm font-medium ${bank.total_units > 0 ? 'text-green-600' : 'text-red-500'}`}>
                              {bank.total_units} units available
                            </span>
                            {bank.contact_phone && (
                              <span className="text-sm text-slate-500">
                                <Phone className="w-3 h-3 inline mr-1" />
                                {bank.contact_phone}
                              </span>
                            )}
                          </div>
                          {/* Availability badges */}
                          <div className="flex flex-wrap gap-1 mt-2">
                            {Object.entries(bank.availability || {}).map(([bg, components]) => {
                              const total = Object.values(components).reduce((a, b) => a + b, 0);
                              if (total > 0) {
                                return (
                                  <Badge key={bg} variant="outline" className="text-xs">
                                    {bg}: {total}
                                  </Badge>
                                );
                              }
                              return null;
                            })}
                          </div>
                        </div>
                        <div className="flex flex-col gap-2">
                          <Button 
                            size="sm"
                            onClick={() => openRequestDialog('external', bank)}
                            disabled={bank.total_units === 0}
                          >
                            Request Blood
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => getDirections(bank)}
                          >
                            <Navigation className="w-3 h-3 mr-1" />
                            Directions
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Blood Request Dialog */}
      <Dialog open={showRequestDialog} onOpenChange={setShowRequestDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowLeftRight className="w-5 h-5 text-red-600" />
              Create Blood Request
            </DialogTitle>
            <DialogDescription>
              {requestForm.request_type === 'internal' 
                ? 'Request blood from your organization\'s inventory'
                : `Request blood from ${selectedBloodBank?.org_name || 'external blood bank'}`
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Request Type Toggle */}
            <div>
              <Label className="mb-2 block">Request Type</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={requestForm.request_type === 'internal' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRequestForm({ ...requestForm, request_type: 'internal', target_org_id: null, target_org_name: '' })}
                  className={requestForm.request_type === 'internal' ? 'bg-blue-600 hover:bg-blue-700' : ''}
                >
                  <Package className="w-4 h-4 mr-1" />
                  Internal
                </Button>
                <Button
                  type="button"
                  variant={requestForm.request_type === 'external' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRequestForm({ ...requestForm, request_type: 'external' })}
                  className={requestForm.request_type === 'external' ? 'bg-red-600 hover:bg-red-700' : ''}
                >
                  <Building2 className="w-4 h-4 mr-1" />
                  External
                </Button>
              </div>
            </div>

            {requestForm.request_type === 'external' && selectedBloodBank && (
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="text-sm font-medium">{selectedBloodBank.org_name}</p>
                <p className="text-xs text-slate-500">{selectedBloodBank.address}, {selectedBloodBank.city}</p>
              </div>
            )}

            {/* Blood Details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Blood Group *</Label>
                <Select
                  value={requestForm.blood_group}
                  onValueChange={(v) => setRequestForm({ ...requestForm, blood_group: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {BLOOD_GROUPS.map(bg => (
                      <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Units Required *</Label>
                <Input
                  type="number"
                  min="1"
                  value={requestForm.units_required}
                  onChange={(e) => setRequestForm({ ...requestForm, units_required: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Component Type</Label>
                <Select
                  value={requestForm.component_type}
                  onValueChange={(v) => setRequestForm({ ...requestForm, component_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {COMPONENT_TYPES.map(ct => (
                      <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Urgency</Label>
                <Select
                  value={requestForm.urgency}
                  onValueChange={(v) => setRequestForm({ ...requestForm, urgency: v })}
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

            {/* Patient Info */}
            <div>
              <Label>Patient Name *</Label>
              <Input
                value={requestForm.patient_name}
                onChange={(e) => setRequestForm({ ...requestForm, patient_name: e.target.value })}
                placeholder="Patient name"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Diagnosis/Reason</Label>
                <Input
                  value={requestForm.diagnosis}
                  onChange={(e) => setRequestForm({ ...requestForm, diagnosis: e.target.value })}
                  placeholder="Reason for request"
                />
              </div>
              <div>
                <Label>Required By Date *</Label>
                <Input
                  type="date"
                  value={requestForm.required_by_date}
                  onChange={(e) => setRequestForm({ ...requestForm, required_by_date: e.target.value })}
                />
              </div>
            </div>

            {/* External request - delivery location */}
            {requestForm.request_type === 'external' && (
              <div className="border-t pt-4">
                <Label className="flex items-center gap-2 mb-2">
                  <MapPin className="w-4 h-4" />
                  Delivery Location
                </Label>
                <MapPicker
                  initialPosition={requestForm.delivery_latitude && requestForm.delivery_longitude 
                    ? [requestForm.delivery_latitude, requestForm.delivery_longitude] 
                    : null}
                  onLocationChange={handleLocationChange}
                  height="200px"
                  showSearch={true}
                  showCurrentLocation={true}
                  showCoordinates={true}
                />
                <div className="mt-2">
                  <Label>Delivery Address</Label>
                  <Textarea
                    value={requestForm.delivery_address}
                    onChange={(e) => setRequestForm({ ...requestForm, delivery_address: e.target.value })}
                    placeholder="Full delivery address"
                    className="min-h-[60px]"
                  />
                </div>
              </div>
            )}

            <div>
              <Label>Notes</Label>
              <Textarea
                value={requestForm.notes}
                onChange={(e) => setRequestForm({ ...requestForm, notes: e.target.value })}
                placeholder="Additional notes"
              />
            </div>
          </div>

          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setShowRequestDialog(false)}>Cancel</Button>
            <Button 
              className="bg-red-600 hover:bg-red-700"
              onClick={handleCreateRequest}
              disabled={submitting}
            >
              {submitting ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : null}
              Submit Request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
