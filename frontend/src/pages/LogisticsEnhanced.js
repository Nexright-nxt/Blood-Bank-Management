import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { logisticsEnhancedAPI, configAPI, issuanceAPI } from '../lib/api';
import { toast } from 'sonner';
import {
  Truck, Package, MapPin, Clock, CheckCircle, AlertTriangle, Plus,
  RefreshCw, Filter, Search, Eye, Edit, ChevronRight, Thermometer,
  Phone, Building2, Car, ExternalLink, Clipboard
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';

const STATUS_CONFIG = {
  preparing: { color: 'bg-slate-100 text-slate-700', icon: Package },
  in_transit: { color: 'bg-amber-100 text-amber-700', icon: Truck },
  delivered: { color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle },
  delayed: { color: 'bg-red-100 text-red-700', icon: AlertTriangle },
  failed: { color: 'bg-red-100 text-red-700', icon: AlertTriangle },
};

const TRACKING_STATUSES = [
  { value: 'preparing', label: 'Preparing' },
  { value: 'picked_up', label: 'Picked Up' },
  { value: 'in_transit', label: 'In Transit' },
  { value: 'out_for_delivery', label: 'Out for Delivery' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'delayed', label: 'Delayed' },
  { value: 'failed', label: 'Failed' },
];

export default function LogisticsEnhanced() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Data
  const [dashboard, setDashboard] = useState(null);
  const [shipments, setShipments] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [couriers, setCouriers] = useState([]);
  const [issuances, setIssuances] = useState([]);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [methodFilter, setMethodFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTrackingDialog, setShowTrackingDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  
  // Form data
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [newShipment, setNewShipment] = useState({
    issuance_id: '',
    destination: '',
    destination_address: '',
    contact_person: '',
    contact_phone: '',
    transport_method: 'self_vehicle',
    vehicle_id: '',
    driver_name: '',
    driver_phone: '',
    driver_license: '',
    courier_company: '',
    courier_contact: '',
    courier_tracking_number: '',
    special_instructions: '',
    estimated_arrival: '',
  });
  
  const [trackingUpdate, setTrackingUpdate] = useState({
    location: '',
    status: 'in_transit',
    notes: '',
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, shipmentsRes, vehiclesRes, couriersRes, issuancesRes] = await Promise.all([
        logisticsEnhancedAPI.getDashboard(),
        logisticsEnhancedAPI.getShipments(),
        configAPI.getVehicles({ is_active: true }),
        configAPI.getCouriers({ is_active: true }),
        issuanceAPI.getAll({ status: 'approved' }),
      ]);
      setDashboard(dashRes.data);
      setShipments(shipmentsRes.data);
      setVehicles(vehiclesRes.data);
      setCouriers(couriersRes.data);
      setIssuances(issuancesRes.data);
    } catch (error) {
      toast.error('Failed to load logistics data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDateTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Filter shipments
  const filteredShipments = shipments.filter(s => {
    if (statusFilter !== 'all' && s.status !== statusFilter) return false;
    if (methodFilter !== 'all' && s.transport_method !== methodFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return s.shipment_id?.toLowerCase().includes(q) ||
             s.tracking_number?.toLowerCase().includes(q) ||
             s.destination?.toLowerCase().includes(q);
    }
    return true;
  });

  const handleCreateShipment = async () => {
    if (!newShipment.issuance_id) {
      toast.error('Please select an issuance');
      return;
    }
    
    try {
      const response = await logisticsEnhancedAPI.createShipment(newShipment);
      toast.success(`Shipment created: ${response.data.tracking_number}`);
      setShowCreateDialog(false);
      setNewShipment({
        issuance_id: '',
        destination: '',
        destination_address: '',
        contact_person: '',
        contact_phone: '',
        transport_method: 'self_vehicle',
        vehicle_id: '',
        driver_name: '',
        driver_phone: '',
        driver_license: '',
        courier_company: '',
        courier_contact: '',
        courier_tracking_number: '',
        special_instructions: '',
        estimated_arrival: '',
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create shipment');
    }
  };

  const handleDispatch = async (shipmentId) => {
    try {
      await logisticsEnhancedAPI.dispatchShipment(shipmentId);
      toast.success('Shipment dispatched');
      fetchData();
    } catch (error) {
      toast.error('Failed to dispatch shipment');
    }
  };

  const handleAddTracking = async () => {
    if (!trackingUpdate.location || !trackingUpdate.status) {
      toast.error('Location and status are required');
      return;
    }
    
    try {
      await logisticsEnhancedAPI.addTrackingUpdate(selectedShipment.id, trackingUpdate);
      toast.success('Tracking update added');
      setShowTrackingDialog(false);
      setTrackingUpdate({ location: '', status: 'in_transit', notes: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to add tracking update');
    }
  };

  const handleMarkDelivered = async (shipment) => {
    const receivedBy = prompt('Enter name of person who received the shipment:');
    if (!receivedBy) return;
    
    try {
      await logisticsEnhancedAPI.deliverShipment(shipment.id, receivedBy, '');
      toast.success('Shipment marked as delivered');
      fetchData();
    } catch (error) {
      toast.error('Failed to mark as delivered');
    }
  };

  const copyTrackingLink = (trackingNumber) => {
    const url = `${window.location.origin}/track/${trackingNumber}`;
    navigator.clipboard.writeText(url);
    toast.success('Tracking link copied to clipboard');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Truck className="w-7 h-7 text-teal-600" />
            Logistics & Tracking
          </h1>
          <p className="page-subtitle">Manage shipments, track deliveries, and monitor fleet</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateDialog(true)} className="bg-teal-600 hover:bg-teal-700">
            <Plus className="w-4 h-4 mr-2" />
            Create Shipment
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Shipments</p>
                  <p className="text-2xl font-bold">{dashboard.total_shipments}</p>
                </div>
                <Package className="w-8 h-8 text-slate-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-amber-200 bg-amber-50">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-amber-700">In Transit</p>
                  <p className="text-2xl font-bold text-amber-700">{dashboard.in_transit}</p>
                </div>
                <Truck className="w-8 h-8 text-amber-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-emerald-200 bg-emerald-50">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-700">Delivered</p>
                  <p className="text-2xl font-bold text-emerald-700">{dashboard.delivered}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-emerald-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-700">Delayed</p>
                  <p className="text-2xl font-bold text-red-700">{dashboard.delayed}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-300" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Avg. Delivery</p>
                  <p className="text-2xl font-bold">{dashboard.avg_delivery_hours}h</p>
                </div>
                <Clock className="w-8 h-8 text-slate-300" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard">Active Shipments</TabsTrigger>
          <TabsTrigger value="all">All Shipments</TabsTrigger>
          <TabsTrigger value="fleet">Fleet Status</TabsTrigger>
        </TabsList>

        {/* Active Shipments Tab */}
        <TabsContent value="dashboard" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Active Shipments</CardTitle>
              <CardDescription>Shipments currently in transit or preparing</CardDescription>
            </CardHeader>
            <CardContent>
              {dashboard?.active_shipments?.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Truck className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>No active shipments</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {dashboard?.active_shipments?.map((shipment) => (
                    <div key={shipment.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${STATUS_CONFIG[shipment.status]?.color || 'bg-slate-100'}`}>
                          {React.createElement(STATUS_CONFIG[shipment.status]?.icon || Package, { className: 'w-6 h-6' })}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{shipment.shipment_id}</p>
                            <Badge variant="outline" className="font-mono text-xs">{shipment.tracking_number}</Badge>
                          </div>
                          <p className="text-sm text-slate-500">
                            <MapPin className="w-3 h-3 inline mr-1" />
                            {shipment.destination}
                          </p>
                          <p className="text-xs text-slate-400">
                            {shipment.transport_method === 'self_vehicle' ? (
                              <><Car className="w-3 h-3 inline mr-1" />Own Vehicle</>
                            ) : (
                              <><Building2 className="w-3 h-3 inline mr-1" />Third Party</>
                            )}
                            {' • '}{shipment.current_location}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => { setSelectedShipment(shipment); setShowDetailDialog(true); }}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => { setSelectedShipment(shipment); setShowTrackingDialog(true); }}>
                          <MapPin className="w-4 h-4 mr-1" />
                          Update
                        </Button>
                        {shipment.status === 'preparing' && (
                          <Button size="sm" onClick={() => handleDispatch(shipment.id)}>
                            Dispatch
                          </Button>
                        )}
                        {shipment.status === 'in_transit' && (
                          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handleMarkDelivered(shipment)}>
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Deliver
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* All Shipments Tab */}
        <TabsContent value="all" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>All Shipments</CardTitle>
                  <CardDescription>Complete shipment history</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <Input 
                      placeholder="Search..." 
                      className="pl-9 w-48"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="preparing">Preparing</SelectItem>
                      <SelectItem value="in_transit">In Transit</SelectItem>
                      <SelectItem value="delivered">Delivered</SelectItem>
                      <SelectItem value="delayed">Delayed</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={methodFilter} onValueChange={setMethodFilter}>
                    <SelectTrigger className="w-36">
                      <SelectValue placeholder="Method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Methods</SelectItem>
                      <SelectItem value="self_vehicle">Self Vehicle</SelectItem>
                      <SelectItem value="third_party">Third Party</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Shipment ID</TableHead>
                    <TableHead>Tracking</TableHead>
                    <TableHead>Destination</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredShipments.map((shipment) => (
                    <TableRow key={shipment.id}>
                      <TableCell className="font-medium">{shipment.shipment_id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <span className="font-mono text-xs">{shipment.tracking_number}</span>
                          <Button size="sm" variant="ghost" className="h-6 w-6 p-0" onClick={() => copyTrackingLink(shipment.tracking_number)}>
                            <Clipboard className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>{shipment.destination}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {shipment.transport_method?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={STATUS_CONFIG[shipment.status]?.color || 'bg-slate-100'}>
                          {shipment.status?.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDateTime(shipment.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => { setSelectedShipment(shipment); setShowDetailDialog(true); }}>
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => window.open(`/track/${shipment.tracking_number}`, '_blank')}>
                            <ExternalLink className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fleet Status Tab */}
        <TabsContent value="fleet" className="mt-6">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Vehicles</CardTitle>
                <CardDescription>{vehicles.length} active vehicles</CardDescription>
              </CardHeader>
              <CardContent>
                {vehicles.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Car className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                    <p>No vehicles configured</p>
                    <Button variant="link" onClick={() => navigate('/configuration')}>
                      Add vehicles in Configuration
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {vehicles.map((vehicle) => (
                      <div key={vehicle.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                            <Car className="w-5 h-5 text-slate-500" />
                          </div>
                          <div>
                            <p className="font-medium">{vehicle.vehicle_id}</p>
                            <p className="text-sm text-slate-500">{vehicle.vehicle_model} • {vehicle.registration_number}</p>
                          </div>
                        </div>
                        <Badge variant={vehicle.is_active ? 'default' : 'secondary'}>
                          {vehicle.is_active ? 'Available' : 'Inactive'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Courier Partners</CardTitle>
                <CardDescription>{couriers.length} active partners</CardDescription>
              </CardHeader>
              <CardContent>
                {couriers.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Building2 className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                    <p>No courier partners configured</p>
                    <Button variant="link" onClick={() => navigate('/configuration')}>
                      Add couriers in Configuration
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {couriers.map((courier) => (
                      <div key={courier.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <Building2 className="w-5 h-5 text-blue-500" />
                          </div>
                          <div>
                            <p className="font-medium">{courier.company_name}</p>
                            <p className="text-sm text-slate-500">{courier.contact_person} • {courier.contact_phone}</p>
                          </div>
                        </div>
                        <Badge variant={courier.is_active ? 'default' : 'secondary'}>
                          {courier.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Shipment Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Shipment</DialogTitle>
            <DialogDescription>Dispatch blood products to a destination</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Select Issuance */}
            <div>
              <Label>Select Issuance</Label>
              <Select value={newShipment.issuance_id} onValueChange={(v) => {
                const issuance = issuances.find(i => i.id === v);
                setNewShipment({
                  ...newShipment,
                  issuance_id: v,
                  destination: issuance?.hospital || '',
                  contact_person: issuance?.contact_person || '',
                  contact_phone: issuance?.contact_phone || '',
                });
              }}>
                <SelectTrigger>
                  <SelectValue placeholder="Select an approved issuance" />
                </SelectTrigger>
                <SelectContent>
                  {issuances.map((iss) => (
                    <SelectItem key={iss.id} value={iss.id}>
                      {iss.issue_id} - {iss.hospital || iss.request_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Destination */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Destination</Label>
                <Input 
                  value={newShipment.destination}
                  onChange={(e) => setNewShipment({...newShipment, destination: e.target.value})}
                  placeholder="Hospital/Facility name"
                />
              </div>
              <div>
                <Label>Address</Label>
                <Input 
                  value={newShipment.destination_address}
                  onChange={(e) => setNewShipment({...newShipment, destination_address: e.target.value})}
                  placeholder="Full address"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Contact Person</Label>
                <Input 
                  value={newShipment.contact_person}
                  onChange={(e) => setNewShipment({...newShipment, contact_person: e.target.value})}
                />
              </div>
              <div>
                <Label>Contact Phone</Label>
                <Input 
                  value={newShipment.contact_phone}
                  onChange={(e) => setNewShipment({...newShipment, contact_phone: e.target.value})}
                />
              </div>
            </div>

            {/* Transport Method */}
            <div>
              <Label>Transport Method</Label>
              <RadioGroup 
                value={newShipment.transport_method}
                onValueChange={(v) => setNewShipment({...newShipment, transport_method: v})}
                className="flex gap-4 mt-2"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="self_vehicle" id="self" />
                  <Label htmlFor="self" className="flex items-center gap-1 cursor-pointer">
                    <Car className="w-4 h-4" />
                    Self Vehicle
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="third_party" id="third" />
                  <Label htmlFor="third" className="flex items-center gap-1 cursor-pointer">
                    <Building2 className="w-4 h-4" />
                    Third Party
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Self Vehicle Fields */}
            {newShipment.transport_method === 'self_vehicle' && (
              <div className="space-y-4 p-4 border rounded-lg bg-slate-50">
                <div>
                  <Label>Select Vehicle</Label>
                  <Select 
                    value={newShipment.vehicle_id} 
                    onValueChange={(v) => {
                      const vehicle = vehicles.find(veh => veh.id === v || veh.vehicle_id === v);
                      setNewShipment({
                        ...newShipment,
                        vehicle_id: v,
                        driver_name: vehicle?.driver_name || '',
                        driver_phone: vehicle?.driver_phone || '',
                        driver_license: vehicle?.driver_license || '',
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a vehicle" />
                    </SelectTrigger>
                    <SelectContent>
                      {vehicles.map((v) => (
                        <SelectItem key={v.id} value={v.id}>
                          {v.vehicle_id} - {v.vehicle_model} ({v.registration_number})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Driver Name</Label>
                    <Input 
                      value={newShipment.driver_name}
                      onChange={(e) => setNewShipment({...newShipment, driver_name: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Driver Phone</Label>
                    <Input 
                      value={newShipment.driver_phone}
                      onChange={(e) => setNewShipment({...newShipment, driver_phone: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Driver License</Label>
                    <Input 
                      value={newShipment.driver_license}
                      onChange={(e) => setNewShipment({...newShipment, driver_license: e.target.value})}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Third Party Fields */}
            {newShipment.transport_method === 'third_party' && (
              <div className="space-y-4 p-4 border rounded-lg bg-blue-50">
                <div>
                  <Label>Courier Company</Label>
                  <Select 
                    value={newShipment.courier_company} 
                    onValueChange={(v) => {
                      const courier = couriers.find(c => c.company_name === v);
                      setNewShipment({
                        ...newShipment,
                        courier_company: v,
                        courier_contact: courier?.contact_phone || '',
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a courier partner" />
                    </SelectTrigger>
                    <SelectContent>
                      {couriers.map((c) => (
                        <SelectItem key={c.id} value={c.company_name}>
                          {c.company_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Courier Contact</Label>
                    <Input 
                      value={newShipment.courier_contact}
                      onChange={(e) => setNewShipment({...newShipment, courier_contact: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>External Tracking Number</Label>
                    <Input 
                      value={newShipment.courier_tracking_number}
                      onChange={(e) => setNewShipment({...newShipment, courier_tracking_number: e.target.value})}
                      placeholder="Optional"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Special Instructions */}
            <div>
              <Label>Special Instructions</Label>
              <Textarea 
                value={newShipment.special_instructions}
                onChange={(e) => setNewShipment({...newShipment, special_instructions: e.target.value})}
                placeholder="Temperature requirements, handling notes, etc."
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateShipment} className="bg-teal-600 hover:bg-teal-700">
              Create Shipment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Tracking Update Dialog */}
      <Dialog open={showTrackingDialog} onOpenChange={setShowTrackingDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Tracking Update</DialogTitle>
            <DialogDescription>
              Shipment: {selectedShipment?.shipment_id}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Current Location</Label>
              <Input 
                value={trackingUpdate.location}
                onChange={(e) => setTrackingUpdate({...trackingUpdate, location: e.target.value})}
                placeholder="Enter current location"
              />
            </div>
            <div>
              <Label>Status</Label>
              <Select value={trackingUpdate.status} onValueChange={(v) => setTrackingUpdate({...trackingUpdate, status: v})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TRACKING_STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea 
                value={trackingUpdate.notes}
                onChange={(e) => setTrackingUpdate({...trackingUpdate, notes: e.target.value})}
                placeholder="Additional notes (optional)"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTrackingDialog(false)}>Cancel</Button>
            <Button onClick={handleAddTracking}>Add Update</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Shipment Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Shipment Details</DialogTitle>
          </DialogHeader>
          
          {selectedShipment && (
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Shipment ID</p>
                  <p className="text-xl font-bold">{selectedShipment.shipment_id}</p>
                </div>
                <Badge className={`${STATUS_CONFIG[selectedShipment.status]?.color || 'bg-slate-100'} text-lg px-4 py-2`}>
                  {selectedShipment.status?.replace(/_/g, ' ')}
                </Badge>
              </div>

              {/* Tracking Number */}
              <div className="p-4 bg-teal-50 rounded-lg">
                <p className="text-sm text-teal-700">Tracking Number</p>
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-mono font-bold text-teal-600">{selectedShipment.tracking_number}</p>
                  <Button size="sm" variant="ghost" onClick={() => copyTrackingLink(selectedShipment.tracking_number)}>
                    <Clipboard className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Destination</p>
                  <p className="font-medium">{selectedShipment.destination}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Contact</p>
                  <p className="font-medium">{selectedShipment.contact_person} • {selectedShipment.contact_phone}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Transport Method</p>
                  <p className="font-medium capitalize">{selectedShipment.transport_method?.replace(/_/g, ' ')}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Current Location</p>
                  <p className="font-medium">{selectedShipment.current_location}</p>
                </div>
              </div>

              {/* Tracking Timeline */}
              <div>
                <p className="font-medium mb-3">Tracking History</p>
                <div className="relative pl-6 space-y-4">
                  <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-slate-200"></div>
                  {(selectedShipment.tracking_updates || []).slice().reverse().map((update, idx) => (
                    <div key={idx} className="relative">
                      <div className={`absolute -left-4 w-4 h-4 rounded-full ${idx === 0 ? 'bg-teal-500' : 'bg-slate-300'}`}></div>
                      <div className="pl-4">
                        <p className="font-medium capitalize">{update.status?.replace(/_/g, ' ')}</p>
                        <p className="text-sm text-slate-500">{update.location}</p>
                        <p className="text-xs text-slate-400">{formatDateTime(update.timestamp)}</p>
                        {update.notes && <p className="text-sm text-slate-600 mt-1">{update.notes}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>Close</Button>
            <Button variant="outline" onClick={() => window.open(`/track/${selectedShipment?.tracking_number}`, '_blank')}>
              <ExternalLink className="w-4 h-4 mr-2" />
              Public Tracking
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
