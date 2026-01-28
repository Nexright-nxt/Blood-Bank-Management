import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Droplet, Clock, CheckCircle, XCircle, Plus, 
  RefreshCw, Building2, Phone, Mail, MapPin,
  AlertCircle, Package, TrendingUp, Map, Navigation, Truck
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import MapPicker from '../components/MapPicker';
import BloodBankMap from '../components/BloodBankMap';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const COMPONENT_TYPES = [
  { value: 'whole_blood', label: 'Whole Blood' },
  { value: 'prc', label: 'Packed Red Cells (PRC)' },
  { value: 'ffp', label: 'Fresh Frozen Plasma (FFP)' },
  { value: 'platelets', label: 'Platelets' },
  { value: 'cryoprecipitate', label: 'Cryoprecipitate' }
];
const URGENCY_LEVELS = [
  { value: 'normal', label: 'Normal', color: 'bg-slate-100 text-slate-700' },
  { value: 'urgent', label: 'Urgent', color: 'bg-orange-100 text-orange-700' },
  { value: 'emergency', label: 'Emergency', color: 'bg-red-100 text-red-700' }
];

export default function RequestorDashboard() {
  const { user, token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [profile, setProfile] = useState(null);
  const [requests, setRequests] = useState([]);
  const [availability, setAvailability] = useState({});
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [showMapView, setShowMapView] = useState(false);
  const [requestForm, setRequestForm] = useState({
    blood_group: '',
    component_type: 'whole_blood',
    units_required: 1,
    urgency: 'normal',
    patient_name: '',
    patient_age: '',
    patient_gender: 'male',
    diagnosis: '',
    hospital_name: '',
    doctor_name: '',
    required_by_date: '',
    notes: '',
    // Location fields
    location_type: 'delivery', // delivery or pickup
    delivery_latitude: null,
    delivery_longitude: null,
    delivery_address: ''
  });

  const api = axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}` }
  });

  useEffect(() => {
    fetchData();
  }, []);

  // Auto-fill location from profile when profile loads
  useEffect(() => {
    if (profile) {
      setRequestForm(prev => ({
        ...prev,
        hospital_name: profile.organization_name || prev.hospital_name,
        delivery_latitude: profile.latitude || prev.delivery_latitude,
        delivery_longitude: profile.longitude || prev.delivery_longitude,
        delivery_address: profile.address ? `${profile.address}, ${profile.city}, ${profile.state}` : prev.delivery_address
      }));
    }
  }, [profile]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Use requestor-specific endpoints
      const [profileRes, requestsRes] = await Promise.all([
        api.get('/requestors/me/profile'),
        api.get('/requestors/me/requests')
      ]);
      setProfile(profileRes.data);
      setRequests(requestsRes.data);
      
      // Try to get public blood availability from blood-link
      try {
        const availRes = await axios.get(`${API_URL}/blood-link/blood-groups`);
        setAvailability(availRes.data || {});
      } catch (e) {
        console.log('Could not fetch public availability');
        setAvailability({});
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
    toast.success('Data refreshed');
  };

  const handleCreateRequest = async () => {
    if (!requestForm.blood_group || !requestForm.patient_name || !requestForm.required_by_date) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await api.post('/requests', {
        ...requestForm,
        units_required: parseInt(requestForm.units_required),
        patient_age: requestForm.patient_age ? parseInt(requestForm.patient_age) : null,
        requestor_org_name: profile?.organization_name,
        // Include location data
        location_type: requestForm.location_type,
        delivery_latitude: requestForm.delivery_latitude,
        delivery_longitude: requestForm.delivery_longitude,
        delivery_address: requestForm.delivery_address
      });
      toast.success('Blood request submitted successfully');
      setShowNewRequest(false);
      setRequestForm({
        blood_group: '',
        component_type: 'whole_blood',
        units_required: 1,
        urgency: 'normal',
        patient_name: '',
        patient_age: '',
        patient_gender: 'male',
        diagnosis: '',
        hospital_name: profile?.organization_name || '',
        doctor_name: '',
        required_by_date: '',
        notes: '',
        location_type: 'delivery',
        delivery_latitude: profile?.latitude || null,
        delivery_longitude: profile?.longitude || null,
        delivery_address: profile?.address ? `${profile.address}, ${profile.city}, ${profile.state}` : ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create request');
    }
  };

  const handleLocationChange = (location) => {
    setRequestForm(prev => ({
      ...prev,
      delivery_latitude: location.latitude,
      delivery_longitude: location.longitude
    }));
  };

  const useProfileLocation = () => {
    if (profile?.latitude && profile?.longitude) {
      setRequestForm(prev => ({
        ...prev,
        delivery_latitude: profile.latitude,
        delivery_longitude: profile.longitude,
        delivery_address: `${profile.address}, ${profile.city}, ${profile.state}`
      }));
      toast.success('Using registered location');
    } else {
      toast.error('No registered location found');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-700',
      approved: 'bg-blue-100 text-blue-700',
      fulfilled: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700',
      cancelled: 'bg-slate-100 text-slate-700'
    };
    return <Badge className={styles[status] || 'bg-slate-100'}>{status}</Badge>;
  };

  const myRequests = requests.filter(r => r.requestor_id === user?.requestor_id || r.created_by === user?.id);
  const pendingCount = myRequests.filter(r => r.status === 'pending').length;
  const approvedCount = myRequests.filter(r => r.status === 'approved').length;
  const fulfilledCount = myRequests.filter(r => r.status === 'fulfilled').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-red-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" data-testid="requestor-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Requestor Dashboard</h1>
          <p className="text-slate-600">
            Welcome, {profile?.organization_name || user?.requestor_org_name}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            variant="outline"
            onClick={() => setShowMapView(true)}
            data-testid="map-view-btn"
          >
            <Map className="w-4 h-4 mr-2" />
            Find Blood Banks
          </Button>
          <Button 
            className="bg-red-600 hover:bg-red-700"
            onClick={() => setShowNewRequest(true)}
            data-testid="new-request-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Request
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Pending</p>
                <p className="text-2xl font-bold text-slate-800">{pendingCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Approved</p>
                <p className="text-2xl font-bold text-slate-800">{approvedCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Package className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Fulfilled</p>
                <p className="text-2xl font-bold text-slate-800">{fulfilledCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Requests</p>
                <p className="text-2xl font-bold text-slate-800">{myRequests.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="requests" className="space-y-4">
        <TabsList>
          <TabsTrigger value="requests">My Requests</TabsTrigger>
          <TabsTrigger value="availability">Blood Availability</TabsTrigger>
          <TabsTrigger value="profile">My Profile</TabsTrigger>
        </TabsList>

        {/* Requests Tab */}
        <TabsContent value="requests">
          <Card>
            <CardHeader>
              <CardTitle>Blood Requests</CardTitle>
              <CardDescription>Track your blood requests and their status</CardDescription>
            </CardHeader>
            <CardContent>
              {myRequests.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Droplet className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p>No blood requests yet</p>
                  <Button 
                    className="mt-4 bg-red-600 hover:bg-red-700"
                    onClick={() => setShowNewRequest(true)}
                  >
                    Create Your First Request
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {myRequests.map((request) => (
                    <div 
                      key={request.id} 
                      className="border rounded-lg p-4 hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex flex-col sm:flex-row justify-between gap-4">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm text-slate-500">
                              {request.request_id}
                            </span>
                            {getStatusBadge(request.status)}
                            <Badge className={URGENCY_LEVELS.find(u => u.value === request.urgency)?.color}>
                              {request.urgency}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="font-semibold text-red-600">
                              {request.blood_group} • {request.units_required} unit(s)
                            </span>
                            <span className="text-slate-500">
                              {request.component_type?.replace('_', ' ')}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600">
                            Patient: {request.patient_name}
                            {request.diagnosis && ` • ${request.diagnosis}`}
                          </p>
                        </div>
                        <div className="text-right text-sm text-slate-500">
                          <p>Required by: {request.required_by_date || 'Not specified'}</p>
                          <p>Created: {new Date(request.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Availability Tab */}
        <TabsContent value="availability">
          <Card>
            <CardHeader>
              <CardTitle>Blood Availability</CardTitle>
              <CardDescription>Current blood stock by blood group</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {BLOOD_GROUPS.map((group) => {
                  const data = availability[group] || { whole_blood_units: 0, components: {} };
                  const totalUnits = data.whole_blood_units + 
                    Object.values(data.components || {}).reduce((a, b) => a + b, 0);
                  
                  return (
                    <div 
                      key={group}
                      className={`p-4 rounded-lg border-2 text-center ${
                        totalUnits > 0 ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                      }`}
                    >
                      <p className="text-2xl font-bold text-slate-800">{group}</p>
                      <p className={`text-sm ${totalUnits > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {totalUnits} units
                      </p>
                      {data.whole_blood_units > 0 && (
                        <p className="text-xs text-slate-500 mt-1">
                          {data.whole_blood_units} whole blood
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
              <p className="text-sm text-slate-500 mt-4 text-center">
                <AlertCircle className="w-4 h-4 inline mr-1" />
                Availability is subject to change. Submit a request to reserve blood.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Profile Tab */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Organization Profile</CardTitle>
              <CardDescription>Your registered organization details</CardDescription>
            </CardHeader>
            <CardContent>
              {profile ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <Building2 className="w-5 h-5 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-sm text-slate-500">Organization</p>
                        <p className="font-medium">{profile.organization_name}</p>
                        <Badge variant="outline" className="mt-1">
                          {profile.requestor_type?.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Mail className="w-5 h-5 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-sm text-slate-500">Email</p>
                        <p className="font-medium">{profile.email}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Phone className="w-5 h-5 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-sm text-slate-500">Phone</p>
                        <p className="font-medium">{profile.phone}</p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <MapPin className="w-5 h-5 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-sm text-slate-500">Address</p>
                        <p className="font-medium">{profile.address}</p>
                        <p className="text-sm text-slate-600">
                          {profile.city}, {profile.state} - {profile.pincode}
                        </p>
                      </div>
                    </div>
                    {profile.license_number && (
                      <div>
                        <p className="text-sm text-slate-500">License Number</p>
                        <p className="font-medium">{profile.license_number}</p>
                      </div>
                    )}
                    {profile.registration_number && (
                      <div>
                        <p className="text-sm text-slate-500">Registration Number</p>
                        <p className="font-medium">{profile.registration_number}</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-slate-500">Profile not available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* New Request Dialog */}
      <Dialog open={showNewRequest} onOpenChange={setShowNewRequest}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>New Blood Request</DialogTitle>
            <DialogDescription>Submit a request for blood products</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Blood Group *</Label>
                <Select
                  value={requestForm.blood_group}
                  onValueChange={(v) => setRequestForm({ ...requestForm, blood_group: v })}
                >
                  <SelectTrigger data-testid="blood-group-select">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {BLOOD_GROUPS.map((bg) => (
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
                  max="10"
                  value={requestForm.units_required}
                  onChange={(e) => setRequestForm({ ...requestForm, units_required: e.target.value })}
                  data-testid="units-input"
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
                    {COMPONENT_TYPES.map((ct) => (
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
                    {URGENCY_LEVELS.map((u) => (
                      <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Patient Name *</Label>
              <Input
                value={requestForm.patient_name}
                onChange={(e) => setRequestForm({ ...requestForm, patient_name: e.target.value })}
                placeholder="Full name of patient"
                data-testid="patient-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Patient Age</Label>
                <Input
                  type="number"
                  min="0"
                  max="150"
                  value={requestForm.patient_age}
                  onChange={(e) => setRequestForm({ ...requestForm, patient_age: e.target.value })}
                />
              </div>
              <div>
                <Label>Patient Gender</Label>
                <Select
                  value={requestForm.patient_gender}
                  onValueChange={(v) => setRequestForm({ ...requestForm, patient_gender: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Diagnosis/Reason</Label>
              <Input
                value={requestForm.diagnosis}
                onChange={(e) => setRequestForm({ ...requestForm, diagnosis: e.target.value })}
                placeholder="e.g., Surgery, Accident, Anemia"
              />
            </div>
            <div>
              <Label>Doctor Name</Label>
              <Input
                value={requestForm.doctor_name}
                onChange={(e) => setRequestForm({ ...requestForm, doctor_name: e.target.value })}
                placeholder="Attending physician"
              />
            </div>
            <div>
              <Label>Required By Date *</Label>
              <Input
                type="date"
                value={requestForm.required_by_date}
                onChange={(e) => setRequestForm({ ...requestForm, required_by_date: e.target.value })}
                min={new Date().toISOString().split('T')[0]}
                data-testid="required-date-input"
              />
            </div>
            <div>
              <Label>Additional Notes</Label>
              <Textarea
                value={requestForm.notes}
                onChange={(e) => setRequestForm({ ...requestForm, notes: e.target.value })}
                placeholder="Any special requirements or notes"
              />
            </div>

            {/* Location Section */}
            <div className="border-t pt-4 mt-2">
              <Label className="flex items-center gap-2 mb-3">
                <MapPin className="w-4 h-4" />
                Delivery/Pickup Location
              </Label>
              
              {/* Location Type Toggle */}
              <div className="flex gap-2 mb-3">
                <Button
                  type="button"
                  variant={requestForm.location_type === 'delivery' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRequestForm({ ...requestForm, location_type: 'delivery' })}
                  className={requestForm.location_type === 'delivery' ? 'bg-red-600 hover:bg-red-700' : ''}
                >
                  <Truck className="w-4 h-4 mr-1" />
                  Delivery
                </Button>
                <Button
                  type="button"
                  variant={requestForm.location_type === 'pickup' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setRequestForm({ ...requestForm, location_type: 'pickup' })}
                  className={requestForm.location_type === 'pickup' ? 'bg-red-600 hover:bg-red-700' : ''}
                >
                  <Building2 className="w-4 h-4 mr-1" />
                  Self Pickup
                </Button>
              </div>

              {requestForm.location_type === 'delivery' && (
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={useProfileLocation}
                    >
                      <MapPin className="w-4 h-4 mr-1" />
                      Use Registered Location
                    </Button>
                  </div>
                  
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

                  <div>
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

              {requestForm.location_type === 'pickup' && (
                <p className="text-sm text-slate-500 bg-slate-50 p-3 rounded-lg">
                  You will pick up the blood from the blood bank. The blood bank will provide pickup instructions once your request is approved.
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewRequest(false)}>Cancel</Button>
            <Button 
              className="bg-red-600 hover:bg-red-700"
              onClick={handleCreateRequest}
              data-testid="submit-request-btn"
            >
              Submit Request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Blood Bank Map Dialog */}
      <Dialog open={showMapView} onOpenChange={setShowMapView}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Map className="w-5 h-5 text-red-600" />
              Find Nearby Blood Banks
            </DialogTitle>
            <DialogDescription>
              View blood banks on the map and check their availability
            </DialogDescription>
          </DialogHeader>
          <BloodBankMap
            height="450px"
            initialUserLocation={profile?.latitude && profile?.longitude 
              ? [profile.latitude, profile.longitude] 
              : null}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
