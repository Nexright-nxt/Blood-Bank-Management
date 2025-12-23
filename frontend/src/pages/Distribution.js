import React, { useState, useEffect } from 'react';
import { requestAPI, issuanceAPI, inventoryAPI, componentAPI } from '../lib/api';
import { toast } from 'sonner';
import { Truck, Package, CheckCircle, Clock, Send } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';

export default function Distribution() {
  const [approvedRequests, setApprovedRequests] = useState([]);
  const [issuances, setIssuances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPickDialog, setShowPickDialog] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [availableItems, setAvailableItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [requestsRes, issuancesRes] = await Promise.all([
        requestAPI.getAll({ status: 'approved' }),
        issuanceAPI.getAll()
      ]);
      setApprovedRequests(requestsRes.data);
      setIssuances(issuancesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleStartPicking = async (request) => {
    setSelectedRequest(request);
    
    try {
      // Get FEFO items
      const response = await inventoryAPI.getFEFO({
        blood_group: request.blood_group,
        component_type: request.product_type !== 'whole_blood' ? request.product_type : undefined,
        quantity: request.quantity * 2 // Get more options
      });
      setAvailableItems(response.data);
      setSelectedItems([]);
      setShowPickDialog(true);
    } catch (error) {
      toast.error('Failed to get available items');
    }
  };

  const handleCreateIssuance = async () => {
    if (selectedItems.length === 0) {
      toast.error('Please select at least one item');
      return;
    }

    try {
      const response = await issuanceAPI.create(
        selectedRequest.id,
        selectedItems
      );
      toast.success(`Issuance created: ${response.data.issue_id}`);
      setShowPickDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create issuance');
    }
  };

  const handlePackIssuance = async (issueId) => {
    try {
      await issuanceAPI.pack(issueId);
      toast.success('Issuance packed');
      fetchData();
    } catch (error) {
      toast.error('Failed to pack issuance');
    }
  };

  const handleShipIssuance = async (issueId) => {
    try {
      await issuanceAPI.ship(issueId);
      toast.success('Issuance shipped');
      fetchData();
    } catch (error) {
      toast.error('Failed to ship issuance');
    }
  };

  const handleDeliverIssuance = async (issueId) => {
    const receivedBy = prompt('Enter receiver name:');
    if (!receivedBy) return;
    
    try {
      await issuanceAPI.deliver(issueId, receivedBy);
      toast.success('Issuance delivered');
      fetchData();
    } catch (error) {
      toast.error('Failed to mark as delivered');
    }
  };

  const toggleItemSelection = (itemId) => {
    setSelectedItems(prev => 
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const statusColors = {
    picking: 'bg-amber-100 text-amber-700',
    packing: 'bg-blue-100 text-blue-700',
    shipped: 'bg-purple-100 text-purple-700',
    delivered: 'bg-emerald-100 text-emerald-700',
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="distribution-page">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Distribution & Issuance</h1>
        <p className="page-subtitle">Pick, pack, and ship blood products</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Approved Requests</p>
            <p className="text-2xl font-bold">{approvedRequests.length}</p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Picking</p>
            <p className="text-2xl font-bold text-amber-600">
              {issuances.filter(i => i.status === 'picking').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">In Transit</p>
            <p className="text-2xl font-bold text-purple-600">
              {issuances.filter(i => i.status === 'shipped').length}
            </p>
          </CardContent>
        </Card>
        <Card className="card-stat">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Delivered</p>
            <p className="text-2xl font-bold text-emerald-600">
              {issuances.filter(i => i.status === 'delivered').length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="requests">
        <TabsList>
          <TabsTrigger value="requests">Approved Requests</TabsTrigger>
          <TabsTrigger value="issuances">Issuances</TabsTrigger>
        </TabsList>

        <TabsContent value="requests" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Approved Requests Ready for Fulfillment</CardTitle>
              <CardDescription>Click "Start Picking" to begin the issuance process</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : approvedRequests.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No approved requests pending fulfillment
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Request ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead>Requester</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {approvedRequests.map((req) => (
                      <TableRow key={req.id} className="data-table-row">
                        <TableCell className="font-mono">{req.request_id}</TableCell>
                        <TableCell className="capitalize">{req.request_type}</TableCell>
                        <TableCell>
                          <span className="blood-group-badge">{req.blood_group}</span>
                        </TableCell>
                        <TableCell className="capitalize">{req.product_type?.replace('_', ' ')}</TableCell>
                        <TableCell>{req.quantity}</TableCell>
                        <TableCell>{req.requester_name}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => handleStartPicking(req)}
                            className="bg-teal-600 hover:bg-teal-700"
                            data-testid={`pick-${req.id}`}
                          >
                            <Package className="w-4 h-4 mr-1" />
                            Start Picking
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

        <TabsContent value="issuances" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Issuances</CardTitle>
              <CardDescription>Track issuance status from picking to delivery</CardDescription>
            </CardHeader>
            <CardContent>
              {issuances.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No issuances created yet
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Issue ID</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Pick Time</TableHead>
                      <TableHead>Pack Time</TableHead>
                      <TableHead>Ship Time</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {issuances.map((issue) => (
                      <TableRow key={issue.id} className="data-table-row">
                        <TableCell className="font-mono">{issue.issue_id}</TableCell>
                        <TableCell>{issue.component_ids?.length || 0} items</TableCell>
                        <TableCell>
                          {issue.pick_timestamp ? new Date(issue.pick_timestamp).toLocaleTimeString() : '-'}
                        </TableCell>
                        <TableCell>
                          {issue.pack_timestamp ? new Date(issue.pack_timestamp).toLocaleTimeString() : '-'}
                        </TableCell>
                        <TableCell>
                          {issue.ship_timestamp ? new Date(issue.ship_timestamp).toLocaleTimeString() : '-'}
                        </TableCell>
                        <TableCell>
                          <Badge className={statusColors[issue.status]}>
                            {issue.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {issue.status === 'picking' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handlePackIssuance(issue.id)}
                            >
                              Pack
                            </Button>
                          )}
                          {issue.status === 'packing' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleShipIssuance(issue.id)}
                            >
                              <Send className="w-4 h-4 mr-1" />
                              Ship
                            </Button>
                          )}
                          {issue.status === 'shipped' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeliverIssuance(issue.id)}
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Delivered
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
        </TabsContent>
      </Tabs>

      {/* Pick Dialog */}
      <Dialog open={showPickDialog} onOpenChange={setShowPickDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package className="w-5 h-5 text-teal-600" />
              Select Items for Issuance
            </DialogTitle>
          </DialogHeader>
          
          {selectedRequest && (
            <div className="py-2 px-3 bg-slate-50 rounded-lg mb-4">
              <div className="flex justify-between">
                <div>
                  <p className="text-sm text-slate-500">Request: {selectedRequest.request_id}</p>
                  <p className="font-medium">{selectedRequest.quantity} x {selectedRequest.product_type?.replace('_', ' ')}</p>
                </div>
                <span className="blood-group-badge">{selectedRequest.blood_group}</span>
              </div>
            </div>
          )}

          <div className="py-4">
            <p className="text-sm text-slate-600 mb-2">
              Available items (FEFO order - First Expired First Out):
            </p>
            {availableItems.length === 0 ? (
              <p className="text-center text-slate-500 py-4">No matching items available</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {availableItems.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedItems.includes(item.id)
                        ? 'border-teal-500 bg-teal-50'
                        : 'border-slate-200 hover:border-teal-300'
                    }`}
                    onClick={() => toggleItemSelection(item.id)}
                  >
                    <div className="flex items-center gap-3">
                      <Checkbox
                        checked={selectedItems.includes(item.id)}
                        onCheckedChange={() => toggleItemSelection(item.id)}
                      />
                      <div>
                        <p className="font-mono text-sm">{item.unit_id || item.component_id}</p>
                        <p className="text-xs text-slate-500">
                          Volume: {item.volume}mL | Expiry: {item.expiry_date || 'N/A'}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-slate-100 text-slate-700">
                      {item.current_location || item.storage_location || 'Storage'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPickDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateIssuance}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={selectedItems.length === 0}
            >
              Create Issuance ({selectedItems.length} items)
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
