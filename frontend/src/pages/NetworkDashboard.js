import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Building2, Package, Users, AlertTriangle, ArrowLeftRight,
  RefreshCw, TrendingUp, Droplet, Clock, CheckCircle,
  Globe, BarChart3
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-blue-100 text-blue-700',
  dispatched: 'bg-indigo-100 text-indigo-700',
  delivered: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  cancelled: 'bg-slate-100 text-slate-700'
};

export default function NetworkDashboard() {
  const { user, isSystemAdmin, isSuperAdmin, isTenantAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [networkData, setNetworkData] = useState(null);
  const [selectedOrg, setSelectedOrg] = useState('all');
  const [viewMode, setViewMode] = useState('overview');

  useEffect(() => {
    fetchNetworkData();
  }, []);

  const fetchNetworkData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/dashboard/network');
      setNetworkData(res.data);
    } catch (error) {
      toast.error('Failed to fetch network data');
    } finally {
      setLoading(false);
    }
  };

  const getTotalInventory = () => {
    if (!networkData?.organizations) return 0;
    return networkData.organizations.reduce((sum, org) => sum + (org.inventory_count || 0), 0);
  };

  const getTotalDonors = () => {
    if (!networkData?.organizations) return 0;
    return networkData.organizations.reduce((sum, org) => sum + (org.donor_count || 0), 0);
  };

  const getTotalExpiring = () => {
    if (!networkData?.organizations) return 0;
    return networkData.organizations.reduce((sum, org) => sum + (org.expiring_count || 0), 0);
  };

  const filteredOrgs = selectedOrg === 'all' 
    ? networkData?.organizations || []
    : networkData?.organizations?.filter(o => o.id === selectedOrg) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  if (!networkData || networkData.error) {
    return (
      <div className="text-center py-12">
        <Globe className="w-16 h-16 mx-auto text-slate-300 mb-4" />
        <h2 className="text-xl font-semibold text-slate-700">Network View Not Available</h2>
        <p className="text-slate-500 mt-2">
          Network dashboard is only available for System Admin, Super Admin, and Tenant Admin users.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Globe className="w-8 h-8 text-teal-600" />
            Network Dashboard
          </h1>
          <p className="page-subtitle">
            {isSystemAdmin() ? 'System-wide overview' : 
             isSuperAdmin() ? 'Parent organization + branches' :
             'Your organization network'}
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedOrg} onValueChange={setSelectedOrg}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All Branches" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Branches</SelectItem>
              {networkData?.organizations?.map(org => (
                <SelectItem key={org.id} value={org.id}>
                  {org.org_name}
                  {org.is_own_org && ' (You)'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchNetworkData}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Network Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-teal-50 to-white border-teal-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-teal-600">Total Branches</p>
                <p className="text-3xl font-bold text-teal-700">
                  {networkData?.total_organizations || 0}
                </p>
              </div>
              <Building2 className="w-10 h-10 text-teal-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Total Donors</p>
                <p className="text-3xl font-bold text-blue-700">{getTotalDonors()}</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-white border-purple-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600">Network Inventory</p>
                <p className="text-3xl font-bold text-purple-700">{getTotalInventory()}</p>
              </div>
              <Package className="w-10 h-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-white border-amber-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600">Expiring Soon</p>
                <p className="text-3xl font-bold text-amber-700">{getTotalExpiring()}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-amber-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-indigo-50 to-white border-indigo-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-indigo-600">Pending Transfers</p>
                <p className="text-3xl font-bold text-indigo-700">
                  {networkData?.transfer_stats?.pending || 0}
                </p>
              </div>
              <ArrowLeftRight className="w-10 h-10 text-indigo-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList>
          <TabsTrigger value="overview">Branch Overview</TabsTrigger>
          <TabsTrigger value="inventory">Inventory Distribution</TabsTrigger>
          <TabsTrigger value="transfers">Transfer Activity</TabsTrigger>
        </TabsList>

        {/* Branch Overview Tab */}
        <TabsContent value="overview" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Branch Performance</CardTitle>
              <CardDescription>Overview of all branches in the network</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Branch</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-center">Donors</TableHead>
                    <TableHead className="text-center">Inventory</TableHead>
                    <TableHead className="text-center">Expiring</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOrgs.map(org => (
                    <TableRow 
                      key={org.id} 
                      className={org.is_own_org ? 'bg-teal-50' : ''}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-slate-400" />
                          <div>
                            <p className="font-medium">{org.org_name}</p>
                            {org.is_own_org && (
                              <Badge className="bg-teal-100 text-teal-700 text-xs">Your Branch</Badge>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {org.org_type?.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>{org.city || '-'}</TableCell>
                      <TableCell className="text-center font-medium">{org.donor_count}</TableCell>
                      <TableCell className="text-center">
                        <span className={`font-medium ${org.inventory_count < 10 ? 'text-red-600' : 'text-green-600'}`}>
                          {org.inventory_count}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={`font-medium ${org.expiring_count > 5 ? 'text-amber-600' : 'text-slate-600'}`}>
                          {org.expiring_count}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge className={org.inventory_count > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                          {org.inventory_count > 0 ? 'Active' : 'Low Stock'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Inventory Distribution Tab */}
        <TabsContent value="inventory" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Droplet className="w-5 h-5" />
                  Inventory by Blood Group
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(networkData?.network_inventory_by_group || {}).map(([group, count]) => (
                    <div key={group} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                          <span className="font-bold text-red-600">{group}</span>
                        </div>
                        <span className="font-medium">{group}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold">{count}</p>
                        <p className="text-xs text-slate-500">units</p>
                      </div>
                    </div>
                  ))}
                  {Object.keys(networkData?.network_inventory_by_group || {}).length === 0 && (
                    <p className="text-center text-slate-500 py-4">No inventory data</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Transfer Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(networkData?.transfer_stats || {}).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <Badge className={STATUS_COLORS[status] || 'bg-slate-100'}>{status}</Badge>
                      <span className="text-xl font-bold">{count}</span>
                    </div>
                  ))}
                  {Object.keys(networkData?.transfer_stats || {}).length === 0 && (
                    <p className="text-center text-slate-500 py-4">No transfer data</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Transfer Activity Tab */}
        <TabsContent value="transfers" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Inter-Branch Transfers</CardTitle>
              <CardDescription>Latest blood transfer activity across the network</CardDescription>
            </CardHeader>
            <CardContent>
              {networkData?.recent_transfers?.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <ArrowLeftRight className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  No recent transfers
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>From</TableHead>
                      <TableHead>To</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Component</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {networkData?.recent_transfers?.map(transfer => (
                      <TableRow key={transfer.id}>
                        <TableCell>
                          <div className="text-sm">
                            {new Date(transfer.created_at).toLocaleDateString()}
                          </div>
                          <div className="text-xs text-slate-500">
                            {new Date(transfer.created_at).toLocaleTimeString()}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-slate-400" />
                            {transfer.fulfilling_org_name}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-slate-400" />
                            {transfer.requesting_org_name}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{transfer.request_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{transfer.component_type?.replace('_', ' ')}</p>
                            <p className="text-xs text-slate-500">{transfer.blood_group}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">{transfer.quantity}</TableCell>
                        <TableCell>
                          <Badge className={STATUS_COLORS[transfer.status]}>
                            {transfer.status}
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
    </div>
  );
}
