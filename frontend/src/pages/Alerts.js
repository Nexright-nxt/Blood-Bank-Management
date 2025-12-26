import React, { useState, useEffect } from 'react';
import { alertsAPI } from '../lib/api';
import { toast } from 'sonner';
import { 
  Bell, AlertTriangle, Clock, Package, Droplet, 
  ChevronRight, RefreshCw, AlertCircle, TrendingDown
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { useNavigate } from 'react-router-dom';

export default function Alerts() {
  const [loading, setLoading] = useState(true);
  const [alertsSummary, setAlertsSummary] = useState(null);
  const [expiringItems, setExpiringItems] = useState({ units: [], components: [] });
  const [lowStock, setLowStock] = useState({ low_stock_items: [], critical_items: [] });
  const [urgentRequests, setUrgentRequests] = useState({ urgent_requests: [] });
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllAlerts();
  }, []);

  const fetchAllAlerts = async () => {
    setLoading(true);
    try {
      const [summary, expiring, stock, urgent] = await Promise.all([
        alertsAPI.getSummary(),
        alertsAPI.getExpiringItems({ days: 7 }),
        alertsAPI.getLowStock({ threshold: 5 }),
        alertsAPI.getUrgentRequests()
      ]);
      setAlertsSummary(summary.data);
      setExpiringItems(expiring.data);
      setLowStock(stock.data);
      setUrgentRequests(urgent.data);
    } catch (error) {
      toast.error('Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  };

  const getCriticalCount = () => {
    return alertsSummary?.total_critical_alerts || 0;
  };

  const getWarningCount = () => {
    if (!alertsSummary) return 0;
    return (
      alertsSummary.expiry_alerts.expiring_within_7_days +
      alertsSummary.stock_alerts.low_stock_groups.length +
      alertsSummary.operational_alerts.pending_blood_requests
    );
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="alerts-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Bell className="w-8 h-8 text-teal-600" />
            Alerts Center
          </h1>
          <p className="page-subtitle">Monitor critical alerts and notifications</p>
        </div>
        <Button 
          onClick={fetchAllAlerts}
          variant="outline"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Alert Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className={`card-stat border-l-4 ${getCriticalCount() > 0 ? 'border-l-red-500 bg-red-50/50' : 'border-l-emerald-500'}`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Critical Alerts</p>
                <p className={`text-3xl font-bold ${getCriticalCount() > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {getCriticalCount()}
                </p>
              </div>
              <AlertCircle className={`w-10 h-10 ${getCriticalCount() > 0 ? 'text-red-500' : 'text-emerald-500'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className={`card-stat border-l-4 ${
          alertsSummary?.expiry_alerts?.expired_units > 0 ? 'border-l-red-500' : 
          alertsSummary?.expiry_alerts?.expiring_within_3_days > 0 ? 'border-l-amber-500' : 'border-l-slate-300'
        }`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Expiring Soon</p>
                <p className="text-3xl font-bold text-amber-600">
                  {alertsSummary?.expiry_alerts?.expiring_within_7_days || 0}
                </p>
                <p className="text-xs text-slate-400">Within 7 days</p>
              </div>
              <Clock className="w-10 h-10 text-amber-500" />
            </div>
          </CardContent>
        </Card>

        <Card className={`card-stat border-l-4 ${
          lowStock.critical_items?.length > 0 ? 'border-l-red-500' : 
          lowStock.low_stock_items?.length > 0 ? 'border-l-amber-500' : 'border-l-slate-300'
        }`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Low Stock Items</p>
                <p className="text-3xl font-bold text-orange-600">
                  {lowStock.summary?.total_low_stock || 0}
                </p>
                <p className="text-xs text-slate-400">{lowStock.summary?.total_critical || 0} critical</p>
              </div>
              <TrendingDown className="w-10 h-10 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className={`card-stat border-l-4 ${
          urgentRequests.emergency_count > 0 ? 'border-l-red-500' : 
          urgentRequests.urgent_count > 0 ? 'border-l-amber-500' : 'border-l-slate-300'
        }`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Urgent Requests</p>
                <p className="text-3xl font-bold text-purple-600">
                  {(urgentRequests.emergency_count || 0) + (urgentRequests.urgent_count || 0)}
                </p>
                <p className="text-xs text-slate-400">{urgentRequests.emergency_count || 0} emergency</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Operational Summary */}
      {alertsSummary && (
        <Card>
          <CardHeader>
            <CardTitle>Operational Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div 
                className="p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
                onClick={() => navigate('/donor-requests')}
              >
                <p className="text-sm text-slate-500">Pending Donor Requests</p>
                <p className="text-2xl font-bold">{alertsSummary.operational_alerts.pending_donor_requests}</p>
              </div>
              <div 
                className="p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
                onClick={() => navigate('/qc-validation')}
              >
                <p className="text-sm text-slate-500">Pending QC</p>
                <p className="text-2xl font-bold">{alertsSummary.operational_alerts.pending_qc_validations}</p>
              </div>
              <div 
                className="p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
                onClick={() => navigate('/qc-validation')}
              >
                <p className="text-sm text-slate-500">In Quarantine</p>
                <p className="text-2xl font-bold text-amber-600">{alertsSummary.operational_alerts.quarantine_items}</p>
              </div>
              <div 
                className="p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
                onClick={() => navigate('/requests')}
              >
                <p className="text-sm text-slate-500">Pending Blood Requests</p>
                <p className="text-2xl font-bold">{alertsSummary.operational_alerts.pending_blood_requests}</p>
              </div>
              <div 
                className="p-4 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 transition-colors"
                onClick={() => navigate('/requests')}
              >
                <p className="text-sm text-red-500">Urgent/Emergency</p>
                <p className="text-2xl font-bold text-red-600">{alertsSummary.operational_alerts.urgent_blood_requests}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="expiring">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="expiring" className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Expiring Items
            {expiringItems.units?.length + expiringItems.components?.length > 0 && (
              <Badge className="bg-amber-500 text-white ml-1">
                {expiringItems.units?.length + expiringItems.components?.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="stock" className="flex items-center gap-2">
            <Package className="w-4 h-4" />
            Low Stock
            {lowStock.low_stock_items?.length > 0 && (
              <Badge className="bg-orange-500 text-white ml-1">
                {lowStock.low_stock_items?.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="urgent" className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Urgent Requests
            {urgentRequests.urgent_requests?.length > 0 && (
              <Badge className="bg-red-500 text-white ml-1">
                {urgentRequests.urgent_requests?.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Expiring Items Tab */}
        <TabsContent value="expiring" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Items Expiring Within 7 Days</CardTitle>
              <CardDescription>Review and take action on expiring blood products</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : expiringItems.units?.length === 0 && expiringItems.components?.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Clock className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  No items expiring soon
                </div>
              ) : (
                <div className="space-y-4">
                  {expiringItems.units?.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium mb-2">Blood Units ({expiringItems.units.length})</h3>
                      <Table className="table-dense">
                        <TableHeader>
                          <TableRow>
                            <TableHead>Unit ID</TableHead>
                            <TableHead>Blood Group</TableHead>
                            <TableHead>Volume</TableHead>
                            <TableHead>Expiry Date</TableHead>
                            <TableHead>Days Left</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {expiringItems.units.slice(0, 10).map((unit) => {
                            const daysLeft = Math.ceil((new Date(unit.expiry_date) - new Date()) / (1000 * 60 * 60 * 24));
                            return (
                              <TableRow key={unit.id} className="data-table-row">
                                <TableCell className="font-mono">{unit.unit_id}</TableCell>
                                <TableCell>
                                  <span className="blood-group-badge">
                                    {unit.confirmed_blood_group || unit.blood_group}
                                  </span>
                                </TableCell>
                                <TableCell>{unit.volume} mL</TableCell>
                                <TableCell>{unit.expiry_date}</TableCell>
                                <TableCell>
                                  <Badge className={
                                    daysLeft <= 1 ? 'bg-red-100 text-red-700' :
                                    daysLeft <= 3 ? 'bg-amber-100 text-amber-700' :
                                    'bg-blue-100 text-blue-700'
                                  }>
                                    {daysLeft} days
                                  </Badge>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                  
                  {expiringItems.components?.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium mb-2">Components ({expiringItems.components.length})</h3>
                      <Table className="table-dense">
                        <TableHeader>
                          <TableRow>
                            <TableHead>Component ID</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Blood Group</TableHead>
                            <TableHead>Expiry Date</TableHead>
                            <TableHead>Days Left</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {expiringItems.components.slice(0, 10).map((comp) => {
                            const daysLeft = Math.ceil((new Date(comp.expiry_date) - new Date()) / (1000 * 60 * 60 * 24));
                            return (
                              <TableRow key={comp.id} className="data-table-row">
                                <TableCell className="font-mono">{comp.component_id}</TableCell>
                                <TableCell className="capitalize">{comp.component_type?.replace('_', ' ')}</TableCell>
                                <TableCell>
                                  {comp.blood_group && <span className="blood-group-badge">{comp.blood_group}</span>}
                                </TableCell>
                                <TableCell>{comp.expiry_date}</TableCell>
                                <TableCell>
                                  <Badge className={
                                    daysLeft <= 1 ? 'bg-red-100 text-red-700' :
                                    daysLeft <= 3 ? 'bg-amber-100 text-amber-700' :
                                    'bg-blue-100 text-blue-700'
                                  }>
                                    {daysLeft} days
                                  </Badge>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Low Stock Tab */}
        <TabsContent value="stock" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Low Stock Alerts</CardTitle>
              <CardDescription>Blood groups and components below threshold (5 units)</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : lowStock.low_stock_items?.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Package className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  All stock levels are adequate
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Critical Items */}
                  {lowStock.critical_items?.length > 0 && (
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                      <h3 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Critical - Zero Stock ({lowStock.critical_items.length})
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {lowStock.critical_items.map((item, idx) => (
                          <Badge key={idx} className="bg-red-100 text-red-700">
                            {item.blood_group} - {item.type.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Low Stock Table */}
                  <Table className="table-dense">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Blood Group</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Current Stock</TableHead>
                        <TableHead>Threshold</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lowStock.low_stock_items?.filter(item => item.count > 0).map((item, idx) => (
                        <TableRow key={idx} className="data-table-row">
                          <TableCell>
                            <span className="blood-group-badge">{item.blood_group}</span>
                          </TableCell>
                          <TableCell className="capitalize">{item.type.replace('_', ' ')}</TableCell>
                          <TableCell className="font-bold">{item.count}</TableCell>
                          <TableCell className="text-slate-500">{item.threshold}</TableCell>
                          <TableCell>
                            <Badge className={item.count <= 2 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}>
                              {item.count <= 2 ? 'Very Low' : 'Low'}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Urgent Requests Tab */}
        <TabsContent value="urgent" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Urgent & Emergency Blood Requests</CardTitle>
              <CardDescription>Pending requests requiring immediate attention</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
                </div>
              ) : urgentRequests.urgent_requests?.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  No urgent requests pending
                </div>
              ) : (
                <Table className="table-dense">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Request ID</TableHead>
                      <TableHead>Urgency</TableHead>
                      <TableHead>Blood Group</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead>Requester</TableHead>
                      <TableHead>Required By</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {urgentRequests.urgent_requests?.map((req) => (
                      <TableRow key={req.id} className="data-table-row">
                        <TableCell className="font-mono">{req.request_id}</TableCell>
                        <TableCell>
                          <Badge className={
                            req.urgency === 'emergency' ? 'bg-red-600 text-white' : 'bg-amber-500 text-white'
                          }>
                            {req.urgency}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="blood-group-badge">{req.blood_group}</span>
                        </TableCell>
                        <TableCell className="capitalize">{req.product_type?.replace('_', ' ')}</TableCell>
                        <TableCell>{req.quantity}</TableCell>
                        <TableCell>{req.requester_name}</TableCell>
                        <TableCell>{req.required_by_date || '-'}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            className="bg-teal-600 hover:bg-teal-700"
                            onClick={() => navigate('/distribution')}
                          >
                            <ChevronRight className="w-4 h-4" />
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
      </Tabs>
    </div>
  );
}
