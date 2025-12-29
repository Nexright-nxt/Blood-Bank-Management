import React, { useState, useEffect } from 'react';
import { logisticsAPI, issuanceAPI } from '../lib/api';
import { toast } from 'sonner';
import { Truck, Package, MapPin, Clock, CheckCircle, Send, Plus, Eye, Thermometer, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

export default function Logistics() {
  const [shipments, setShipments] = useState([]);
  const [issuances, setIssuances] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTrackingDialog, setShowTrackingDialog] = useState(false);
  const [showUpdateDialog, setShowUpdateDialog] = useState(false);
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  const [form, setForm] = useState({
    issuance_id: '',
    destination: '',
    destination_address: '',
    contact_person: '',
    contact_phone: '',
    transport_method: 'vehicle',
    special_instructions: '',
  });

  const [updateForm, setUpdateForm] = useState({
    location: '',
    temperature: '',
    notes: '',
  });

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [shipmentsRes, issuancesRes, dashboardRes] = await Promise.all([
        logisticsAPI.getShipments(statusFilter !== 'all' ? { status: statusFilter } : {}),
        issuanceAPI.getAll({ status: 'packing' }),
        logisticsAPI.getDashboard()
      ]);
      setShipments(shipmentsRes.data);
      setIssuances(issuancesRes.data);
      setDashboard(dashboardRes.data);
    } catch (error) {
      toast.error('Failed to fetch logistics data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateShipment = async () => {
    if (!form.issuance_id || !form.destination || !form.contact_person) {
      toast.error('Please fill required fields');
      return;
    }

    try {
      const response = await logisticsAPI.createShipment(form);
      toast.success(`Shipment created: ${response.data.shipment_id}`);
      setShowCreateDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create shipment');
    }
  };

  const handleDispatch = async (shipmentId) => {
    try {
      await logisticsAPI.dispatchShipment(shipmentId);
      toast.success('Shipment dispatched');
      fetchData();
    } catch (error) {
      toast.error('Failed to dispatch shipment');
    }
  };

  const handleUpdateLocation = async () => {
    if (!updateForm.location) {
      toast.error('Please enter location');
      return;
    }

    try {
      await logisticsAPI.updateLocation(selectedShipment.id, {
        location: updateForm.location,
        temperature: updateForm.temperature ? parseFloat(updateForm.temperature) : undefined,
        notes: updateForm.notes || undefined,
      });
      toast.success('Location updated');
      setShowUpdateDialog(false);
      setUpdateForm({ location: '', temperature: '', notes: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to update location');
    }
  };

  const handleDeliver = async (shipmentId) => {
    const receivedBy = prompt('Enter receiver name:');
    if (!receivedBy) return;

    try {
      await logisticsAPI.deliverShipment(shipmentId, receivedBy);
      toast.success('Shipment marked as delivered');
      fetchData();
    } catch (error) {
      toast.error('Failed to mark as delivered');
    }
  };

  const viewTracking = async (shipment) => {
    try {
      const response = await logisticsAPI.getShipment(shipment.id);
      setSelectedShipment(response.data);
      setShowTrackingDialog(true);
    } catch (error) {
      toast.error('Failed to load tracking info');
    }
  };

  const resetForm = () => {
    setForm({
      issuance_id: '',
      destination: '',
      destination_address: '',
      contact_person: '',
      contact_phone: '',
      transport_method: 'vehicle',
      special_instructions: '',
    });
  };

  const statusColors = {
    preparing: 'bg-slate-100 text-slate-700',
    in_transit: 'bg-blue-100 text-blue-700',
    delivered: 'bg-emerald-100 text-emerald-700',
  };

  const statusIcons = {
    preparing: Package,
    in_transit: Truck,
    delivered: CheckCircle,
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="logistics-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">Logistics & Delivery</h1>
          <p className="page-subtitle">Track shipments and manage deliveries</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            onClick={() => setShowCreateDialog(true)}
            className="bg-teal-600 hover:bg-teal-700"
            data-testid="create-shipment-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Shipment
          </Button>
        </div>
      </div>

      {/* Stats */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="card-stat">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Total Shipments</p>
              <p className="text-2xl font-bold">{dashboard.total_shipments}</p>
            </CardContent>
          </Card>
          <Card className="card-stat border-l-4 border-l-slate-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Preparing</p>
              <p className="text-2xl font-bold text-slate-600">{dashboard.preparing}</p>
            </CardContent>
          </Card>
          <Card className="card-stat border-l-4 border-l-blue-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">In Transit</p>
              <p className="text-2xl font-bold text-blue-600">{dashboard.in_transit}</p>
            </CardContent>
          </Card>
          <Card className="card-stat border-l-4 border-l-emerald-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Delivered</p>
              <p className="text-2xl font-bold text-emerald-600">{dashboard.delivered}</p>
            </CardContent>
          </Card>
          <Card className="card-stat border-l-4 border-l-amber-500">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Avg Delivery Time</p>
              <p className="text-2xl font-bold text-amber-600">{dashboard.avg_delivery_hours}h</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="preparing">Preparing</SelectItem>
                <SelectItem value="in_transit">In Transit</SelectItem>
                <SelectItem value="delivered">Delivered</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Shipments Table */}
      <Card>
        <CardHeader>
          <CardTitle>Shipments</CardTitle>
          <CardDescription>Track all blood product shipments</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
            </div>
          ) : shipments.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No shipments found
            </div>
          ) : (
            <Table className="table-dense">
              <TableHeader>
                <TableRow>
                  <TableHead>Shipment ID</TableHead>
                  <TableHead>Destination</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Transport</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shipments.map((shipment) => {
                  const StatusIcon = statusIcons[shipment.status] || Package;
                  return (
                    <TableRow key={shipment.id} className="data-table-row">
                      <TableCell className="font-mono">{shipment.shipment_id}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{shipment.destination}</p>
                          <p className="text-xs text-slate-500 truncate max-w-48">{shipment.destination_address}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm">{shipment.contact_person}</p>
                          <p className="text-xs text-slate-500">{shipment.contact_phone}</p>
                        </div>
                      </TableCell>
                      <TableCell className="capitalize">{shipment.transport_method}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[shipment.status]}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {shipment.status?.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(shipment.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewTracking(shipment)}
                            title="View Tracking"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {shipment.status === 'preparing' && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-blue-600"
                              onClick={() => handleDispatch(shipment.id)}
                            >
                              <Send className="w-4 h-4 mr-1" />
                              Dispatch
                            </Button>
                          )}
                          {shipment.status === 'in_transit' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedShipment(shipment);
                                  setShowUpdateDialog(true);
                                }}
                              >
                                <MapPin className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => handleDeliver(shipment.id)}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Deliver
                              </Button>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Shipment Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => { setShowCreateDialog(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Truck className="w-5 h-5 text-teal-600" />
              Create Shipment
            </DialogTitle>
            <DialogDescription>
              Create a new shipment for packed issuances
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Issuance *</Label>
              <Select 
                value={form.issuance_id}
                onValueChange={(v) => setForm({ ...form, issuance_id: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select issuance" />
                </SelectTrigger>
                <SelectContent>
                  {issuances.map(issue => (
                    <SelectItem key={issue.id} value={issue.id}>
                      {issue.issue_id} - {issue.component_ids?.length || 0} items
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Destination *</Label>
                <Input
                  value={form.destination}
                  onChange={(e) => setForm({ ...form, destination: e.target.value })}
                  placeholder="Hospital/Clinic name"
                />
              </div>
              <div className="space-y-2">
                <Label>Transport Method</Label>
                <Select 
                  value={form.transport_method}
                  onValueChange={(v) => setForm({ ...form, transport_method: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vehicle">Vehicle</SelectItem>
                    <SelectItem value="ambulance">Ambulance</SelectItem>
                    <SelectItem value="courier">Courier</SelectItem>
                    <SelectItem value="drone">Drone</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Destination Address</Label>
              <Textarea
                value={form.destination_address}
                onChange={(e) => setForm({ ...form, destination_address: e.target.value })}
                placeholder="Full address..."
                rows={2}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Contact Person *</Label>
                <Input
                  value={form.contact_person}
                  onChange={(e) => setForm({ ...form, contact_person: e.target.value })}
                  placeholder="Receiver name"
                />
              </div>
              <div className="space-y-2">
                <Label>Contact Phone</Label>
                <Input
                  value={form.contact_phone}
                  onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                  placeholder="Phone number"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Special Instructions</Label>
              <Textarea
                value={form.special_instructions}
                onChange={(e) => setForm({ ...form, special_instructions: e.target.value })}
                placeholder="Any special handling instructions..."
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowCreateDialog(false); resetForm(); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateShipment}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={!form.issuance_id || !form.destination || !form.contact_person}
            >
              <Plus className="w-4 h-4 mr-1" />
              Create Shipment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Update Location Dialog */}
      <Dialog open={showUpdateDialog} onOpenChange={setShowUpdateDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-600" />
              Update Location
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Current Location *</Label>
              <Input
                value={updateForm.location}
                onChange={(e) => setUpdateForm({ ...updateForm, location: e.target.value })}
                placeholder="Enter current location"
              />
            </div>

            <div className="space-y-2">
              <Label>Temperature (°C)</Label>
              <Input
                type="number"
                step="0.1"
                value={updateForm.temperature}
                onChange={(e) => setUpdateForm({ ...updateForm, temperature: e.target.value })}
                placeholder="e.g., 4.5"
              />
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={updateForm.notes}
                onChange={(e) => setUpdateForm({ ...updateForm, notes: e.target.value })}
                placeholder="Any notes..."
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUpdateDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpdateLocation}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={!updateForm.location}
            >
              <MapPin className="w-4 h-4 mr-1" />
              Update Location
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Tracking Dialog */}
      <Dialog open={showTrackingDialog} onOpenChange={setShowTrackingDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Truck className="w-5 h-5 text-teal-600" />
              Shipment Tracking
            </DialogTitle>
          </DialogHeader>
          
          {selectedShipment && (
            <div className="space-y-6 py-4">
              {/* Shipment Info */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Shipment ID</p>
                    <p className="font-mono font-medium">{selectedShipment.shipment_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Status</p>
                    <Badge className={statusColors[selectedShipment.status]}>
                      {selectedShipment.status?.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Destination</p>
                    <p className="font-medium">{selectedShipment.destination}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Contact</p>
                    <p>{selectedShipment.contact_person}</p>
                  </div>
                </div>
              </div>

              {/* Tracking History */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Tracking History
                </h4>
                <div className="space-y-3">
                  {selectedShipment.tracking_history?.map((entry, index) => (
                    <div key={index} className="flex gap-3">
                      <div className="w-2 h-2 mt-2 rounded-full bg-teal-500 flex-shrink-0"></div>
                      <div className="flex-1 pb-3 border-b border-slate-100 last:border-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium capitalize">{entry.status?.replace('_', ' ')}</p>
                          <p className="text-xs text-slate-500">
                            {new Date(entry.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <p className="text-sm text-slate-600">{entry.location}</p>
                        {entry.notes && (
                          <p className="text-xs text-slate-500 mt-1">{entry.notes}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Temperature Log */}
              {selectedShipment.temperature_log?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <Thermometer className="w-4 h-4" />
                    Temperature Log
                  </h4>
                  <div className="space-y-2">
                    {selectedShipment.temperature_log.map((entry, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                        <span className="font-mono">{entry.temperature}°C</span>
                        <span className="text-sm text-slate-500">{entry.location}</span>
                        <span className="text-xs text-slate-400">
                          {new Date(entry.timestamp).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTrackingDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
