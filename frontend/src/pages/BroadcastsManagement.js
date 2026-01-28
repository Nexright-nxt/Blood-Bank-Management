import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  Megaphone, Plus, AlertTriangle, Package, RefreshCw,
  Phone, Building2, Clock, Users, X, Trash2, CheckCircle,
  MessageSquare, Eye
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
import { useAuth } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const COMPONENT_TYPES = [
  { value: 'whole_blood', label: 'Whole Blood' },
  { value: 'prc', label: 'Packed Red Cells' },
  { value: 'ffp', label: 'Fresh Frozen Plasma' },
  { value: 'platelets', label: 'Platelets' },
  { value: 'cryoprecipitate', label: 'Cryoprecipitate' }
];

export default function BroadcastsManagement() {
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [myBroadcasts, setMyBroadcasts] = useState([]);
  const [networkBroadcasts, setNetworkBroadcasts] = useState([]);
  const [stats, setStats] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showResponseDialog, setShowResponseDialog] = useState(false);
  const [selectedBroadcast, setSelectedBroadcast] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [isAdminView, setIsAdminView] = useState(false);

  // System admin cannot create broadcasts (no org_id)
  const canCreateBroadcast = user?.org_id || user?.user_type !== 'system_admin';

  const [newBroadcast, setNewBroadcast] = useState({
    broadcast_type: 'urgent_need',
    blood_group: 'O-',
    component_type: '',
    units_needed: '',
    units_available: '',
    expiry_date: '',
    title: '',
    description: '',
    priority: 'normal',
    visibility: 'network_wide',
    contact_phone: '',
    contact_name: '',
    expires_in_hours: 48
  });

  const [responseMessage, setResponseMessage] = useState('');
  const [responseUnits, setResponseUnits] = useState('');
  const [responsePhone, setResponsePhone] = useState('');

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [myRes, networkRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/broadcasts/my-broadcasts`, { headers }),
        axios.get(`${API_URL}/broadcasts/active`),
        axios.get(`${API_URL}/broadcasts/stats`)
      ]);
      setMyBroadcasts(myRes.data.broadcasts || []);
      setNetworkBroadcasts(networkRes.data.broadcasts || []);
      setStats(statsRes.data);
      setIsAdminView(myRes.data.is_admin_view || false);
    } catch (error) {
      toast.error('Failed to load broadcasts');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBroadcast = async () => {
    if (!newBroadcast.blood_group || !newBroadcast.title) {
      toast.error('Please fill in required fields');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        ...newBroadcast,
        units_needed: newBroadcast.units_needed ? parseInt(newBroadcast.units_needed) : undefined,
        units_available: newBroadcast.units_available ? parseInt(newBroadcast.units_available) : undefined,
        component_type: newBroadcast.component_type || undefined
      };
      await axios.post(`${API_URL}/broadcasts`, payload, { headers });
      toast.success('Broadcast created successfully');
      setShowCreateDialog(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create broadcast');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRespondToBroadcast = async () => {
    if (!responseMessage.trim()) {
      toast.error('Please enter a response message');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/broadcasts/${selectedBroadcast.id}/respond`, {
        message: responseMessage,
        units_offered: responseUnits ? parseInt(responseUnits) : undefined,
        contact_phone: responsePhone || undefined
      }, { headers });
      toast.success('Response sent successfully');
      setShowResponseDialog(false);
      setSelectedBroadcast(null);
      setResponseMessage('');
      setResponseUnits('');
      setResponsePhone('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send response');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseBroadcast = async (broadcastId, reason = 'fulfilled') => {
    try {
      await axios.put(`${API_URL}/broadcasts/${broadcastId}/close?reason=${reason}`, {}, { headers });
      toast.success(`Broadcast marked as ${reason}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to close broadcast');
    }
  };

  const handleDeleteBroadcast = async (broadcastId) => {
    if (!window.confirm('Are you sure you want to delete this broadcast?')) return;
    try {
      await axios.delete(`${API_URL}/broadcasts/${broadcastId}`, { headers });
      toast.success('Broadcast deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete broadcast');
    }
  };

  const resetForm = () => {
    setNewBroadcast({
      broadcast_type: 'urgent_need',
      blood_group: 'O-',
      component_type: '',
      units_needed: '',
      units_available: '',
      expiry_date: '',
      title: '',
      description: '',
      priority: 'normal',
      visibility: 'network_wide',
      contact_phone: '',
      contact_name: '',
      expires_in_hours: 48
    });
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-700">Active</Badge>;
      case 'responded':
        return <Badge className="bg-blue-100 text-blue-700">Responded</Badge>;
      case 'fulfilled':
        return <Badge className="bg-purple-100 text-purple-700">Fulfilled</Badge>;
      case 'expired':
        return <Badge className="bg-slate-100 text-slate-700">Expired</Badge>;
      case 'closed':
        return <Badge className="bg-slate-100 text-slate-700">Closed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'critical':
        return <Badge className="bg-red-600 text-white">Critical</Badge>;
      case 'high':
        return <Badge className="bg-orange-500 text-white">High</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-red-600" />
            Network Broadcasts
          </h1>
          <p className="text-slate-600 mt-1">Share urgent needs or surplus alerts with the blood bank network</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {canCreateBroadcast && (
            <Button className="bg-red-600 hover:bg-red-700" onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Broadcast
            </Button>
          )}
        </div>
      </div>

      {/* Admin Notice */}
      {isAdminView && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
          <strong>Admin View:</strong> You are viewing all broadcasts across the network. System admins cannot create broadcasts but can manage them.
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-8 h-8 text-red-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.urgent_needs_active}</p>
                  <p className="text-sm text-slate-500">Urgent Needs</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <Package className="w-8 h-8 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.surplus_alerts_active}</p>
                  <p className="text-sm text-slate-500">Surplus Alerts</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-8 h-8 text-purple-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.total_fulfilled}</p>
                  <p className="text-sm text-slate-500">Fulfilled</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-8 h-8 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">{stats.total_responses}</p>
                  <p className="text-sm text-slate-500">Total Responses</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="network" className="w-full">
        <TabsList>
          <TabsTrigger value="network">Network Alerts ({networkBroadcasts.length})</TabsTrigger>
          <TabsTrigger value="my">
            {isAdminView ? `All Broadcasts (${myBroadcasts.length})` : `My Broadcasts (${myBroadcasts.length})`}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="network" className="mt-4">
          {loading ? (
            <div className="text-center py-8 text-slate-500">Loading...</div>
          ) : networkBroadcasts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Megaphone className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-600">No active broadcasts in the network</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {networkBroadcasts.map((broadcast) => (
                <Card key={broadcast.id} className={`border-l-4 ${broadcast.priority === 'critical' ? 'border-red-500' : broadcast.priority === 'high' ? 'border-orange-400' : 'border-slate-200'}`}>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        {broadcast.broadcast_type === 'urgent_need' ? (
                          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                        ) : (
                          <Package className="w-5 h-5 text-green-600 mt-0.5" />
                        )}
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium">{broadcast.title}</span>
                            {getPriorityBadge(broadcast.priority)}
                            <Badge className={broadcast.broadcast_type === 'urgent_need' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}>
                              {broadcast.blood_group}
                            </Badge>
                            {getStatusBadge(broadcast.status)}
                          </div>
                          <p className="text-sm text-slate-600 mt-1">
                            {broadcast.org_name} • {formatTimeAgo(broadcast.created_at)}
                            {broadcast.units_needed && ` • ${broadcast.units_needed} units needed`}
                            {broadcast.units_available && ` • ${broadcast.units_available} units available`}
                          </p>
                          {broadcast.description && (
                            <p className="text-sm text-slate-500 mt-2">{broadcast.description}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {broadcast.response_count > 0 && (
                          <Badge variant="outline">{broadcast.response_count} responses</Badge>
                        )}
                        <Button 
                          size="sm" 
                          onClick={() => {
                            setSelectedBroadcast(broadcast);
                            setShowResponseDialog(true);
                          }}
                          data-testid={`respond-${broadcast.id}`}
                        >
                          Respond
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="my" className="mt-4">
          {loading ? (
            <div className="text-center py-8 text-slate-500">Loading...</div>
          ) : myBroadcasts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Megaphone className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-600 mb-4">You haven't created any broadcasts yet</p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Broadcast
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {myBroadcasts.map((broadcast) => (
                <Card key={broadcast.id} className={`border-l-4 ${broadcast.status === 'active' ? 'border-green-500' : 'border-slate-200'}`}>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        {broadcast.broadcast_type === 'urgent_need' ? (
                          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                        ) : (
                          <Package className="w-5 h-5 text-green-600 mt-0.5" />
                        )}
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium">{broadcast.title}</span>
                            {getPriorityBadge(broadcast.priority)}
                            <Badge className={broadcast.broadcast_type === 'urgent_need' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}>
                              {broadcast.blood_group}
                            </Badge>
                            {getStatusBadge(broadcast.status)}
                          </div>
                          <p className="text-sm text-slate-600 mt-1">
                            Created {formatTimeAgo(broadcast.created_at)}
                            {broadcast.response_count > 0 && ` • ${broadcast.response_count} responses`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {broadcast.status === 'active' && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleCloseBroadcast(broadcast.id, 'fulfilled')}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Mark Fulfilled
                          </Button>
                        )}
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDeleteBroadcast(broadcast.id)}
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Broadcast Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Broadcast</DialogTitle>
            <DialogDescription>
              Share an urgent need or surplus alert with the blood bank network
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Type Selection */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                className={`p-4 rounded-lg border-2 text-left transition-colors ${newBroadcast.broadcast_type === 'urgent_need' ? 'border-red-500 bg-red-50' : 'border-slate-200 hover:border-slate-300'}`}
                onClick={() => setNewBroadcast(prev => ({ ...prev, broadcast_type: 'urgent_need' }))}
              >
                <AlertTriangle className={`w-6 h-6 mb-2 ${newBroadcast.broadcast_type === 'urgent_need' ? 'text-red-600' : 'text-slate-400'}`} />
                <p className="font-medium">Urgent Need</p>
                <p className="text-xs text-slate-500">Request blood from network</p>
              </button>
              <button
                type="button"
                className={`p-4 rounded-lg border-2 text-left transition-colors ${newBroadcast.broadcast_type === 'surplus_alert' ? 'border-green-500 bg-green-50' : 'border-slate-200 hover:border-slate-300'}`}
                onClick={() => setNewBroadcast(prev => ({ ...prev, broadcast_type: 'surplus_alert' }))}
              >
                <Package className={`w-6 h-6 mb-2 ${newBroadcast.broadcast_type === 'surplus_alert' ? 'text-green-600' : 'text-slate-400'}`} />
                <p className="font-medium">Surplus Alert</p>
                <p className="text-xs text-slate-500">Share available stock</p>
              </button>
            </div>

            {/* Title */}
            <div>
              <Label>Title *</Label>
              <Input
                placeholder={newBroadcast.broadcast_type === 'urgent_need' ? 'e.g., Urgent O- needed for surgery' : 'e.g., Excess A+ available before expiry'}
                value={newBroadcast.title}
                onChange={(e) => setNewBroadcast(prev => ({ ...prev, title: e.target.value }))}
                data-testid="broadcast-title"
              />
            </div>

            {/* Blood Group & Component */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Blood Group *</Label>
                <Select
                  value={newBroadcast.blood_group}
                  onValueChange={(v) => setNewBroadcast(prev => ({ ...prev, blood_group: v }))}
                >
                  <SelectTrigger data-testid="broadcast-blood-group">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BLOOD_GROUPS.map((bg) => (
                      <SelectItem key={bg} value={bg}>{bg}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Component (Optional)</Label>
                <Select
                  value={newBroadcast.component_type || 'none'}
                  onValueChange={(v) => setNewBroadcast(prev => ({ ...prev, component_type: v === 'none' ? '' : v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Any Component</SelectItem>
                    {COMPONENT_TYPES.map((ct) => (
                      <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Units */}
            <div className="grid grid-cols-2 gap-3">
              {newBroadcast.broadcast_type === 'urgent_need' ? (
                <div>
                  <Label>Units Needed</Label>
                  <Input
                    type="number"
                    min="1"
                    placeholder="e.g., 5"
                    value={newBroadcast.units_needed}
                    onChange={(e) => setNewBroadcast(prev => ({ ...prev, units_needed: e.target.value }))}
                  />
                </div>
              ) : (
                <>
                  <div>
                    <Label>Units Available</Label>
                    <Input
                      type="number"
                      min="1"
                      placeholder="e.g., 10"
                      value={newBroadcast.units_available}
                      onChange={(e) => setNewBroadcast(prev => ({ ...prev, units_available: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label>Expiry Date</Label>
                    <Input
                      type="date"
                      value={newBroadcast.expiry_date}
                      onChange={(e) => setNewBroadcast(prev => ({ ...prev, expiry_date: e.target.value }))}
                    />
                  </div>
                </>
              )}
              <div>
                <Label>Priority</Label>
                <Select
                  value={newBroadcast.priority}
                  onValueChange={(v) => setNewBroadcast(prev => ({ ...prev, priority: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Description */}
            <div>
              <Label>Description (Optional)</Label>
              <Textarea
                placeholder="Add any additional details..."
                value={newBroadcast.description}
                onChange={(e) => setNewBroadcast(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            {/* Contact */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Contact Name</Label>
                <Input
                  placeholder="Your name"
                  value={newBroadcast.contact_name}
                  onChange={(e) => setNewBroadcast(prev => ({ ...prev, contact_name: e.target.value }))}
                />
              </div>
              <div>
                <Label>Contact Phone</Label>
                <Input
                  placeholder="Phone number"
                  value={newBroadcast.contact_phone}
                  onChange={(e) => setNewBroadcast(prev => ({ ...prev, contact_phone: e.target.value }))}
                />
              </div>
            </div>

            {/* Visibility */}
            <div>
              <Label>Visibility</Label>
              <Select
                value={newBroadcast.visibility}
                onValueChange={(v) => setNewBroadcast(prev => ({ ...prev, visibility: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="network_wide">Network-wide (All blood banks)</SelectItem>
                  <SelectItem value="nearby_only">Nearby Only (Within radius)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button 
              className="bg-red-600 hover:bg-red-700"
              onClick={handleCreateBroadcast}
              disabled={submitting}
            >
              {submitting ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Megaphone className="w-4 h-4 mr-2" />}
              Create Broadcast
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Response Dialog */}
      <Dialog open={showResponseDialog} onOpenChange={setShowResponseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Respond to Broadcast</DialogTitle>
            <DialogDescription>
              {selectedBroadcast?.title} - {selectedBroadcast?.org_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Your Message *</Label>
              <Textarea
                placeholder="e.g., We have 3 units available and can arrange transport..."
                value={responseMessage}
                onChange={(e) => setResponseMessage(e.target.value)}
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Units Offered (Optional)</Label>
                <Input
                  type="number"
                  min="1"
                  placeholder="e.g., 3"
                  value={responseUnits}
                  onChange={(e) => setResponseUnits(e.target.value)}
                />
              </div>
              <div>
                <Label>Contact Phone (Optional)</Label>
                <Input
                  placeholder="Your phone"
                  value={responsePhone}
                  onChange={(e) => setResponsePhone(e.target.value)}
                />
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setShowResponseDialog(false)}>Cancel</Button>
            <Button 
              className="bg-red-600 hover:bg-red-700"
              onClick={handleRespondToBroadcast}
              disabled={submitting}
            >
              {submitting ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <MessageSquare className="w-4 h-4 mr-2" />}
              Send Response
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
